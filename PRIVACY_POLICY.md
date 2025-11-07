# Privacy Policy - AI Interview Bot

**Last Updated:** November 6, 2025  
**Effective Date:** November 6, 2025

## Introduction

At AI Interview Bot, we are committed to protecting your privacy and ensuring transparency in how we collect, use, and protect your personal data. This Privacy Policy explains our data practices in clear, understandable terms.

## Our Privacy Commitment

We believe in **privacy by design** and **data minimization**. We only collect what is absolutely necessary to provide you with interview assessment services, and we give you full control over your data.

## What Data We Collect

We collect only **essential data** required for interview assessment:

### Core Data Types
1. **Voice Data** - Audio recordings from your interview responses
2. **Video Data** - Video recordings showing your presentation during the interview
3. **Textual Answers** - Transcriptions and text-based responses to interview questions

### Metadata
- Session timestamps
- Consent preferences and settings
- IP address (for security purposes only)
- User agent information

## How We Use Your Data

Your data is used **exclusively** for the following purposes:

### Primary Use
- **Performance Assessment**: Analyzing your interview responses to provide feedback
- **Transcription**: Converting audio to text for analysis
- **Behavioral Analysis**: Evaluating communication patterns and presentation skills
- **Feedback Generation**: Creating personalized improvement recommendations

### What We DON'T Do
- ❌ We **never** sell your data to third parties
- ❌ We **never** use your data for advertising
- ❌ We **never** share your data without explicit consent
- ❌ We **never** train AI models on your data without permission

## Your Consent Choices

Before each interview session, you have three clear options:

### Option 1: Allow Recording and Save Data
- Your audio, video, and responses are recorded
- Data is stored securely in our database
- You can access your data for review and improvement
- **Auto-deletion:** All data is automatically deleted after **30 days**
- You can manually delete your data at any time

### Option 2: Allow Recording but Don't Save
- Your audio, video, and responses are recorded temporarily
- Analysis is performed in real-time
- **All data is immediately deleted** after the session ends
- No permanent records are kept in our database
- Perfect for practicing without leaving a digital footprint

### Option 3: Decline Recording (Practice Mode)
- No audio or video recording occurs
- Text-based interaction only
- No data is collected or stored
- Completely anonymous session
- Ideal for getting familiar with the interview format

## Data Storage and Security

### Storage Duration
- **With Save Consent**: 30 days (automatic deletion via TTL index)
- **Without Save Consent**: Immediate deletion after analysis
- **Practice Mode**: No storage - zero data collection

### Security Measures
- 🔒 Encrypted data transmission (HTTPS)
- 🔒 Secure MongoDB database with access controls
- 🔒 Server-side processing only (no client-side data persistence)
- 🔒 Regular security audits and updates
- 🔒 Minimal data exposure principle

### Data Anonymization
- All stored transcriptions are anonymized
- Personal identifiable information (PII) is automatically removed
- Only assessment-relevant information is retained

## Your Rights

You have complete control over your data:

### Right to Access
- View all data we have stored about you
- Access your interview history and feedback
- Review consent logs and preferences

### Right to Deletion
- Delete your data at any time using the command: **"Delete my data now"**
- Immediate removal from our database
- Permanent deletion of associated video files
- Confirmation of successful deletion

### Right to Opt-Out
- Choose not to save data before each session
- Switch between consent modes anytime
- No penalties for opting out of data storage

### Right to Portability
- Request a copy of your data
- Export your interview history
- Machine-readable format available

### Right to Be Informed
- Clear explanations of data practices
- Transparent consent process
- Real-time status updates on data handling

## Data Retention Policy

### Automatic Deletion
- All interview data expires **30 days** after creation
- MongoDB TTL (Time-To-Live) index ensures automatic cleanup
- No manual intervention required
- Countdown timer shows remaining days

### Manual Deletion
You can request immediate deletion:

1. Obtain your session ID from interview history
2. Send a POST request to `/api/data/delete` with:
   ```json
   {
     "command": "Delete my data now",
     "user_id": "your_session_id"
   }
   ```
3. Receive confirmation of permanent deletion

### What Gets Deleted
- Video recordings (files)
- Audio transcriptions
- Facial analysis results
- Assessment scores and feedback
- All metadata and session logs

## Compliance and Standards

We adhere to:

- **GDPR** (General Data Protection Regulation) principles
- **Data Minimization** standards
- **Privacy by Design** methodology
- **Transparency** requirements
- **User Consent** best practices

## Third-Party Services

We do **not** use third-party analytics, tracking, or advertising services. All data processing happens on our own servers.

### Technology Stack
- **Backend**: Python (Flask/FastAPI)
- **Frontend**: React (JSX)
- **Database**: MongoDB (local instance)
- **Storage**: Local file system (no cloud providers)

## Cookies and Tracking

- **No tracking cookies**: We don't track your behavior across websites
- **Session storage only**: Used for authentication during your session
- **Local storage**: Stores login state only (no sensitive data)

## Changes to This Policy

We may update this Privacy Policy to reflect:
- Changes in legal requirements
- Improvements to our privacy practices
- New features or services

**Notification**: We will notify users of significant changes via email or in-app notification.

## Contact and Data Protection Officer

For privacy-related questions, concerns, or requests:

**Email**: privacy@aiinterviewbot.com  
**Data Protection Officer**: [Contact information]  
**Response Time**: Within 72 hours

## Your Consent

By using AI Interview Bot, you acknowledge that:
- You have read and understood this Privacy Policy
- You consent to data collection only as you explicitly approve through the consent modal
- You can withdraw consent at any time
- You understand your rights regarding your data

## Summary: Your Data, Your Choice

✅ **Transparent**: You know exactly what data we collect  
✅ **Minimal**: We only collect what's necessary  
✅ **Temporary**: Automatic deletion after 30 days  
✅ **Secure**: Encrypted and protected  
✅ **Controllable**: You can delete data anytime  
✅ **Optional**: Choose not to save data at all  

---

**Privacy First, Always.**

*This policy reflects our commitment to ethical AI practices and user privacy protection.*
