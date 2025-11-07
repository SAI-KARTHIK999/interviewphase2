# Complete Fix: Store Both Original Text and Tokens in MongoDB

## Problem Identified

Currently, the system processes audio/text but the storage is **split across two endpoints**:
1. `/upload/audio` - Returns transcript but doesn't store it
2. `/process/text` - Stores both original_text and tokens

This means if the frontend only calls the audio endpoint and doesn't follow up with text processing, **nothing gets stored in MongoDB**.

## Solution: Ensure Complete Storage

### Option 1: Auto-store after audio processing (Recommended)

Modify the audio endpoint to automatically store the transcript after STT processing.

### Option 2: Update frontend to call both endpoints

Ensure frontend calls `/process/text` after `/upload/audio`.

## Implementation

### Backend Fix: Auto-store transcript after STT

Update `backend/api_endpoints.py` to store the original transcript immediately after audio processing:

```python
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
    
    NOW ALSO STORES the original transcript to MongoDB
    """
    session = await validate_session(session_id, database)
    await enforce_consent(session, "audio")
    
    temp_path = None
    try:
        # ... existing audio processing code ...
        
        audio_processor = get_audio_processor(settings.WHISPER_MODEL, settings.AUDIO_CHUNK_DURATION)
        result = await audio_processor.process_audio(temp_path, language, timeout=300)
        
        # === NEW: Store transcript immediately if consent allows ===
        if session["allow_storage"]:
            # Process text to get tokens
            text_processor = get_text_processor()
            text_result = await text_processor.process_text(
                result["original_text"],
                compute_embedding=True,
                lowercase_tokens=False
            )
            
            # Store complete document with BOTH original text and tokens
            answer_doc = {
                "session_id": session_id,
                "user_id": session["user_id"],
                "consent_id": session["consent_id"],
                "original_text": result["original_text"],      # ✅ Original spoken text
                "cleaned_text": text_result["cleaned_text"],
                "tokens": text_result["tokens"],                # ✅ Tokenized format
                "token_count": text_result["token_count"],
                "stt_confidence": result["stt_confidence"],
                "embedding": text_result.get("embedding"),
                "embedding_present": text_result["embedding_present"],
                "created_at": datetime.utcnow()
            }
            await database.answers.insert_one(answer_doc)
            logger.info(f"✓ Transcript AND tokens stored for session {session_id}")
        
        # Log audit
        await log_audit(
            database, session_id, session["user_id"],
            "audio_processed_and_stored",
            {
                "filename": audio_file.filename,
                "duration": result["duration_seconds"],
                "confidence": result["stt_confidence"],
                "stored": session["allow_storage"]
            },
            session["allow_storage"]
        )
        
        return AudioProcessResult(
            session_id=session_id,
            original_text=result["original_text"],
            stt_confidence=result["stt_confidence"],
            stt_timestamp=result["stt_timestamp"],
            duration_seconds=result["duration_seconds"],
            partial=result.get("partial", False),
            chunk_count=result.get("chunk_count", 1)
        )
        
    except Exception as e:
        logger.error(f"✗ Audio processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
```

### MongoDB Document Structure (After Fix)

```javascript
// After calling /upload/audio
db.answers.findOne({ session_id: "session_abc123" })

// Returns:
{
  "_id": ObjectId("..."),
  "session_id": "session_abc123",
  "user_id": "user_123",
  "consent_id": "consent_xyz",
  
  // === ORIGINAL SPOKEN TEXT (from Whisper STT) ===
  "original_text": "I have five years of Python experience building web applications with Django and Flask",
  
  // === CLEANED TEXT (PII redacted if any) ===
  "cleaned_text": "I have five years of Python experience building web applications with Django and Flask",
  
  // === TOKENIZED FORMAT (automatically generated) ===
  "tokens": [
    "I", "have", "five", "years", "of", "Python", "experience",
    "building", "web", "applications", "with", "Django", "and", "Flask"
  ],
  "token_count": 14,
  
  // === STT METADATA ===
  "stt_confidence": 0.95,
  
  // === EMBEDDING (384-dimensional vector) ===
  "embedding": [0.123, -0.456, 0.789, ...],
  "embedding_present": true,
  
  // === TIMESTAMPS ===
  "created_at": ISODate("2025-11-06T19:20:00Z")
}
```

## Verification Steps

### 1. Test Audio Upload with Storage

```bash
# Start services
cd backend
python processing_service.py  # Port 8000

# Create a session (from another terminal)
curl -X POST http://localhost:8000/api/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "consent_id": "consent_123",
    "allow_storage": true,
    "allow_audio": true,
    "allow_video": true
  }'

# Response will include session_id
# Use that session_id for next step

# Upload audio file
curl -X POST http://localhost:8000/api/upload/audio \
  -F "session_id=YOUR_SESSION_ID" \
  -F "audio_file=@path/to/audio.wav"
```

### 2. Check MongoDB

```javascript
// Connect to MongoDB
mongo

// Switch to database
use interview_db

// Find the stored answer
db.answers.find().pretty()

// Should show document with BOTH:
{
  "original_text": "...",  // ✅ Full spoken text
  "tokens": [...],          // ✅ Tokenized array
  "token_count": 14
}
```

### 3. Verify Both Fields Exist

```javascript
// Query for specific fields
db.answers.find(
  {},
  {
    original_text: 1,
    tokens: 1,
    token_count: 1,
    _id: 0
  }
)

// Expected output:
{
  "original_text": "I have five years...",
  "tokens": ["I", "have", "five", "years", ...],
  "token_count": 14
}
```

## Frontend Display

Update your React components to display both formats:

```jsx
// components/AnswerDisplay.jsx
import React from 'react';

const AnswerDisplay = ({ answer }) => {
  return (
    <div className="answer-container">
      {/* Original Spoken Text */}
      <div className="original-text-section">
        <h3>📝 Original Transcript</h3>
        <p className="original-text">{answer.original_text}</p>
        <span className="confidence-badge">
          Confidence: {(answer.stt_confidence * 100).toFixed(0)}%
        </span>
      </div>

      {/* Tokenized Format */}
      <div className="tokens-section">
        <h3>🔤 Tokenized Format ({answer.token_count} tokens)</h3>
        <div className="tokens-grid">
          {answer.tokens.map((token, idx) => (
            <span key={idx} className="token-badge">
              {token}
            </span>
          ))}
        </div>
      </div>

      {/* Quality Scores */}
      {answer.quality_score && (
        <div className="scores-section">
          <h3>📊 Quality Score: {answer.quality_score.toFixed(1)}/100</h3>
          {/* Use AnswerScores component here */}
        </div>
      )}
    </div>
  );
};

export default AnswerDisplay;
```

### Styling (AnswerDisplay.css)

```css
.answer-container {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin: 20px 0;
}

.original-text-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 2px solid #e2e8f0;
}

.original-text-section h3 {
  color: #1e293b;
  font-size: 18px;
  margin-bottom: 12px;
}

.original-text {
  font-size: 16px;
  line-height: 1.6;
  color: #334155;
  padding: 16px;
  background: #f8fafc;
  border-left: 4px solid #3b82f6;
  border-radius: 4px;
}

.confidence-badge {
  display: inline-block;
  margin-top: 8px;
  padding: 4px 12px;
  background: #10b981;
  color: white;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
}

.tokens-section {
  margin-bottom: 24px;
}

.tokens-section h3 {
  color: #1e293b;
  font-size: 18px;
  margin-bottom: 12px;
}

.tokens-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.token-badge {
  display: inline-block;
  padding: 6px 12px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  font-size: 14px;
  color: #1e40af;
  font-family: 'Courier New', monospace;
}

.scores-section {
  padding-top: 24px;
  border-top: 2px solid #e2e8f0;
}
```

## API Response Format

After the fix, the `/upload/audio` endpoint will return:

```json
{
  "session_id": "session_abc123",
  "original_text": "I have five years of Python experience...",
  "stt_confidence": 0.95,
  "stt_timestamp": "2025-11-06T19:20:00Z",
  "duration_seconds": 12.5,
  "partial": false,
  "chunk_count": 1
}
```

**And MongoDB will contain:**

```javascript
{
  "original_text": "I have five years of Python experience...",  // ✅
  "tokens": ["I", "have", "five", "years", ...],                 // ✅
  "token_count": 14,                                            // ✅
  "stt_confidence": 0.95                                        // ✅
}
```

## Benefits

✅ **Single API call** - Frontend only needs to call `/upload/audio`
✅ **Immediate storage** - Both formats stored right away
✅ **Consistent data** - Original text and tokens always in sync
✅ **Better UX** - No need for separate tokenization step
✅ **Consent respected** - Only stores if `allow_storage=true`

## Testing Checklist

- [ ] Upload audio file via `/upload/audio`
- [ ] Check MongoDB for new document in `answers` collection
- [ ] Verify `original_text` field contains full transcript
- [ ] Verify `tokens` array contains tokenized words
- [ ] Verify `token_count` matches array length
- [ ] Test with `allow_storage=false` (should not store)
- [ ] Display both formats in frontend
- [ ] Test with long audio (>30s) to verify chunking works
- [ ] Verify evaluation service can still analyze stored answers

## Summary

**Before Fix:**
- Audio endpoint returned transcript but didn't store
- Had to manually call `/process/text` to store
- Risk of data loss if second call not made

**After Fix:**
- Audio endpoint processes AND stores in one step
- MongoDB contains both `original_text` and `tokens`
- Frontend gets both formats immediately
- System is more robust and user-friendly

🎯 **Result: MongoDB now stores BOTH what was spoken (original_text) AND the tokenized format (tokens array) automatically after audio processing!**
