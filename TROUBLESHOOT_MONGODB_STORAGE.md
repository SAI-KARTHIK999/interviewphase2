# Troubleshooting: MongoDB Not Showing Tokens

## Quick Diagnosis

Run this verification script to check what's actually in MongoDB:

```bash
python verify_mongodb_storage.py
```

This will show you:
- ✅ or ❌ for `original_text`
- ✅ or ❌ for `tokens`
- ✅ or ❌ for `token_count`
- Sample of what's stored

## Common Issues & Solutions

### Issue 1: No Data in MongoDB at All

**Symptoms:**
```
Total answers in database: 0
```

**Cause:** Either:
1. Audio hasn't been uploaded yet
2. `allow_storage` is set to `false` in consent

**Solution:**
```javascript
// Check MongoDB
db.sessions.findOne({}, {allow_storage: 1})

// Should show: {allow_storage: true}
```

If `allow_storage` is false, recreate session with storage enabled.

### Issue 2: Text Present, Tokens Missing

**Symptoms:**
```
✅ original_text: PRESENT
❌ tokens: MISSING
```

**Cause:** Text processor not being called or failing silently

**Solution:** Check the logs when uploading audio:
```
✓ Transcript AND tokens stored for session {session_id}
```

If you don't see this message, the text processor might be failing.

**Fix:** Add more detailed logging in `api_endpoints.py`:

```python
# In upload_audio function, around line 135
try:
    text_processor = get_text_processor()
    logger.info(f"🔄 Processing text for tokenization...")
    
    text_result = await text_processor.process_text(
        result["original_text"],
        compute_embedding=True,
        lowercase_tokens=False
    )
    
    logger.info(f"✓ Text processed: {text_result['token_count']} tokens generated")
    logger.info(f"   Tokens sample: {text_result['tokens'][:5]}")
    
    # ... rest of code
except Exception as e:
    logger.error(f"✗ Text processing failed: {e}", exc_info=True)
    raise  # Re-raise to see the full error
```

### Issue 3: Empty Tokens Array

**Symptoms:**
```
✅ tokens: PRESENT (array with 0 tokens)
```

**Cause:** Empty text or text processor issue

**Solution:** Check if `original_text` has content:

```python
# Add this check in api_endpoints.py before text processing
if not result["original_text"] or result["original_text"].strip() == "":
    logger.error("❌ Empty original_text from Whisper!")
    raise HTTPException(status_code=500, detail="Empty transcript")
```

### Issue 4: Old Schema (Using `cleaned_text` instead of `original_text`)

**Symptoms:**
```
ℹ️  original_text: Not present
✅ cleaned_text: PRESENT
```

**Cause:** Old code or mixed versions

**Solution:** Ensure you're using the latest `api_endpoints.py` code (lines 142-154):

```python
answer_doc = {
    "session_id": session_id,
    "user_id": session["user_id"],
    "consent_id": session["consent_id"],
    "original_text": result["original_text"],      # ← Must be here
    "cleaned_text": text_result["cleaned_text"],
    "tokens": text_result["tokens"],                # ← Must be here
    "token_count": text_result["token_count"],
    "stt_confidence": result["stt_confidence"],
    "embedding": text_result.get("embedding"),
    "embedding_present": text_result["embedding_present"],
    "created_at": datetime.utcnow()
}
```

## Manual Test

### Step 1: Create Test Session

```bash
curl -X POST http://localhost:8000/api/session/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_001",
    "consent_id": "consent_test",
    "allow_storage": true,
    "allow_audio": true,
    "allow_video": true
  }'
```

Save the `session_id` from response.

### Step 2: Upload Audio

```bash
curl -X POST http://localhost:8000/api/upload/audio \
  -F "session_id=YOUR_SESSION_ID" \
  -F "audio_file=@path/to/audio.wav"
```

### Step 3: Check MongoDB

```javascript
// Connect to MongoDB
mongo

// Switch to database
use interview_db

// Find the latest answer
db.answers.find().sort({created_at: -1}).limit(1).pretty()

// Should show document like:
{
  "original_text": "I have five years of Python experience...",
  "tokens": ["I", "have", "five", "years", "of", "Python", "experience"],
  "token_count": 7,
  ...
}
```

## Verify Both Fields Are Present

```javascript
// Query to check if both fields exist
db.answers.aggregate([
  {
    $project: {
      session_id: 1,
      has_original_text: { $cond: [{ $ifNull: ["$original_text", false] }, true, false] },
      has_tokens: { $cond: [{ $ifNull: ["$tokens", false] }, true, false] },
      token_count: 1,
      created_at: 1
    }
  },
  { $sort: { created_at: -1 } },
  { $limit: 10 }
])

// Output should show:
// has_original_text: true
// has_tokens: true
```

## Quick Fix: Force Re-process Existing Answers

If you have answers with text but no tokens, run this update script:

```python
# fix_missing_tokens.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys
sys.path.insert(0, 'backend')
from processors.text_processor import get_text_processor

async def fix_missing_tokens():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["interview_db"]
    
    # Find answers without tokens
    cursor = db.answers.find({
        "$or": [
            {"tokens": {"$exists": False}},
            {"tokens": []}
        ],
        "original_text": {"$exists": True}
    })
    
    text_processor = get_text_processor()
    fixed_count = 0
    
    async for doc in cursor:
        try:
            # Process text to get tokens
            text_result = await text_processor.process_text(
                doc["original_text"],
                compute_embedding=False,
                lowercase_tokens=False
            )
            
            # Update document
            await db.answers.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "tokens": text_result["tokens"],
                    "token_count": text_result["token_count"],
                    "cleaned_text": text_result["cleaned_text"]
                }}
            )
            
            fixed_count += 1
            print(f"✓ Fixed {doc['_id']}: added {text_result['token_count']} tokens")
            
        except Exception as e:
            print(f"✗ Failed to fix {doc['_id']}: {e}")
    
    print(f"\n✅ Fixed {fixed_count} documents")
    client.close()

if __name__ == "__main__":
    asyncio.run(fix_missing_tokens())
```

Run it:
```bash
python fix_missing_tokens.py
```

## Expected MongoDB Document Structure

After upload, each document in `answers` collection should look like:

```javascript
{
  "_id": ObjectId("..."),
  "session_id": "session_abc123",
  "user_id": "user_123",
  "consent_id": "consent_xyz",
  
  // === BOTH OF THESE MUST BE PRESENT ===
  "original_text": "I have five years of Python experience building web applications",
  "tokens": ["I", "have", "five", "years", "of", "Python", "experience", "building", "web", "applications"],
  "token_count": 10,
  // =====================================
  
  "cleaned_text": "I have five years of Python experience building web applications",
  "stt_confidence": 0.95,
  "embedding": [0.1, 0.2, 0.3, ...],  // 384-dimensional array
  "embedding_present": true,
  "created_at": ISODate("2025-11-06T19:40:00Z")
}
```

## Still Not Working?

### Check Processing Service Logs

When you upload audio, you should see:
```
📁 Audio file saved: 12345 bytes
🔄 Processing with Whisper...
✓ Audio processed
🔄 Processing text for tokenization...
✓ Text processed: 42 tokens generated
✓ Transcript AND tokens stored for session session_abc123
```

If you see errors instead, that's your issue.

### Check Text Processor

Test the text processor directly:

```python
python
>>> import sys
>>> sys.path.insert(0, 'backend')
>>> from processors.text_processor import get_text_processor
>>> import asyncio
>>> 
>>> processor = get_text_processor()
>>> text = "I have five years of Python experience"
>>> result = asyncio.run(processor.process_text(text, compute_embedding=False))
>>> print(result['tokens'])
['I', 'have', 'five', 'years', 'of', 'Python', 'experience']
>>> print(result['token_count'])
7
```

If this fails, there's an issue with the text processor initialization.

## Summary Checklist

- [ ] Run `verify_mongodb_storage.py` to see current state
- [ ] Verify `allow_storage=true` in session
- [ ] Check processing service logs for errors
- [ ] Ensure latest `api_endpoints.py` code is deployed
- [ ] Test text processor directly
- [ ] Upload new audio and check immediately
- [ ] Run `fix_missing_tokens.py` if needed for old data

**Both `original_text` and `tokens` should always be stored together!**
