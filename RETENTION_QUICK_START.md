# Data Retention System - Quick Start

## ✅ System Status

**TTL Index:** ✓ ACTIVE  
**Retention Period:** 30 days  
**Auto-Deletion:** Enabled

## 🚀 Quick Commands

### 1. Check System Status
```powershell
python backend/manage_retention.py
# Select option 1: Check TTL Index Status
```

### 2. View Data with Countdown
```powershell
python backend/manage_retention.py
# Select option 2: View Data with Deletion Countdown
```

### 3. Test Manual Deletion

**Via API:**
```powershell
curl -X POST http://localhost:5001/api/data/delete `
  -H "Content-Type: application/json" `
  -d '{\"command\": \"Delete my data now\", \"id\": \"YOUR_ID\"}'
```

**Via PowerShell:**
```powershell
$body = @{
    command = "Delete my data now"
    id = "1762273874_5162a48b"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5001/api/data/delete" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

### 4. Get Retention Policy Info
```powershell
curl http://localhost:5001/api/data/retention-info
```

### 5. View Interview History with Countdown
```powershell
curl http://localhost:5001/api/interview/history
```

## 📊 Response Structure

### After Uploading Interview:
```json
{
  "assessment": {
    "score": 0.75,
    "feedback": "Good answer..."
  },
  "storage": {
    "saved": true,
    "method": "MongoDB",
    "id": "1762273874_5162a48b"
  },
  "data_retention": {
    "auto_deletion_days": 30,
    "deletion_date": "2025-12-04T16:31:14.770207",
    "message": "Your data will be automatically deleted after 30 days. Type 'Delete my data now' to delete immediately."
  }
}
```

### Interview History with Countdown:
```json
{
  "count": 5,
  "source": "MongoDB",
  "retention_policy": "Auto-deletion after 30 days",
  "data": [
    {
      "id": "1762273874_5162a48b",
      "days_until_deletion": 25,
      "deletion_date": "2025-12-04T16:31:14",
      "createdAt": "2025-11-04T16:31:14",
      ...
    }
  ]
}
```

## 🎨 Visual Countdown Indicators

When viewing data with the management script:

- 🟢 **Green (30-8 days):** Data is fresh
- 🟡 **Yellow (7-4 days):** Warning - deletion soon
- 🔴 **Red (3-0 days):** Urgent - deleting very soon
- ⚠️ **Expired:** Should be deleted (MongoDB checks every 60s)

## 🔧 Restart Backend

After making changes, restart:

```powershell
# Stop existing processes
Get-Process python | Where-Object {$_.Path -like "*saika*"} | Stop-Process -Force

# Start backend
python backend/app.py
```

## 📝 New Files Created

```
ai_interview/
├── backend/
│   ├── app.py                          # Enhanced with retention
│   ├── manage_retention.py             # NEW: Management tool
│   └── data/
│       └── deletion_log.json           # NEW: Deletion logs
├── DATA_RETENTION_POLICY.md            # NEW: Full documentation
└── RETENTION_QUICK_START.md            # NEW: This file
```

## ✨ Features Implemented

- ✅ TTL index for automatic 30-day deletion
- ✅ `createdAt` field on all new records
- ✅ Days until deletion counter
- ✅ Manual deletion endpoint
- ✅ Deletion logging (MongoDB collection)
- ✅ Video file cleanup on deletion
- ✅ Retention policy API endpoint
- ✅ Management script with 5 tools
- ✅ Full documentation

## 🎯 User Message

Users now see after every interview:

```
✓ Your interview has been saved!

Data Retention Notice:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your interview data will be automatically deleted 
after 30 days in accordance with our data 
minimization policy.

Deletion Date: December 4, 2025
Days Remaining: 30

You can delete it anytime by typing:
"Delete my data now"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🛡️ Privacy Compliance

✅ GDPR Compliant  
✅ Data Minimization  
✅ Right to Deletion  
✅ Transparency (deletion logs)  
✅ Automated cleanup

---

**Ready to use!** 🎉
