# AI Interview Processing Service

Privacy-first FastAPI microservice for audio/video/text processing with Whisper STT, MediaPipe face analysis, and advanced NLP tokenization.

## Features

- 🎤 **Speech-to-Text**: Whisper-based transcription with chunking support for long audio
- 📹 **Video Analysis**: MediaPipe face detection with attention/emotion scoring  
- 📝 **NLP Processing**: PII detection/redaction, spaCy tokenization, sentence embeddings
- 🔐 **Consent Enforcement**: Server-side validation of storage permissions
- 📊 **MongoDB Storage**: Indexed collections with automatic 30-day TTL cleanup
- 🔍 **Audit Logging**: Complete audit trail of all processing actions

## Architecture

```
Processing Service (FastAPI on port 8000)
│
├── /api/session/start → Create processing session with consent
├── /api/upload/audio → Whisper STT transcription
├── /api/upload/video → MediaPipe face/emotion analysis
└── /api/process/text → PII detection + tokenization + embeddings

MongoDB Collections:
├── sessions → Active processing sessions
├── answers → Tokenized text with embeddings (TTL 30 days)
├── video_analysis → Face/attention metrics (TTL 30 days)
└── processing_audit → Complete audit trail
```

## Installation

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements_processing.txt
```

### 2. Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 3. Set Environment Variables (Optional)

```bash
# Create .env file
MONGODB_URL=mongodb://localhost:27017
WHISPER_MODEL=base  # tiny, base, small, medium, large
```

## Running the Service

### Start the Server

```bash
python processing_service.py
```

Server runs on **http://localhost:8000**  
API Documentation: **http://localhost:8000/docs**

## API Endpoints

### 1. Start Session

**POST /api/session/start**

Create a new processing session with consent validation.

**Request Body:**
```json
{
  "user_id": "user_123",
  "consent_id": "consent_abc",
  "allow_storage": false,
  "allow_audio": true,
  "allow_video": true
}
```

**Response (201):**
```json
{
  "session_id": "session_a1b2c3d4",
  "user_id": "user_123",
  "consent_id": "consent_abc",
  "allow_storage": false,
  "created_at": "2025-11-06T18:00:00Z",
  "expires_at": "2025-11-07T18:00:00Z",
  "status": "active"
}
```

### 2. Upload Audio

**POST /api/upload/audio**

Process audio file with Whisper STT. Supports chunking for files > 30 seconds.

**Form Data:**
- `session_id`: Session identifier (required)
- `audio_file`: Audio file (WAV, MP3, etc.) up to 50MB
- `language`: Optional language code (e.g., "en")

**Response (202):**
```json
{
  "session_id": "session_a1b2c3d4",
  "original_text": "Hello, my name is John and I'm excited about this opportunity...",
  "stt_confidence": 0.93,
  "stt_timestamp": "2025-11-06T18:05:00Z",
  "duration_seconds": 45.2,
  "partial": false,
  "chunk_count": 2
}
```

### 3. Upload Video

**POST /api/upload/video**

Process video with MediaPipe for face detection and attention analysis.

**Form Data:**
- `session_id`: Session identifier (required)
- `video_file`: Video file (WebM, MP4) up to 100MB

**Response (202):**
```json
{
  "session_id": "session_a1b2c3d4",
  "frames_processed": 120,
  "faces_detected": 115,
  "attention_score": 0.87,
  "emotion_summary": {
    "neutral": 0.7,
    "happy": 0.2,
    "engaged": 0.8
  },
  "processing_time_seconds": 12.4
}
```

### 4. Process Text

**POST /api/process/text**

Clean, tokenize, detect PII, and optionally compute embeddings.

**Request Body:**
```json
{
  "session_id": "session_a1b2c3d4",
  "original_text": "My email is john@example.com and my phone is 555-123-4567",
  "compute_embedding": true
}
```

**Response (200):**
```json
{
  "session_id": "session_a1b2c3d4",
  "cleaned_text": "My email is [EMAIL_REDACTED] and my phone is [PHONE_REDACTED]",
  "tokens": ["My", "email", "is", "[EMAIL_REDACTED]", "and", "my", "phone", "is", "[PHONE_REDACTED]"],
  "token_count": 9,
  "pii_redacted": true,
  "pii_flags": ["email", "phone"],
  "embedding_present": true,
  "embedding_dimensions": 384
}
```

## Consent Enforcement

### Storage Rules

**If `allow_storage=false`:**
- ✅ Audio/video/text **processed normally**
- ✅ Results **returned to client**
- ❌ `original_text`, `tokens`, `embedding` **NOT saved to MongoDB**
- ✅ Audit log created (no sensitive data)

**If `allow_storage=true`:**
- ✅ All processing results **saved to MongoDB**
- ✅ 30-day TTL auto-deletion applied
- ✅ Full audit trail with stored data flag

### Consent Validation

All endpoints validate session consent before processing:

```python
# Audio endpoint checks allow_audio
# Video endpoint checks allow_video  
# Both respect allow_storage for persistence
```

**Error Codes:**
- `403`: Consent denied (missing permission)
- `404`: Session not found
- `400`: Invalid input
- `413`: File too large
- `500`: Processing error

## MongoDB Collections

### `sessions`
Tracks active processing sessions.

```javascript
{
  session_id: "session_a1b2c3d4",
  user_id: "user_123",
  consent_id: "consent_abc",
  allow_storage: false,
  allow_audio: true,
  allow_video: true,
  created_at: ISODate(...),
  expires_at: ISODate(...),
  status: "active"
}
```

**Indexes:** `session_id` (unique), `(user_id, created_at)`

### `answers`
Stores tokenized text responses (only if `allow_storage=true`).

```javascript
{
  _id: ObjectId(...),
  session_id: "session_a1b2c3d4",
  user_id: "user_123",
  consent_id: "consent_abc",
  original_text: "My answer...",
  cleaned_text: "My answer...",
  tokens: ["My", "answer"],
  token_count: 2,
  stt_confidence: 0.93,
  embedding: [0.1, 0.2, ...],  // 384-dim vector
  embedding_present: true,
  created_at: ISODate(...)
}
```

**Indexes:** `session_id`, `(user_id, created_at)`, `token_count`, TTL on `created_at` (30 days)

**Token Storage:** Tokens are stored in the `tokens` array field as strings.

### `video_analysis`
Stores facial analysis metrics (only if `allow_storage=true`).

```javascript
{
  session_id: "session_a1b2c3d4",
  user_id: "user_123",
  consent_id: "consent_abc",
  frames_processed: 120,
  faces_detected: 115,
  attention_score: 0.87,
  emotion_summary: {...},
  created_at: ISODate(...)
}
```

**Indexes:** `session_id`, TTL on `created_at` (30 days)

### `processing_audit`
Complete audit trail of all actions.

```javascript
{
  session_id: "session_a1b2c3d4",
  user_id: "user_123",
  action: "text_processed",
  details: {
    token_count: 42,
    pii_redacted: true,
    pii_flags: ["email"]
  },
  stored_sensitive_data: false,
  timestamp: ISODate(...)
}
```

**Indexes:** `session_id`, `(user_id, timestamp)`

## Data Retention Policy

### Automatic Deletion (TTL)

- **answers** collection: 30-day TTL on `created_at`
- **video_analysis** collection: 30-day TTL on `created_at`
- MongoDB automatically removes expired documents

### Manual Re-tokenization

To re-run tokenization on stored text:

```python
from processors.text_processor import get_text_processor

text_processor = get_text_processor()
result = await text_processor.process_text(original_text, compute_embedding=True)
# Updates tokens in answers collection
```

### Privacy-Friendly Practices

1. **Minimal Storage**: Only store when `allow_storage=true`
2. **PII Redaction**: Automatic detection and removal of emails, phones, SSNs
3. **TTL Cleanup**: All data expires after 30 days
4. **Audit Trail**: Complete log of who accessed/processed what
5. **No Cross-Session Leakage**: Sessions expire after 24 hours

## Testing

### Run Unit Tests

```bash
pytest tests/test_processors.py -v
```

### Test PII Redaction

```bash
pytest tests/test_pii_redaction.py -v
```

### Test Consent Enforcement

```bash
pytest tests/test_consent.py -v
```

### Manual Testing with cURL

**Start Session:**
```bash
curl -X POST http://localhost:8000/api/session/start \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test_user","consent_id":"consent_123","allow_storage":false,"allow_audio":true,"allow_video":true}'
```

**Process Text:**
```bash
curl -X POST http://localhost:8000/api/process/text \
  -H "Content-Type: application/json" \
  -d '{"session_id":"SESSION_ID","original_text":"Test message with john@example.com","compute_embedding":false}'
```

## Configuration

Edit `processing_service.py` Settings class:

```python
class Settings:
    MONGODB_URL = "mongodb://localhost:27017"
    DATABASE_NAME = "interview_db"
    MAX_AUDIO_SIZE_MB = 50
    MAX_VIDEO_SIZE_MB = 100
    WHISPER_MODEL = "base"  # Change to "large" for better accuracy
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    AUDIO_CHUNK_DURATION = 30  # seconds
    RETENTION_DAYS = 30
```

## Troubleshooting

### Whisper Not Found
```bash
pip install openai-whisper
# Or use mock mode (automatically enabled if not installed)
```

### spaCy Model Missing
```bash
python -m spacy download en_core_web_sm
```

### MongoDB Connection Error
```bash
# Check MongoDB is running
mongosh --eval "db.version()"

# Or start MongoDB service
net start MongoDB  # Windows
```

### CUDA Out of Memory (Whisper)
```python
# Use smaller model
settings.WHISPER_MODEL = "tiny"  # or "base"
```

## Production Deployment

1. **Enable HTTPS**: Use reverse proxy (nginx)
2. **Add Authentication**: JWT tokens for API access
3. **Rate Limiting**: Prevent abuse (e.g., 10 req/min per user)
4. **Monitoring**: Track processing times, error rates
5. **Backup MongoDB**: Regular backups of audit logs
6. **Scale Workers**: Use Gunicorn with multiple workers
7. **GPU Support**: Deploy on GPU instance for faster Whisper

## License

Privacy-first AI processing service - demonstrating ethical data handling.
