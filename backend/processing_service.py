"""
AI Interview Processing Service
FastAPI-based microservice for audio/video/text processing with consent enforcement
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== Configuration =====
class Settings:
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = "interview_db"
    MAX_AUDIO_SIZE_MB: int = 50
    MAX_VIDEO_SIZE_MB: int = 100
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RATE_LIMIT_PER_MINUTE: int = 10
    AUDIO_CHUNK_DURATION: int = 30  # seconds
    RETENTION_DAYS: int = 30

settings = Settings()

# ===== Pydantic Models =====
class SessionCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    consent_id: str = Field(..., min_length=1)
    allow_storage: bool = False
    allow_audio: bool = True
    allow_video: bool = True
    metadata: Optional[Dict[str, Any]] = None

class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    consent_id: str
    allow_storage: bool
    created_at: datetime
    expires_at: datetime
    status: str = "active"

class AudioProcessResult(BaseModel):
    session_id: str
    original_text: str
    stt_confidence: float
    stt_timestamp: datetime
    duration_seconds: float
    partial: bool = False
    chunk_count: int = 1

class VideoProcessResult(BaseModel):
    session_id: str
    frames_processed: int
    faces_detected: int
    attention_score: Optional[float] = None
    emotion_summary: Optional[Dict[str, float]] = None
    processing_time_seconds: float

class TextProcessRequest(BaseModel):
    session_id: str
    original_text: str
    compute_embedding: bool = False

class TextProcessResult(BaseModel):
    session_id: str
    cleaned_text: str
    tokens: List[str]
    token_count: int
    pii_redacted: bool
    pii_flags: List[str] = []
    embedding_present: bool = False
    embedding_dimensions: Optional[int] = None

class AnswerDocument(BaseModel):
    session_id: str
    user_id: str
    consent_id: str
    original_text: Optional[str] = None
    cleaned_text: Optional[str] = None
    tokens: Optional[List[str]] = None
    token_count: int = 0
    stt_confidence: Optional[float] = None
    embedding_present: bool = False
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ===== FastAPI App =====
app = FastAPI(
    title="AI Interview Processing Service",
    description="Privacy-first audio/video/text processing with consent enforcement",
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

# ===== Database Connection =====
motor_client = None
db = None

@app.on_event("startup")
async def startup_db_client():
    global motor_client, db
    try:
        motor_client = AsyncIOMotorClient(settings.MONGODB_URL)
        db = motor_client[settings.DATABASE_NAME]
        
        # Create indexes
        await create_indexes()
        
        logger.info(f"✓ Connected to MongoDB at {settings.MONGODB_URL}")
        logger.info(f"✓ Using database: {settings.DATABASE_NAME}")
    except Exception as e:
        logger.error(f"✗ Failed to connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    if motor_client:
        motor_client.close()
        logger.info("✓ Closed MongoDB connection")

async def create_indexes():
    """Create MongoDB indexes for optimal performance"""
    try:
        # Sessions collection
        await db.sessions.create_index([("session_id", 1)], unique=True)
        await db.sessions.create_index([("user_id", 1), ("created_at", -1)])
        
        # Answers collection
        await db.answers.create_index([("session_id", 1)])
        await db.answers.create_index([("user_id", 1), ("created_at", -1)])
        await db.answers.create_index([("token_count", 1)])
        await db.answers.create_index([("created_at", 1)], expireAfterSeconds=settings.RETENTION_DAYS * 86400)
        
        # Video analysis collection
        await db.video_analysis.create_index([("session_id", 1)])
        await db.video_analysis.create_index([("created_at", 1)], expireAfterSeconds=settings.RETENTION_DAYS * 86400)
        
        # Audit logs
        await db.processing_audit.create_index([("session_id", 1)])
        await db.processing_audit.create_index([("user_id", 1), ("timestamp", -1)])
        
        logger.info("✓ MongoDB indexes created successfully")
    except Exception as e:
        logger.warning(f"⚠️ Index creation warning: {e}")

# ===== Dependency Injection =====
async def get_database():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return db

async def validate_session(session_id: str, database = Depends(get_database)) -> dict:
    """Validate session exists and is active"""
    session = await database.sessions.find_one({"session_id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Check if expired
    if session.get("expires_at") and session["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Session expired")
    
    if session.get("status") != "active":
        raise HTTPException(status_code=403, detail=f"Session is {session.get('status')}")
    
    return session

async def enforce_consent(session: dict, required_permission: str):
    """Enforce consent permissions"""
    if required_permission == "audio" and not session.get("allow_audio"):
        raise HTTPException(status_code=403, detail="Audio processing not consented")
    
    if required_permission == "video" and not session.get("allow_video"):
        raise HTTPException(status_code=403, detail="Video processing not consented")

async def log_audit(database, session_id: str, user_id: str, action: str, details: dict, stored_data: bool = False):
    """Log processing action for audit trail"""
    audit_record = {
        "session_id": session_id,
        "user_id": user_id,
        "action": action,
        "details": details,
        "stored_sensitive_data": stored_data,
        "timestamp": datetime.utcnow(),
        "ip_address": None  # Can be added from request context
    }
    await database.processing_audit.insert_one(audit_record)

# ===== Health Check =====
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "connected" if db is not None else "disconnected"
    return {
        "status": "healthy",
        "service": "processing_service",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "AI Interview Processing Service",
        "version": "1.0.0",
        "endpoints": [
            "POST /api/session/start",
            "POST /api/upload/audio",
            "POST /api/upload/video",
            "POST /api/process/text",
            "GET /health"
        ],
        "documentation": "/docs"
    }

# Include API router
try:
    from api_endpoints import router as api_router
    app.include_router(api_router)
    logger.info("✓ API endpoints registered")
except Exception as e:
    logger.error(f"✗ Failed to register API endpoints: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "processing_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
