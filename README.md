# AI Interview Bot - Privacy-First Edition

An ethical, privacy-focused AI-powered interview assessment platform with comprehensive user consent management.

## 🌟 Key Features

- **🔒 Privacy-First Consent System**: Three clear consent options before every session
- **🎤 AI-Powered Assessment**: Voice, video, and text analysis for interview performance
- **⏱️ Auto-Deletion**: 30-day data retention with automatic cleanup
- **🚫 Practice Mode**: Zero data collection option for anonymous practice
- **✅ GDPR Compliant**: Transparent data handling with full user control
- **📊 Real-time Feedback**: Instant interview analysis and scoring

## 🔐 Privacy & Consent Features

### Three Consent Options

1. **✅ Allow Recording and Save Data**
   - Full interview recording with audio and video
   - Data stored securely for 30 days
   - Personalized feedback available
   - Automatic deletion after retention period

2. **🔒 Allow Recording but Don't Save**
   - Temporary recording for real-time analysis
   - Immediate data deletion after session
   - No permanent storage
   - Perfect for practice without digital footprint

3. **🚫 Decline Recording (Practice Mode)**
   - Text-only interaction
   - Zero audio/video recording
   - Completely anonymous
   - No data collection whatsoever

### User Rights
- **Right to Access**: View your consent history and interview data
- **Right to Deletion**: Manually delete your data anytime
- **Right to Opt-Out**: Choose not to save data before each session
- **Right to Be Informed**: Clear explanations at every step

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Get up and running in 5 minutes
- **[CONSENT_IMPLEMENTATION_GUIDE.md](CONSENT_IMPLEMENTATION_GUIDE.md)** - Complete technical documentation
- **[PRIVACY_POLICY.md](PRIVACY_POLICY.md)** - User-facing privacy policy
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Overview of consent system
- **[DATA_RETENTION_POLICY.md](DATA_RETENTION_POLICY.md)** - Data retention details
- **[STORAGE_GUIDE.md](STORAGE_GUIDE.md)** - Storage configuration

## 🚀 Quick Start

### Prerequisites
- Node.js v14+
- Python 3.8+
- MongoDB (local instance)

### Installation

```bash
# 1. Start MongoDB
net start MongoDB  # Windows

# 2. Install backend dependencies
cd backend
pip install flask flask-cors pymongo

# 3. Install frontend dependencies
cd ../frontend
npm install

# 4. Start the application
# Option A: Use provided scripts
python run_both.py

# Option B: Start manually (2 terminals)
# Terminal 1:
cd backend && python app.py

# Terminal 2:
cd frontend && npm start
```

The app will open at http://localhost:3000

## 🧪 Testing the Consent System

### Test 1: Full Recording with Save
1. Navigate to Interview page
2. Select "Allow Recording and Save Data"
3. Record a video response
4. Verify data is saved in MongoDB with 30-day TTL

### Test 2: Recording Without Save
1. Select "Allow Recording but Don't Save"
2. Record and submit
3. Verify video file is immediately deleted
4. Confirm no data in `interviews` collection

### Test 3: Practice Mode
1. Select "Decline Recording"
2. Use text-only interface
3. Verify zero data collection

See [QUICK_START.md](QUICK_START.md) for detailed testing instructions.

## 🏗️ Architecture

### Frontend
- **Framework**: React (JSX)
- **Key Components**:
  - `ConsentModal`: Privacy consent interface
  - `Interview`: Main interview page with conditional rendering
  - Practice Mode: Text-only UI

### Backend
- **Framework**: Flask (Python)
- **Key Endpoints**:
  - `POST /api/consent`: Logs user consent
  - `POST /api/interview/video`: Processes interviews with consent enforcement
  - `POST /api/data/delete`: Manual data deletion
  - `GET /api/data/retention-info`: Data retention policy info

### Database
- **System**: MongoDB (local)
- **Collections**:
  - `user_consent_logs`: All consent records with audit trail
  - `interviews`: Interview sessions with TTL (30-day auto-delete)
  - `deletion_log`: Tracks manual and automatic deletions

## 📊 Data Flow

```
User → ConsentModal
        ↓
POST /api/consent
        ↓
MongoDB: user_consent_logs
        ↓
Return: consent_id, session_mode
        ↓
Frontend: Render UI based on consent
        ↓
User records interview
        ↓
POST /api/interview/video (with consent_id)
        ↓
[If storage=true]      [If storage=false]
     ↓                      ↓
Save to MongoDB        Analyze & Delete
     ↓                      ↓
30-day TTL             Immediate cleanup
```

## 🔒 Security & Compliance

- **GDPR Compliant**: Explicit consent, granular control, data minimization
- **Transparent**: Clear explanations, embedded privacy policy
- **Accountable**: Audit logs for all consent and deletion actions
- **Secure**: Anonymization, encryption-ready, access controls
- **User-Centric**: Full control, easy opt-out, practice mode

## 📁 Project Structure

```
ai_interview/
├── backend/
│   ├── app.py                  # Flask API with consent endpoint
│   ├── nlp_processor.py        # AI analysis functions
│   ├── uploads/                # Temporary video storage
│   └── data/                   # JSON fallback storage
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ConsentModal.js # Privacy consent modal
│       │   └── ConsentModal.css
│       └── pages/
│           ├── Interview.js    # Main interview page
│           └── Practice.js     # Practice mode page
├── PRIVACY_POLICY.md           # User privacy policy
├── CONSENT_IMPLEMENTATION_GUIDE.md  # Technical docs
├── QUICK_START.md              # Getting started guide
└── README.md                   # This file
```

## 🛠️ API Reference

### POST /api/consent
Log user consent before interview session.

**Request:**
```json
{
  "user_id": "user@example.com",
  "allow_audio": true,
  "allow_video": true,
  "allow_storage": false,
  "session_mode": "record"
}
```

**Response:**
```json
{
  "status": "success",
  "consent_id": "consent_1731780000_a1b2",
  "session_mode": "record",
  "permissions": {
    "audio": true,
    "video": true,
    "storage": false
  }
}
```

### POST /api/interview/video
Submit interview video with consent enforcement.

### POST /api/data/delete
Manually delete user data.

**Request:**
```json
{
  "command": "Delete my data now",
  "user_id": "session_id_here"
}
```

See [CONSENT_IMPLEMENTATION_GUIDE.md](CONSENT_IMPLEMENTATION_GUIDE.md) for complete API documentation.

## 🐛 Troubleshooting

### ConsentModal doesn't appear
- Clear browser cache and localStorage
- Check browser console for errors
- Verify ConsentModal.js exists

### Cannot connect to MongoDB
```bash
# Check MongoDB status
mongo --eval "db.version()"

# Start MongoDB
net start MongoDB  # Windows
mongod             # Linux/Mac
```

### Video not deleting when "Don't Save" selected
- Check backend console for deletion log
- Verify `opt_in_data_save` is "false"
- Look for: "Deleted uploaded file immediately due to no-save consent"

See [QUICK_START.md](QUICK_START.md) for more troubleshooting.

## 📈 Production Deployment

Before deploying to production:

1. **Security**:
   - Enable HTTPS/SSL
   - Add MongoDB authentication
   - Implement rate limiting
   - Enable CORS whitelist

2. **Legal**:
   - Review privacy policy with legal team
   - Update contact information
   - Add data protection officer details

3. **Monitoring**:
   - Set up consent analytics
   - Monitor deletion effectiveness
   - Track TTL cleanup
   - Regular audit logs review

See [CONSENT_IMPLEMENTATION_GUIDE.md](CONSENT_IMPLEMENTATION_GUIDE.md) for production checklist.

## 🎓 Technologies Used

- **Frontend**: React, react-webcam, react-router-dom
- **Backend**: Flask, Flask-CORS, PyMongo
- **Database**: MongoDB with TTL indexes
- **AI/ML**: Whisper (transcription), NLP analysis
- **Storage**: Local filesystem with immediate cleanup

## 📝 License

This project demonstrates ethical AI development practices with privacy-first design.

## 🤝 Contributing

Contributions welcome! Please ensure:
- Privacy-first principles maintained
- Comprehensive testing
- Documentation updates
- GDPR compliance preserved

## 📞 Support

For questions or issues:
- Check documentation in project root
- Review [CONSENT_IMPLEMENTATION_GUIDE.md](CONSENT_IMPLEMENTATION_GUIDE.md)
- Examine backend console logs
- Check browser console for frontend issues

---

**Privacy First, Always.** 🔒

*This project sets a high standard for privacy-respecting AI applications.*
