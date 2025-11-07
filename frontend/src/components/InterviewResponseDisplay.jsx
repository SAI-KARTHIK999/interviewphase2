import React from 'react';
import './InterviewResponseDisplay.css';

/**
 * Component to display interview response with both raw transcript and anonymized version
 * Used in admin/review interfaces to show transparency in data processing
 */
const InterviewResponseDisplay = ({ response }) => {
  if (!response) {
    return null;
  }

  return (
    <div className="interview-response-display">
      {/* Response Header */}
      <div className="response-header">
        <div className="response-meta">
          <span className="response-id">ID: {response.id}</span>
          <span className="response-date">
            📅 {new Date(response.timestamp || response.createdAt).toLocaleDateString()}
          </span>
          <span className="response-score">
            ⭐ Score: {response.score || 0}%
          </span>
        </div>
      </div>

      {/* Question */}
      <div className="response-question">
        <h3>💬 Question</h3>
        <p>{response.question}</p>
      </div>

      {/* Transcribed Text (Raw STT Output) */}
      <div className="response-section transcribed">
        <div className="section-header">
          <h3>🎤 Transcribed Text (Raw Speech-to-Text)</h3>
          <span className="badge badge-original">Original</span>
        </div>
        <div className="section-content">
          {response.transcribed_text ? (
            <>
              <p className="response-text">{response.transcribed_text}</p>
              <div className="text-info">
                <span>📝 {response.transcribed_text.split(' ').length} words</span>
                <span>🔤 {response.transcribed_text.length} characters</span>
              </div>
            </>
          ) : (
            <p className="no-data">❌ No transcribed text available</p>
          )}
        </div>
      </div>

      {/* Anonymized Answer (Tokenized/Processed) */}
      <div className="response-section anonymized">
        <div className="section-header">
          <h3>🔒 Anonymized Answer (Tokenized/Processed)</h3>
          <span className="badge badge-anonymized">Privacy Protected</span>
        </div>
        <div className="section-content">
          {response.anonymized_answer ? (
            <>
              <p className="response-text">{response.anonymized_answer}</p>
              <div className="text-info">
                <span>📝 {response.anonymized_answer.split(' ').length} words</span>
                <span>🔤 {response.anonymized_answer.length} characters</span>
              </div>
            </>
          ) : (
            <p className="no-data">❌ No anonymized answer available</p>
          )}
        </div>
      </div>

      {/* Comparison Indicator */}
      {response.transcribed_text && response.anonymized_answer && (
        <div className="comparison-section">
          <div className="comparison-header">
            <h4>🔍 Data Processing Transparency</h4>
          </div>
          <div className="comparison-stats">
            <div className="stat-item">
              <span className="stat-label">Text Modified:</span>
              <span className="stat-value">
                {response.transcribed_text !== response.anonymized_answer ? '✅ Yes' : '❌ No'}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Word Count Change:</span>
              <span className="stat-value">
                {response.transcribed_text.split(' ').length} → {response.anonymized_answer.split(' ').length}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Privacy Status:</span>
              <span className="stat-value">🔒 Anonymized</span>
            </div>
          </div>
        </div>
      )}

      {/* Feedback Section */}
      {response.feedback && (
        <div className="response-feedback">
          <h3>💡 AI Feedback</h3>
          <p>{response.feedback}</p>
        </div>
      )}

      {/* Facial Analysis (if available) */}
      {response.facial_analysis && (
        <div className="response-facial-analysis">
          <h3>😊 Facial Analysis</h3>
          <pre>{JSON.stringify(response.facial_analysis, null, 2)}</pre>
        </div>
      )}

      {/* Data Retention Info */}
      {response.deletion_date && (
        <div className="retention-info">
          <span className="retention-icon">🗑️</span>
          <span>
            Auto-deletion in {response.days_until_deletion} days 
            ({new Date(response.deletion_date).toLocaleDateString()})
          </span>
        </div>
      )}
    </div>
  );
};

export default InterviewResponseDisplay;
