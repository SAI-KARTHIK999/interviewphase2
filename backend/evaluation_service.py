"""
Evaluation Service
FastAPI service for analyzing and scoring interview answers with NLP models.
"""

import sys
import os
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging
import time
import asyncio
from collections import defaultdict

# Import our modules
from scoring_engine import ScoringEngine
from models.answer_scorer import AnswerScorer
from models.tone_analyzer import ToneAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Interview Answer Evaluation Service",
    description="NLP-powered answer scoring with consent enforcement",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = "interview_db"
CONFIG_PATH = Path(__file__).parent / "scoring_config.json"

# Global instances
scoring_engine = None
answer_scorer = None
tone_analyzer = None
db_client = None
db = None

# Rate limiting storage (session_id -> list of timestamps)
rate_limit_tracker = defaultdict(list)


# Pydantic Models
class AnalysisRequest(BaseModel):
    """Request model for answer analysis."""
    answer_id: str = Field(..., description="MongoDB ObjectId of the answer")
    question_text: Optional[str] = Field(None, description="Question text for relevance")
    ground_truth: Optional[str] = Field(None, description="Expected answer for correctness")
    audio_path: Optional[str] = Field(None, description="Path to audio file for tone analysis")


class AnalysisResponse(BaseModel):
    """Response model for answer analysis."""
    answer_id: str
    clarity: float
    correctness: float
    relevance: float
    tone_score: float
    stt_confidence: float
    quality_score: float
    components: Dict[str, str]
    model_version: str
    created_at: datetime


class ConfigResponse(BaseModel):
    """Response model for configuration."""
    weights: Dict[str, float]
    models: Optional[Dict[str, Any]] = None
    thresholds: Optional[Dict[str, Any]] = None


class ConfigUpdateRequest(BaseModel):
    """Request model for configuration update."""
    weights: Optional[Dict[str, float]] = None
    models: Optional[Dict[str, Any]] = None
    thresholds: Optional[Dict[str, Any]] = None


# Startup and Shutdown
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global scoring_engine, answer_scorer, tone_analyzer, db_client, db
    
    logger.info("Starting Evaluation Service...")
    
    # Initialize scoring components
    try:
        scoring_engine = ScoringEngine(str(CONFIG_PATH))
        logger.info("✓ Scoring engine initialized")
    except Exception as e:
        logger.error(f"Failed to initialize scoring engine: {e}")
        raise
    
    try:
        answer_scorer = AnswerScorer(
            embedding_model="sentence-transformers/all-mpnet-base-v2",
            model_version="v1.0"
        )
        logger.info("✓ Answer scorer initialized")
    except Exception as e:
        logger.warning(f"Answer scorer initialization failed: {e}")
        answer_scorer = None
    
    try:
        tone_analyzer = ToneAnalyzer()
        logger.info("✓ Tone analyzer initialized")
    except Exception as e:
        logger.warning(f"Tone analyzer initialization failed: {e}")
        tone_analyzer = None
    
    # Connect to MongoDB
    try:
        db_client = AsyncIOMotorClient(MONGODB_URL)
        db = db_client[DB_NAME]
        # Test connection
        await db_client.admin.command('ping')
        logger.info(f"✓ Connected to MongoDB: {DB_NAME}")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise
    
    logger.info("Evaluation Service ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global db_client
    if db_client:
        db_client.close()
        logger.info("MongoDB connection closed")


# Dependencies
async def get_database():
    """Dependency to get database connection."""
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )
    return db


async def check_rate_limit(session_id: str) -> bool:
    """
    Check if session has exceeded rate limit.
    
    Args:
        session_id: Session identifier
        
    Returns:
        True if within limit, raises HTTPException otherwise
    """
    config = scoring_engine.get_config()
    limit = config.get("rate_limits", {}).get("analyses_per_session_per_minute", 10)
    
    now = time.time()
    cutoff = now - 60  # Last minute
    
    # Remove old timestamps
    rate_limit_tracker[session_id] = [
        ts for ts in rate_limit_tracker[session_id] if ts > cutoff
    ]
    
    # Check limit
    if len(rate_limit_tracker[session_id]) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: max {limit} analyses per minute per session"
        )
    
    # Add current timestamp
    rate_limit_tracker[session_id].append(now)
    return True


# API Endpoints
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "Interview Answer Evaluation Service",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "components": {
            "scoring_engine": scoring_engine is not None,
            "answer_scorer": answer_scorer is not None,
            "tone_analyzer": tone_analyzer is not None,
            "database": db is not None
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/answers/{answer_id}/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_answer(
    answer_id: str,
    request: AnalysisRequest = None,
    db: AsyncIOMotorClient = Depends(get_database)
):
    """
    Analyze an interview answer and compute quality scores.
    
    This endpoint:
    1. Validates consent and session
    2. Fetches answer text from database
    3. Computes component scores (clarity, correctness, relevance)
    4. Analyzes tone from text (and optionally audio)
    5. Combines scores into quality_score
    6. Stores results if allow_storage=true
    7. Always logs audit trail
    """
    start_time = time.time()
    
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(answer_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid answer_id format"
            )
        
        # Fetch answer from database
        answer = await db.answers.find_one({"_id": ObjectId(answer_id)})
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found"
            )
        
        # Get session and consent info
        session_id = answer.get("session_id")
        user_id = answer.get("user_id")
        consent_id = answer.get("consent_id")
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Answer has no associated session"
            )
        
        # Check rate limit
        await check_rate_limit(session_id)
        
        # Fetch session to check consent
        session = await db.sessions.find_one({"session_id": session_id})
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check session expiry
        if session.get("expires_at") and session["expires_at"] < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session expired"
            )
        
        # Check consent for processing
        allow_storage = session.get("allow_storage", False)
        
        # If allow_storage is false, we can still analyze but won't store sensitive data
        if not allow_storage:
            logger.info(f"Analyzing answer {answer_id} without storage (consent)")
        
        # Get answer text
        answer_text = answer.get("original_text") or answer.get("cleaned_text")
        if not answer_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Answer has no text to analyze"
            )
        
        # Get STT confidence (default to 1.0 if not available)
        stt_confidence = answer.get("stt_confidence", 1.0)
        
        # Extract question and ground truth from request
        question_text = request.question_text if request else None
        ground_truth = request.ground_truth if request else None
        audio_path = request.audio_path if request else None
        
        # Perform NLP analysis
        if not answer_scorer:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Answer scorer not available"
            )
        
        nlp_analysis = answer_scorer.analyze_answer(
            answer_text,
            question_text=question_text,
            ground_truth=ground_truth
        )
        
        clarity = nlp_analysis["clarity"]
        correctness = nlp_analysis["correctness"]
        relevance = nlp_analysis["relevance"]
        components = nlp_analysis["components"]
        model_version = nlp_analysis["model_version"]
        tokens = nlp_analysis.get("tokens", [])
        token_count = nlp_analysis.get("token_count", 0)
        embedding = nlp_analysis.get("embedding")
        
        # Perform tone analysis
        tone_score = 50.0  # Default neutral
        tone_label = "neutral"
        
        if tone_analyzer:
            tone_analysis = tone_analyzer.analyze_tone(answer_text, audio_path)
            tone_score = tone_analysis["tone_score"]
            tone_label = tone_analysis["tone_label"]
            components["tone_label"] = tone_label
        
        # Compute quality score
        quality_result = scoring_engine.analyze_with_quality_score(
            clarity=clarity,
            correctness=correctness,
            relevance=relevance,
            tone_score=tone_score,
            stt_confidence=stt_confidence,
            components=components
        )
        
        quality_score = quality_result["quality_score"]
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Create analysis result
        analysis_data = {
            "answer_id": str(answer_id),
            "session_id": session_id,
            "user_id": user_id,
            "consent_id": consent_id,
            "quality_score": quality_score,
            "clarity": clarity,
            "correctness": correctness,
            "relevance": relevance,
            "tone_score": tone_score,
            "stt_confidence": stt_confidence,
            "components": components,
            "model_version": model_version,
            "processing_time_ms": processing_time_ms,
            "created_at": datetime.utcnow()
        }
        
        # Store analysis results if consent allows
        if allow_storage:
            # Prepare update data - store both original text and tokenized format
            update_data = {
                "quality_score": quality_score,
                "clarity": clarity,
                "correctness": correctness,
                "relevance": relevance,
                "tone_score": tone_score,
                "tokens": tokens,  # Tokenized format
                "token_count": token_count,
                "analysis_meta": {
                    "model_version": model_version,
                    "processing_time_ms": processing_time_ms,
                    "analyzed_at": datetime.utcnow()
                }
            }
            
            # Store embedding if available
            if embedding:
                update_data["embedding"] = embedding
                update_data["embedding_present"] = True
            
            # Update answer document with scores and tokens
            # Note: original_text is already in the document from STT processing
            await db.answers.update_one(
                {"_id": ObjectId(answer_id)},
                {"$set": update_data}
            )
            logger.info(
                f"Stored analysis for answer {answer_id}: "
                f"original_text preserved, tokens={token_count}, scores added"
            )
        
        # Always log audit (even if not storing sensitive data)
        await db.processing_audit.insert_one({
            "session_id": session_id,
            "user_id": user_id,
            "consent_id": consent_id,
            "action": "answer_analyzed",
            "answer_id": str(answer_id),
            "details": {
                "quality_score": quality_score,
                "processing_time_ms": processing_time_ms,
                "model_version": model_version
            },
            "stored_sensitive_data": allow_storage,
            "timestamp": datetime.utcnow()
        })
        
        logger.info(
            f"Analyzed answer {answer_id}: quality_score={quality_score:.1f}, "
            f"processing_time={processing_time_ms:.1f}ms"
        )
        
        # Return analysis result
        return AnalysisResponse(
            answer_id=str(answer_id),
            clarity=clarity,
            correctness=correctness,
            relevance=relevance,
            tone_score=tone_score,
            stt_confidence=stt_confidence,
            quality_score=quality_score,
            components=components,
            model_version=model_version,
            created_at=analysis_data["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed for answer {answer_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@app.get("/api/score/config", response_model=ConfigResponse, tags=["Configuration"])
async def get_scoring_config():
    """
    Get current scoring configuration including weights.
    """
    config = scoring_engine.get_config()
    return ConfigResponse(
        weights=config.get("weights", {}),
        models=config.get("models"),
        thresholds=config.get("thresholds")
    )


@app.put("/api/score/config", response_model=ConfigResponse, tags=["Configuration"])
async def update_scoring_config(update: ConfigUpdateRequest):
    """
    Update scoring configuration (admin endpoint).
    
    In production, this should be protected with authentication.
    """
    try:
        # Create new config dict
        new_config = {}
        
        if update.weights:
            new_config["weights"] = update.weights
        if update.models:
            new_config["models"] = update.models
        if update.thresholds:
            new_config["thresholds"] = update.thresholds
        
        # Update configuration
        scoring_engine.update_config(new_config)
        scoring_engine.save_config()
        
        logger.info("Configuration updated successfully")
        
        # Return updated config
        config = scoring_engine.get_config()
        return ConfigResponse(
            weights=config.get("weights", {}),
            models=config.get("models"),
            thresholds=config.get("thresholds")
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Config update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration update failed: {str(e)}"
        )


# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Evaluation Service on port 8001...")
    uvicorn.run(
        "evaluation_service:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
