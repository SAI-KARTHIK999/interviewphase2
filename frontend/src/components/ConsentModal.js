import React, { useState } from 'react';
import './ConsentModal.css';

function ConsentModal({ onConsentSubmit, onClose }) {
  const [selectedOption, setSelectedOption] = useState(null);
  const [showPrivacyPolicy, setShowPrivacyPolicy] = useState(false);

  const consentOptions = [
    {
      id: 'allow_save',
      title: '✅ Allow Recording and Save Data',
      description: 'Record my interview with audio and video. Save my data for future review and personalized feedback.',
      details: [
        'Voice and video will be recorded',
        'Your responses will be stored in our database',
        'Data will be auto-deleted after 30 days',
        'You can request deletion anytime'
      ],
      permissions: {
        allow_audio: true,
        allow_video: true,
        allow_storage: true,
        session_mode: 'record'
      }
    },
    {
      id: 'allow_no_save',
      title: '🔒 Allow Recording but Don\'t Save',
      description: 'Record my interview but delete all data immediately after analysis. Experience the full interview without permanent storage.',
      details: [
        'Voice and video will be recorded temporarily',
        'Analysis will be performed in real-time',
        'All data deleted immediately after session',
        'No permanent record will be kept'
      ],
      permissions: {
        allow_audio: true,
        allow_video: true,
        allow_storage: false,
        session_mode: 'record'
      }
    },
    {
      id: 'decline',
      title: '🚫 Decline Recording',
      description: 'Practice without recording. Switch to text-only mode with no audio or video capture.',
      details: [
        'No audio or video recording',
        'Text-based interaction only',
        'Practice mode - no analysis performed',
        'Completely anonymous session'
      ],
      permissions: {
        allow_audio: false,
        allow_video: false,
        allow_storage: false,
        session_mode: 'practice'
      }
    }
  ];

  const handleSubmit = () => {
    if (!selectedOption) {
      alert('Please select a consent option to continue.');
      return;
    }

    const option = consentOptions.find(opt => opt.id === selectedOption);
    onConsentSubmit(option.permissions);
  };

  return (
    <div className="consent-modal-overlay">
      <div className="consent-modal">
        <div className="consent-modal-header">
          <h2>🔐 Privacy & Consent</h2>
          <p className="consent-intro">
            Your privacy matters to us. Before we begin, please choose how you'd like to participate in this interview session.
          </p>
        </div>

        <div className="consent-data-info">
          <h3>What data do we collect?</h3>
          <div className="data-items">
            <span className="data-item">🎤 Your voice (audio)</span>
            <span className="data-item">📹 Your video</span>
            <span className="data-item">💬 Your textual answers</span>
          </div>
          <p className="data-purpose">
            We use this data <strong>only</strong> to evaluate your interview performance and provide feedback.
          </p>
        </div>

        <div className="consent-options-container">
          {consentOptions.map(option => (
            <div 
              key={option.id}
              className={`consent-option ${selectedOption === option.id ? 'selected' : ''}`}
              onClick={() => setSelectedOption(option.id)}
            >
              <div className="consent-option-header">
                <input 
                  type="radio" 
                  name="consent" 
                  value={option.id}
                  checked={selectedOption === option.id}
                  onChange={() => setSelectedOption(option.id)}
                />
                <h3>{option.title}</h3>
              </div>
              <p className="consent-option-description">{option.description}</p>
              <ul className="consent-option-details">
                {option.details.map((detail, idx) => (
                  <li key={idx}>{detail}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {showPrivacyPolicy && (
          <div className="privacy-policy-section">
            <h3>Privacy Policy Summary</h3>
            <div className="privacy-content">
              <h4>Data Collection</h4>
              <p>We collect only essential data: your voice, video, and interview answers.</p>
              
              <h4>Data Usage</h4>
              <p>Your data is used exclusively for interview performance assessment and providing personalized feedback.</p>
              
              <h4>Data Storage</h4>
              <p>If you choose to save data, it's stored securely in our database with encryption. All data is automatically deleted after 30 days.</p>
              
              <h4>Your Rights</h4>
              <ul>
                <li>Right to access your data</li>
                <li>Right to delete your data anytime</li>
                <li>Right to opt-out of data storage</li>
                <li>Right to transparent information about data usage</li>
              </ul>
              
              <h4>Data Deletion</h4>
              <p>You can request immediate deletion by sending the command "Delete my data now" with your session ID to our API.</p>
              
              <h4>Compliance</h4>
              <p>We follow GDPR principles and data minimization standards.</p>
            </div>
            <button 
              className="close-privacy-btn"
              onClick={() => setShowPrivacyPolicy(false)}
            >
              Close
            </button>
          </div>
        )}

        <div className="consent-modal-footer">
          <button 
            className="link-button"
            onClick={() => setShowPrivacyPolicy(!showPrivacyPolicy)}
          >
            {showPrivacyPolicy ? 'Hide' : 'View'} Full Privacy Policy
          </button>
          
          <div className="consent-actions">
            <button 
              className="button button-secondary"
              onClick={onClose}
            >
              Cancel
            </button>
            <button 
              className="button button-primary"
              onClick={handleSubmit}
              disabled={!selectedOption}
            >
              Continue with Selected Option
            </button>
          </div>
        </div>

        <div className="consent-transparency">
          <p>
            <strong>Transparency Promise:</strong> We will never use your data for purposes other than interview assessment. 
            Your consent is stored and can be reviewed at any time.
          </p>
        </div>
      </div>
    </div>
  );
}

export default ConsentModal;
