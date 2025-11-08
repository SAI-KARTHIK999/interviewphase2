"""
API Endpoints for Processing Service
Implements all processing endpoints with consent enforcement
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from datetime import datetime, timedelta
import os
import tempfile
import uuid
from typing import Optional

# Import from processing_service
from processing_service import (
    SessionCreate, SessionResponse, AudioProcessResult, VideoProcessResult,
    TextProcessRequest, TextProcessResult, AnswerDocument,
    get_database, validate_session, enforce_consent, log_audit, settings, logger
)

# Import processors
from processors.audio_processor import get_audio_processor
from processors.video_processor import get_video_processor
from processors.text_processor import get_text_processor

# Field-level encryption for secure storage
from security.field_encryption import encrypt_document_fields

router = APIRouter(prefix="/api", tags=["processing"])

# ===== Session Management =====
@router.post("/session/start", response_model=SessionResponse, status_code=201)
async def start_session(session_data: SessionCreate, database = Depends(get_database)):
    """
    Start a new processing session with consent validation
    
    Requires:
        - user_id: User identifier
        - consent_id: Reference to consent record
        - allow_storage: Whether to persist sensitive data
        - allow_audio/allow_video: Permission flags
    """
    try:
        # Generate unique session ID
        session_id = f"session_{uuid.uuid4().hex[:16]}"
        
        # Create session record
        session_record = {
            "session_id": session_id,
            "user_id": session_data.user_id,
            "consent_id": session_data.consent_id,
            "allow_storage": session_data.allow_storage,
            "allow_audio": session_data.allow_audio,
            "allow_video": session_data.allow_video,
            "metadata": session_data.metadata or {},
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "status": "active"
        }
        
        await database.sessions.insert_one(session_record)
        
        # Log audit
        await log_audit(
            database, session_id, session_data.user_id,
            "session_start",
            {"consent_id": session_data.consent_id, "allow_storage": session_data.allow_storage},
            False
        )
        
        logger.info(f"✓ Session started: {session_id} for user {session_data.user_id}")
        
        return SessionResponse(
            session_id=session_id,
            user_id=session_data.user_id,
            consent_id=session_data.consent_id,
            allow_storage=session_data.allow_storage,
            created_at=session_record["created_at"],
            expires_at=session_record["expires_at"],
            status="active"
        )
        
    except Exception as e:
        logger.error(f"✗ Session start error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

# ===== Audio Processing =====
@router.post("/upload/audio", response_model=AudioProcessResult, status_code=202)
async def upload_audio(
    session_id: str = Form(...),
    audio_file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    database = Depends(get_database)
):
    """
    Upload and process audio file with Whisper STT
    
    Returns transcript with confidence score
    Enforces audio consent before processing
    """
    session = await validate_session(session_id, database)
    await enforce_consent(session, "audio")
    
    temp_path = None
    try:
        # Validate file
        if not audio_file.filename:
            raise HTTPException(status_code=400, detail="No audio file provided")
        
        # Check file size
        file_size = 0
        audio_content = await audio_file.read()
        file_size = len(audio_content)
        
        if file_size > settings.MAX_AUDIO_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"Audio file too large: {file_size/(1024*1024):.1f}MB (max {settings.MAX_AUDIO_SIZE_MB}MB)"
            )
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_path = temp_file.name
            temp_file.write(audio_content)
        
        logger.info(f"📁 Audio file saved: {os.path.getsize(temp_path)} bytes")
        
        # Process audio
        audio_processor = get_audio_processor(settings.WHISPER_MODEL, settings.AUDIO_CHUNK_DURATION)
        result = await audio_processor.process_audio(temp_path, language, timeout=300)
        
        # === Store transcript AND tokens if consent allows ===
        stored_data = False
        redacted_text_for_response = result["original_text"]
        if session["allow_storage"]:
            try:
                # Process text to redact PII and get tokens (uses advanced redactor if available)
                text_processor = get_text_processor()
                text_result = await text_processor.process_text(
                    result["original_text"],
                    compute_embedding=True,
                    lowercase_tokens=False
                )
                redacted_text_for_response = text_result["cleaned_text"]
                
                # Store complete document with raw + redacted + tokens
                answer_doc = {
                    "session_id": session_id,
                    "user_id": session["user_id"],
                    "consent_id": session["consent_id"],
                    # Raw STT
                    "transcribed_text": result["original_text"],
                    # Redacted/tokenized
                    "cleaned_text": text_result["cleaned_text"],
                    "tokens": text_result["tokens"],
                    "token_count": text_result["token_count"],
                    "pii_metadata": text_result.get("pii_metadata"),
                    # Metrics
                    "stt_confidence": result["stt_confidence"],
                    "embedding": text_result.get("embedding"),
                    "embedding_present": text_result["embedding_present"],
                    "created_at": datetime.utcnow()
                }
                # Encrypt sensitive fields before storage
                encrypted_doc = encrypt_document_fields(
                    answer_doc,
                    fields_to_encrypt=["transcribed_text", "cleaned_text"],
                    associated_data={
                        "collection": "answers",
                        "session_id": session_id,
                        "user_id": session["user_id"],
                        "consent_id": session["consent_id"]
                    }
                )
                await database.answers.insert_one(encrypted_doc)
                stored_data = True
                logger.info(f"✓ Transcript (encrypted) and tokens stored for session {session_id}")
            except Exception as e:
                logger.error(f"✗ Failed to store answer: {e}")
                # Continue even if storage fails - transcript still returned to user
        else:
            logger.info(f"✓ Audio processed but NOT stored (no consent) for session {session_id}")
        
        # Log audit
        await log_audit(
            database, session_id, session["user_id"],
            "audio_processed_and_stored" if stored_data else "audio_processed",
            {
                "filename": audio_file.filename,
                "duration": result["duration_seconds"],
                "confidence": result["stt_confidence"],
                "partial": result.get("partial", False),
                "stored": stored_data
            },
            stored_data
        )
        
        logger.info(f"✓ Audio processed for session {session_id}")
        
        return AudioProcessResult(
            session_id=session_id,
            # Return redacted text to clients to avoid PII leakage
            original_text=redacted_text_for_response,
            stt_confidence=result["stt_confidence"],
            stt_timestamp=result["stt_timestamp"],
            duration_seconds=result["duration_seconds"],
            partial=result.get("partial", False),
            chunk_count=result.get("chunk_count", 1)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Audio processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")
    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# ===== Video Processing =====
@router.post("/upload/video", response_model=VideoProcessResult, status_code=202)
async def upload_video(
    session_id: str = Form(...),
    video_file: UploadFile = File(...),
    database = Depends(get_database)
):
    """
    Upload and process video file with MediaPipe
    
    Extracts faces and computes attention/emotion metrics
    Enforces video consent before processing
    """
    session = await validate_session(session_id, database)
    await enforce_consent(session, "video")
    
    temp_path = None
    try:
        # Validate file
        if not video_file.filename:
            raise HTTPException(status_code=400, detail="No video file provided")
        
        # Check file size
        video_content = await video_file.read()
        file_size = len(video_content)
        
        if file_size > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"Video file too large: {file_size/(1024*1024):.1f}MB (max {settings.MAX_VIDEO_SIZE_MB}MB)"
            )
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            temp_path = temp_file.name
            temp_file.write(video_content)
        
        logger.info(f"📁 Video file saved: {os.path.getsize(temp_path)} bytes")
        
        # Process video
        video_processor = get_video_processor()
        result = await video_processor.process_video(temp_path, sample_rate=30)
        
        # Store video analysis if consent allows
        if session["allow_storage"]:
            video_doc = {
                "session_id": session_id,
                "user_id": session["user_id"],
                "consent_id": session["consent_id"],
                "frames_processed": result["frames_processed"],
                "faces_detected": result["faces_detected"],
                "attention_score": result.get("attention_score"),
                "emotion_summary": result.get("emotion_summary"),
                "created_at": datetime.utcnow()
            }
            await database.video_analysis.insert_one(video_doc)
            logger.info(f"✓ Video analysis stored for session {session_id}")
        
        # Log audit
        await log_audit(
            database, session_id, session["user_id"],
            "video_processed",
            {
                "filename": video_file.filename,
                "frames_processed": result["frames_processed"],
                "faces_detected": result["faces_detected"]
            },
            session["allow_storage"]
        )
        
        return VideoProcessResult(**result, session_id=session_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ Video processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")
    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# ===== Text Processing =====
@router.post("/process/text", response_model=TextProcessResult)
async def process_text(
    request: TextProcessRequest,
    database = Depends(get_database)
):
    """
    Process text: clean, tokenize, detect PII, optionally compute embeddings
    
    Stores to MongoDB only if session allows storage
    """
    session = await validate_session(request.session_id, database)
    
    try:
        # Process text
        text_processor = get_text_processor()
        result = await text_processor.process_text(
            request.original_text,
            compute_embedding=request.compute_embedding,
            lowercase_tokens=False
        )
        
        # Store to MongoDB if consent allows
        if session["allow_storage"]:
            answer_doc = {
                "session_id": request.session_id,
                "user_id": session["user_id"],
                "consent_id": session["consent_id"],
                "original_text": request.original_text,
                "cleaned_text": result["cleaned_text"],
                "tokens": result["tokens"],
                "token_count": result["token_count"],
                "pii_metadata": result.get("pii_metadata"),
                "stt_confidence": None,  # Can be updated if from audio
                "embedding": result.get("embedding"),
                "embedding_present": result["embedding_present"],
                "created_at": datetime.utcnow()
            }
            # Encrypt sensitive text fields before storage
            encrypted_doc = encrypt_document_fields(
                answer_doc,
                fields_to_encrypt=["original_text", "cleaned_text"],
                associated_data={
                    "collection": "answers",
                    "session_id": request.session_id,
                    "user_id": session["user_id"],
                    "consent_id": session["consent_id"]
                }
            )
            await database.answers.insert_one(encrypted_doc)
            logger.info(f"✓ Text (encrypted) and tokens stored for session {request.session_id}")
            stored_data = True
        else:
            logger.info(f"✓ Answer processed but NOT stored (no consent) for session {request.session_id}")
            stored_data = False
        
        # Log audit (always log, even if not storing)
        await log_audit(
            database, request.session_id, session["user_id"],
            "text_processed",
            {
                "token_count": result["token_count"],
                "pii_redacted": result["pii_redacted"],
                "pii_flags": result["pii_flags"],
                "embedding_computed": result["embedding_present"]
            },
            stored_data
        )
        
        return TextProcessResult(
            session_id=request.session_id,
            cleaned_text=result["cleaned_text"],
            tokens=result["tokens"],
            token_count=result["token_count"],
            pii_redacted=result["pii_redacted"],
            pii_flags=result["pii_flags"],
            embedding_present=result["embedding_present"],
            embedding_dimensions=result.get("embedding_dimensions")
        )
        
    except Exception as e:
        logger.error(f"✗ Text processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Text processing failed: {str(e)}")
