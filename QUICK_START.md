# Quick Start Guide - Privacy-First AI Interview Bot

## Prerequisites

- **Node.js** (v14 or higher)
- **Python** 3.8+
- **MongoDB** (local instance running on port 27017)
- **npm** or **yarn**

## Installation

### 1. Start MongoDB

```bash
# Windows (if MongoDB is installed as service)
net start MongoDB

# Or start manually
mongod

# Verify connection
mongo --eval "db.version()"
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
# Or create virtual environment first:
python -m venv .venv
.venv\Scripts\activate  # On Windows
pip install flask flask-cors pymongo
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
# or
yarn install
```

## Running the Application

### Option 1: Using Provided Scripts (Recommended)

**Windows:**
```bash
# Terminal 1 - Start Backend
start_backend.bat

# Terminal 2 - Start Frontend
start_frontend.bat
```

**Or use the all-in-one runner:**
```bash
python run_both.py
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```
Backend will start on http://localhost:5001

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```
Frontend will open on http://localhost:3000

## Testing the Consent System

### Test 1: Full Recording with Data Storage

1. Navigate to http://localhost:3000
2. Log in (or create account if required)
3. Go to **Interview** page
4. **ConsentModal appears automatically**
5. Select: **"✅ Allow Recording and Save Data"**
6. Click **"Continue with Selected Option"**
7. You'll see consent status:
   - 🎤 Audio: Enabled
   - 📹 Video: Enabled
   - 💾 Storage: Enabled (30 days)
8. Click **"Start Recording"**
9. Answer the interview question (speak for 10-30 seconds)
10. Click **"Stop Recording"**
11. Click **"Submit Video"**
12. Wait for analysis results

**What Happens:**
- Consent logged in MongoDB `user_consent_logs` collection
- Video analyzed (transcription, facial analysis, scoring)
- Data saved in `interviews` collection with 30-day TTL
- Video file remains in `backend/uploads/`
- Feedback displayed with score

**Verify in MongoDB Compass:**
```javascript
// Check consent log
db.user_consent_logs.find().sort({timestamp: -1}).limit(1)

// Check interview saved with consent_id
db.interviews.find().sort({createdAt: -1}).limit(1)
```

### Test 2: Recording Without Saving Data

1. Go to Interview page (or refresh to restart)
2. **ConsentModal appears**
3. Select: **"🔒 Allow Recording but Don't Save"**
4. Click **"Continue with Selected Option"**
5. Notice the privacy badge: **"🔒 Not Saving Data"**
6. Consent status shows: **"💾 Storage: Disabled"**
7. Record and submit video as before

**What Happens:**
- Consent logged with `allow_storage: false`
- Video analyzed normally
- Results returned to frontend
- **Video file immediately deleted** from disk
- **NO record in `interviews` collection**

**Verify:**
```javascript
// Consent exists
db.user_consent_logs.find({allow_storage: false}).sort({timestamp: -1}).limit(1)

// NO interview record for this consent_id
db.interviews.count({consent_id: "[the_consent_id_from_above]"})
// Should return: 0
```

```bash
# Check uploads folder - video should be gone
dir backend\uploads\
```

### Test 3: Practice Mode (No Recording)

1. Go to Interview page
2. **ConsentModal appears**
3. Select: **"🚫 Decline Recording"**
4. Click **"Continue with Selected Option"**
5. You'll see **Practice Mode** interface:
   - No webcam
   - No recording controls
   - Text-only answer box
   - Message: "Privacy Protected - Practice Mode"

**What Happens:**
- Consent logged with `session_mode: "practice"`
- No audio/video capture occurs
- Zero data collection
- Completely anonymous

**Verify:**
```javascript
db.user_consent_logs.find({session_mode: "practice"}).sort({timestamp: -1}).limit(1)
```

### Test 4: Changing Consent Mid-Session

1. Complete Test 1 or Test 2
2. Click **"Modify Consent"** button (below consent status)
3. ConsentModal reopens
4. Select a different option
5. Notice the UI updates accordingly

**What Happens:**
- New consent record created with new `consent_id`
- Session mode changes immediately
- Previous consent remains in audit log

### Test 5: Manual Data Deletion

1. Complete Test 1 (save data)
2. Note your session ID from the response (or query MongoDB)
3. Send DELETE request:

```bash
curl -X POST http://localhost:5001/api/data/delete ^
  -H "Content-Type: application/json" ^
  -d "{\"command\": \"Delete my data now\", \"user_id\": \"YOUR_SESSION_ID\"}"
```

**PowerShell:**
```powershell
$body = @{
    command = "Delete my data now"
    user_id = "YOUR_SESSION_ID"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:5001/api/data/delete `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

**What Happens:**
- MongoDB documents deleted
- Video files removed from filesystem
- Deletion logged in `deletion_log`
- Confirmation returned

## Verifying the System

### Check Consent Logs
```javascript
// MongoDB Compass or Shell
use interview_db
db.user_consent_logs.find().pretty()
```

### Check Interview Data
```javascript
db.interviews.find().pretty()
// Should show consent_id linkage
```

### Check Deletion Logs
```javascript
db.deletion_log.find().pretty()
```

### Check TTL Index
```javascript
db.interviews.getIndexes()
// Look for: expireAfterSeconds: 2592000 (30 days)
```

## API Endpoints

Base URL: http://localhost:5001

### Health Check
```bash
curl http://localhost:5001/api/health
```

### Data Retention Info
```bash
curl http://localhost:5001/api/data/retention-info
```

### Interview History
```bash
curl http://localhost:5001/api/interview/history
```

### Consent Endpoint
```bash
curl -X POST http://localhost:5001/api/consent \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test@example.com", "allow_audio": true, "allow_video": true, "allow_storage": false, "session_mode": "record"}'
```

## Troubleshooting

### Issue: ConsentModal doesn't appear
**Solution:** 
- Clear browser cache and localStorage
- Check browser console for React errors
- Verify ConsentModal.js was created correctly

### Issue: "Cannot connect to MongoDB"
**Solution:**
```bash
# Check if MongoDB is running
mongo --eval "db.version()"

# Start MongoDB service
net start MongoDB  # Windows

# Or start manually
mongod --dbpath C:\data\db
```

### Issue: CORS errors in browser console
**Solution:**
- Verify backend has `flask-cors` installed
- Check that backend is running on port 5001
- Frontend should be on port 3000

### Issue: Video upload fails
**Solution:**
- Check `backend/uploads/` directory exists
- Verify file size < 50MB
- Check backend console for error messages

### Issue: Data not being deleted when "Don't Save" selected
**Solution:**
- Check backend console for deletion log message
- Verify `opt_in_data_save` is being sent as "false"
- Look for: "Deleted uploaded file immediately due to no-save consent"

## Features Overview

✅ **Three Consent Options:**
1. Save data (30 days)
2. Temporary processing (immediate deletion)
3. Practice mode (no recording)

✅ **Transparency:**
- Clear explanations of data usage
- Real-time consent status display
- Privacy policy embedded in modal

✅ **User Control:**
- Modify consent anytime
- Manual data deletion
- Practice without recording

✅ **Privacy Protection:**
- Immediate file deletion when not saving
- Anonymization of stored data
- 30-day auto-deletion via TTL
- Audit trail of all consent actions

✅ **Compliance:**
- GDPR-aligned consent process
- Data minimization principle
- Right to be forgotten
- Transparent data retention policy

## Next Steps

1. **Read Full Documentation:**
   - `CONSENT_IMPLEMENTATION_GUIDE.md` - Complete technical documentation
   - `PRIVACY_POLICY.md` - User-facing privacy policy

2. **Test All Scenarios:**
   - Follow test cases in implementation guide
   - Verify data deletion works correctly
   - Test consent modification flow

3. **Customize for Production:**
   - Update privacy policy with actual contact info
   - Enable HTTPS/SSL
   - Add MongoDB authentication
   - Implement rate limiting

4. **Monitor and Audit:**
   - Regularly review consent logs
   - Track data retention compliance
   - Audit deletion effectiveness

## Support

For questions or issues:
- Check `CONSENT_IMPLEMENTATION_GUIDE.md` for detailed troubleshooting
- Review `PRIVACY_POLICY.md` for privacy-related questions
- Examine backend console logs for server errors
- Check browser console for frontend issues

---

**Privacy First, Always.** 🔒
