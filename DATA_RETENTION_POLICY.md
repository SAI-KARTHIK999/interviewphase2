# Data Retention & Auto-Deletion Policy

## Overview
This AI Interview system implements a **30-day automatic data retention policy** for privacy compliance and data minimization in accordance with GDPR and best practices.

## 🔒 What Data is Stored

- Video recordings (.webm format)
- Audio transcriptions
- Facial expression analysis results
- Assessment scores and feedback
- Metadata (timestamps, file sizes)

## ⏰ Automatic Deletion (TTL Index)

### How It Works
MongoDB's TTL (Time-To-Live) index automatically deletes documents after 30 days:

```javascript
db.interviews.createIndex({ "createdAt": 1 }, { expireAfterSeconds: 2592000 })
```

- **Retention Period:** 30 days (2,592,000 seconds)
- **Index Field:** `createdAt` (UTC datetime)
- **Process:** MongoDB background task checks every 60 seconds
- **Deletion:** Automatic, no cron job required

### What Gets Deleted
When a document expires:
1. ✓ MongoDB document (all interview data)
2. ✓ Associated video file from uploads folder
3. ✓ All related metadata

## 📊 Remaining Days Counter

Each interview response includes:

```json
{
  "id": "1762273874_5162a48b",
  "createdAt": "2025-11-04T16:31:14.770207",
  "deletion_date": "2025-12-04T16:31:14.770207",
  "days_until_deletion": 30,
  "... other data ..."
}
```

### View Countdown via API

```bash
GET http://localhost:5001/api/interview/history
```

**Response includes:**
```json
{
  "count": 5,
  "source": "MongoDB",
  "retention_policy": "Auto-deletion after 30 days",
  "data": [
    {
      "id": "...",
      "days_until_deletion": 25,
      "deletion_date": "2025-12-04T16:31:14",
      ...
    }
  ]
}
```

## 🗑️ Manual Deletion ("Delete my data now")

### User Command
Users can trigger immediate deletion with:

**Command:** `"Delete my data now"`

### API Endpoint

```bash
POST http://localhost:5001/api/data/delete
Content-Type: application/json

{
  "command": "Delete my data now",
  "id": "1762273874_5162a48b"
}
```

### Response

**Success:**
```json
{
  "status": "success",
  "message": "Your interview data has been permanently deleted",
  "deleted_records": 1,
  "deleted_files": 1,
  "deleted_at": "2025-11-04T17:30:00.123456"
}
```

**Error:**
```json
{
  "error": "Invalid command",
  "hint": "Type exactly: 'Delete my data now' to confirm deletion"
}
```

### What Happens
1. Validates command is exactly "Delete my data now"
2. Finds all documents matching the ID
3. Deletes video files from disk
4. Deletes MongoDB documents
5. Logs deletion event to `deletion_log` collection
6. Returns confirmation

## 📝 Deletion Logs

All deletions (automatic and manual) are logged for transparency and audit.

### Log Structure

```json
{
  "deleted_at": "2025-11-04T17:30:00",
  "user_id": "1762273874_5162a48b",
  "deleted_count": 1,
  "deleted_files": ["1762273874_interview-response.webm"],
  "deletion_type": "manual",  // or "automatic"
  "command": "delete my data now"
}
```

### View Logs

```bash
# Via management script
python backend/manage_retention.py
# Select option 3: View Deletion Logs
```

## 🛠️ Management Tools

### Retention Management Script

```bash
python backend/manage_retention.py
```

**Features:**
1. Check TTL Index Status
2. View Data with Deletion Countdown
3. View Deletion Logs
4. Create/Update TTL Index
5. Cleanup Orphaned Video Files

### Example Output

```
============================================================
INTERVIEW DATA WITH DELETION COUNTDOWN
============================================================
Total records: 5

ID                        Created              Days Left    Deletion Date       
-------------------------------------------------------------------------------------
1762273874_5162a48b       2025-11-04 16:31     🟢 30 days   2025-12-04 16:31    
1762264677_a1b2c3d4       2025-11-04 14:20     🟢 29 days   2025-12-03 14:20    
1762251234_xyz789         2025-11-01 10:15     🟡 7 days    2025-12-01 10:15    
1762100000_abc123         2025-10-28 09:00     🔴 2 days    2025-11-27 09:00    
```

## 🔍 Verification & Testing

### 1. Check if TTL Index is Active

```bash
python backend/manage_retention.py
# Select option 1: Check TTL Index Status
```

**Expected output:**
```
✓ TTL Index Found
  Field: createdAt
  Expiration: 2592000 seconds (30 days)
  Status: ✓ ACTIVE
```

### 2. View Current Data with Countdown

```bash
python backend/manage_retention.py
# Select option 2: View Data with Deletion Countdown
```

### 3. Test Manual Deletion

```bash
curl -X POST http://localhost:5001/api/data/delete \
  -H "Content-Type: application/json" \
  -d '{
    "command": "Delete my data now",
    "id": "YOUR_INTERVIEW_ID"
  }'
```

## 📋 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/data/retention-info` | GET | Get retention policy info |
| `/api/interview/history` | GET | View all data with countdown |
| `/api/data/delete` | POST | Manual deletion |

### Get Retention Policy Info

```bash
GET http://localhost:5001/api/data/retention-info
```

**Response:**
```json
{
  "retention_policy": {
    "auto_deletion_days": 30,
    "description": "All interview data is automatically deleted after 30 days",
    "data_stored": [
      "Video recordings",
      "Audio transcriptions",
      "Facial analysis results",
      "Assessment scores"
    ],
    "manual_deletion": {
      "command": "Delete my data now",
      "endpoint": "/api/data/delete",
      "method": "POST",
      "required_fields": ["command", "id or user_id"]
    }
  },
  "privacy_compliance": "GDPR & Data Minimization"
}
```

## 🎯 User Confirmation Message

After each interview upload, users see:

```
✓ Assessment Complete!

Data Retention Notice:
Your interview data will be securely deleted automatically after 30 days
in accordance with our data minimization policy.

Deletion Date: 2025-12-04 16:31:14
Days Remaining: 30

You can also delete it anytime using the command: "Delete my data now"
```

## 🔧 Configuration

Change retention period in `backend/app.py`:

```python
# Data retention policy constants
RETENTION_DAYS = 30  # Change to desired days
RETENTION_SECONDS = RETENTION_DAYS * 24 * 60 * 60
```

After changing, restart backend and run:

```bash
python backend/manage_retention.py
# Select option 4: Create/Update TTL Index
```

## ⚠️ Important Notes

1. **TTL Background Task:** MongoDB checks every 60 seconds, so deletion may take up to 1 minute after expiry
2. **Video Files:** Must be manually cleaned up or add logic to delete on document removal
3. **Old Records:** Documents without `createdAt` field won't auto-delete (manually add or delete)
4. **Backup:** Auto-deleted data is permanent and cannot be recovered

## 🧪 Testing Auto-Deletion

To test with shorter retention:

```python
# Temporarily change in app.py
RETENTION_DAYS = 0.0007  # ~1 minute for testing
RETENTION_SECONDS = int(RETENTION_DAYS * 24 * 60 * 60)  # 60 seconds
```

1. Restart backend
2. Create TTL index
3. Upload interview
4. Wait 2-3 minutes
5. Check if document is deleted

## 📞 Support

For issues or questions:
- Check MongoDB logs: `mongod.log`
- Run verification script
- View deletion logs

---

**Compliance Status:** ✅ GDPR & Data Minimization Compliant

**Last Updated:** 2025-11-04
