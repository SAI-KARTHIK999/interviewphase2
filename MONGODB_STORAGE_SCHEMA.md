# MongoDB Storage Schema

## Overview

This document describes the complete data storage structure for the AI Interview Bot, including how we store both **original spoken text** and **tokenized format** in MongoDB.

## Collections

### 1. `answers` Collection

This collection stores interview answers with **both original text and tokenized format**.

#### Complete Document Structure

```javascript
{
  // Document ID
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  
  // Session & User Info
  "session_id": "session_a1b2c3d4",
  "user_id": "user_123",
  "consent_id": "consent_abc",
  
  // === ORIGINAL SPOKEN TEXT (from STT) ===
  "original_text": "I have five years of Python experience building web applications with Django and Flask. I'm proficient in REST APIs and database design.",
  
  // Cleaned version (PII redacted if any)
  "cleaned_text": "I have five years of Python experience building web applications with Django and Flask. I'm proficient in REST APIs and database design.",
  
  // === TOKENIZED FORMAT (from Evaluation Service) ===
  "tokens": [
    "I", "have", "five", "years", "of", "Python", "experience", 
    "building", "web", "applications", "with", "Django", "and", 
    "Flask", "I'm", "proficient", "in", "REST", "APIs", "and", 
    "database", "design"
  ],
  "token_count": 22,
  
  // Speech-to-Text Confidence
  "stt_confidence": 0.95,
  
  // === QUALITY SCORES (from Evaluation Service) ===
  "quality_score": 82.5,
  "clarity": 85.0,
  "correctness": 78.0,
  "relevance": 88.0,
  "tone_score": 75.0,
  
  // === EMBEDDINGS (vector representation) ===
  "embedding": [0.123, -0.456, 0.789, ...],  // 384-dimensional array
  "embedding_present": true,
  
  // === METADATA ===
  "analysis_meta": {
    "model_version": "v1.0",
    "processing_time_ms": 1250.5,
    "analyzed_at": ISODate("2025-11-06T18:30:00Z")
  },
  
  "created_at": ISODate("2025-11-06T18:25:00Z")
}
```

#### Storage Workflow

```
1. User speaks answer
   ↓
2. Whisper STT processes audio
   ↓
3. Stores "original_text" in MongoDB
   ↓
4. Evaluation Service retrieves answer
   ↓
5. Tokenizes text → creates "tokens" array
   ↓
6. Computes scores and embedding
   ↓
7. Updates MongoDB with:
   - tokens (tokenized format)
   - token_count
   - quality_score, clarity, correctness, relevance, tone_score
   - embedding (vector)
   ↓
8. MongoDB now contains BOTH:
   - original_text (what was spoken)
   - tokens (tokenized format)
```

#### Field Descriptions

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `original_text` | String | Raw transcript from speech-to-text | "I have 5 years experience..." |
| `cleaned_text` | String | PII-redacted version | "I have 5 years experience..." |
| `tokens` | Array[String] | Tokenized words | ["I", "have", "5", "years", ...] |
| `token_count` | Integer | Number of tokens | 22 |
| `embedding` | Array[Float] | 384-dim vector representation | [0.123, -0.456, ...] |
| `quality_score` | Float | Overall quality (0-100) | 82.5 |
| `clarity` | Float | Communication clarity (0-100) | 85.0 |
| `correctness` | Float | Factual accuracy (0-100) | 78.0 |
| `relevance` | Float | Answer relevance (0-100) | 88.0 |
| `tone_score` | Float | Speaking confidence (0-100) | 75.0 |
| `stt_confidence` | Float | Transcription confidence (0-1) | 0.95 |

#### Indexes

```javascript
// Existing indexes
db.answers.createIndex({ "session_id": 1 })
db.answers.createIndex({ "user_id": 1, "created_at": -1 })
db.answers.createIndex({ "token_count": 1 })

// TTL index - auto-delete after 30 days
db.answers.createIndex(
  { "created_at": 1 }, 
  { expireAfterSeconds: 2592000 }
)
```

### 2. `sessions` Collection

Tracks user sessions and consent permissions.

```javascript
{
  "_id": ObjectId("..."),
  "session_id": "session_a1b2c3d4",
  "user_id": "user_123",
  "consent_id": "consent_abc",
  
  // Consent flags
  "allow_storage": true,    // If false, no text/tokens stored
  "allow_audio": true,
  "allow_video": true,
  
  "created_at": ISODate("2025-11-06T18:00:00Z"),
  "expires_at": ISODate("2025-11-07T18:00:00Z"),  // 24 hours
  "status": "active"
}
```

### 3. `processing_audit` Collection

Permanent audit log of all processing actions.

```javascript
{
  "_id": ObjectId("..."),
  "session_id": "session_a1b2c3d4",
  "user_id": "user_123",
  "consent_id": "consent_abc",
  "action": "answer_analyzed",
  "answer_id": "507f1f77bcf86cd799439011",
  
  "details": {
    "quality_score": 82.5,
    "processing_time_ms": 1250.5,
    "model_version": "v1.0"
  },
  
  // Whether sensitive data was actually stored
  "stored_sensitive_data": true,  // false if allow_storage=false
  
  "timestamp": ISODate("2025-11-06T18:30:00Z")
}
```

## Consent-Based Storage

### When `allow_storage = true`

**Everything is stored:**
```javascript
{
  "original_text": "Full spoken answer...",  // ✅ Stored
  "tokens": ["Full", "spoken", "answer"],  // ✅ Stored
  "token_count": 3,                        // ✅ Stored
  "embedding": [0.1, 0.2, ...],           // ✅ Stored
  "quality_score": 85.0,                   // ✅ Stored
  "clarity": 88.0,                         // ✅ Stored
  // ... all other scores
}
```

### When `allow_storage = false`

**Only metadata is stored:**
```javascript
{
  "original_text": null,        // ❌ Not stored
  "tokens": null,                // ❌ Not stored
  "token_count": null,           // ❌ Not stored
  "embedding": null,             // ❌ Not stored
  "quality_score": null,         // ❌ Not stored
  // Scores are returned to user but NOT persisted
}

// But audit log still records that analysis happened
{
  "action": "answer_analyzed",
  "stored_sensitive_data": false,  // ✅ Logged
  "details": {
    "processing_time_ms": 1200
  }
}
```

## Example Queries

### 1. Get Answer with Both Text and Tokens

```javascript
db.answers.findOne({ _id: ObjectId("507f1f77bcf86cd799439011") })

// Returns:
{
  "original_text": "I have 5 years of Python experience...",
  "tokens": ["I", "have", "5", "years", "of", "Python", "experience"],
  "token_count": 7,
  "quality_score": 82.5
}
```

### 2. Find Answers by Token Count

```javascript
// Find short answers (< 50 tokens)
db.answers.find({ 
  "token_count": { $lt: 50 },
  "quality_score": { $exists: true }
}).sort({ "quality_score": -1 })
```

### 3. Find Answers with Specific Keywords in Tokens

```javascript
// Find answers containing "Python" token
db.answers.find({
  "tokens": "Python"
})

// Find answers containing multiple keywords
db.answers.find({
  "tokens": { $all: ["Python", "Django"] }
})
```

### 4. Get User's Answer History

```javascript
db.answers.find(
  { "user_id": "user_123" },
  { 
    "original_text": 1,
    "tokens": 1,
    "token_count": 1,
    "quality_score": 1,
    "created_at": 1
  }
).sort({ "created_at": -1 })
```

### 5. Aggregate Statistics

```javascript
// Average token count per user
db.answers.aggregate([
  { $match: { "token_count": { $exists: true } } },
  { $group: {
      _id: "$user_id",
      avg_tokens: { $avg: "$token_count" },
      avg_quality: { $avg: "$quality_score" },
      count: { $sum: 1 }
  }}
])
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Interview                        │
└────────────────────┬────────────────────────────────────┘
                     │ User speaks answer
                     ↓
┌─────────────────────────────────────────────────────────┐
│         Processing Service (Port 8000)                   │
│  - Whisper STT: Transcribes audio                       │
│  - Saves to MongoDB:                                    │
│    ✓ original_text: "I have 5 years experience..."     │
│    ✓ stt_confidence: 0.95                               │
└────────────────────┬────────────────────────────────────┘
                     │ STT complete
                     ↓
┌─────────────────────────────────────────────────────────┐
│         Evaluation Service (Port 8001)                   │
│  1. Fetches answer from MongoDB                         │
│     → Reads "original_text"                             │
│                                                          │
│  2. Tokenizes text                                      │
│     → Creates "tokens" array                            │
│     → Counts tokens                                     │
│                                                          │
│  3. Computes scores                                     │
│     → clarity, correctness, relevance, tone             │
│                                                          │
│  4. Computes embedding                                  │
│     → 384-dim vector                                    │
│                                                          │
│  5. Updates MongoDB (if allow_storage=true)             │
│     ✓ tokens: ["I", "have", "5", "years", ...]         │
│     ✓ token_count: 22                                   │
│     ✓ embedding: [0.1, 0.2, ...]                        │
│     ✓ quality_score: 82.5                               │
│     ✓ clarity, correctness, relevance, tone_score       │
│                                                          │
│     Note: original_text PRESERVED from step 1           │
└────────────────────┬────────────────────────────────────┘
                     │ Analysis complete
                     ↓
┌─────────────────────────────────────────────────────────┐
│               MongoDB - answers collection               │
│                                                          │
│  {                                                       │
│    "original_text": "I have 5 years experience...",    │
│    "tokens": ["I", "have", "5", "years", ...],         │
│    "token_count": 22,                                   │
│    "embedding": [0.1, 0.2, ...],                        │
│    "quality_score": 82.5,                               │
│    "clarity": 85.0,                                     │
│    "correctness": 78.0,                                 │
│    "relevance": 88.0,                                   │
│    "tone_score": 75.0                                   │
│  }                                                       │
└─────────────────────────────────────────────────────────┘
```

## Verification Steps

### 1. Verify Original Text is Stored

```javascript
// After STT processing
db.answers.findOne(
  { _id: ObjectId("YOUR_ANSWER_ID") },
  { original_text: 1, stt_confidence: 1 }
)

// Should return:
{
  "_id": ObjectId("..."),
  "original_text": "I have 5 years of Python experience...",
  "stt_confidence": 0.95
}
```

### 2. Verify Tokens are Added After Analysis

```javascript
// After evaluation service analysis
db.answers.findOne(
  { _id: ObjectId("YOUR_ANSWER_ID") },
  { original_text: 1, tokens: 1, token_count: 1 }
)

// Should return:
{
  "_id": ObjectId("..."),
  "original_text": "I have 5 years of Python experience...",
  "tokens": ["I", "have", "5", "years", "of", "Python", "experience"],
  "token_count": 7
}
```

### 3. Verify Both are Present

```javascript
db.answers.findOne({ _id: ObjectId("YOUR_ANSWER_ID") })

// Should contain BOTH:
// ✓ original_text (from STT)
// ✓ tokens (from Evaluation)
// ✓ token_count
// ✓ quality_score, clarity, etc.
```

## Best Practices

1. **Always check consent** before querying sensitive fields
2. **Use projections** to limit data exposure:
   ```javascript
   // Only get what you need
   db.answers.find({}, { tokens: 1, token_count: 1, quality_score: 1 })
   ```

3. **Respect TTL** - data auto-deletes after 30 days
4. **Monitor token_count** - useful for answer length analysis
5. **Use tokens for search** - faster than full-text search on original_text

## Summary

✅ **Original Text Storage**: Stored by Processing Service (Whisper STT)
✅ **Tokenized Format Storage**: Stored by Evaluation Service (answer_scorer)
✅ **Both Coexist**: MongoDB document contains both formats
✅ **Consent Enforced**: Storage only happens if `allow_storage=true`
✅ **Audit Trail**: Always logged, even when not storing

**The system now stores BOTH what the user spoke (original_text) AND the tokenized format (tokens array) in MongoDB!**
