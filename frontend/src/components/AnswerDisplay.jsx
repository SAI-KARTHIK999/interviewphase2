/**
 * AnswerDisplay Component
 * Displays both original transcript and tokenized format from MongoDB
 */

import React, { useState } from 'react';
import AnswerScores from './AnswerScores';
import './AnswerDisplay.css';

const AnswerDisplay = ({ answer }) => {
  const [showTokens, setShowTokens] = useState(true);

  if (!answer) {
    return (
      <div className="answer-display-container">
        <p className="no-answer">No answer data available</p>
      </div>
    );
  }

  return (
    <div className="answer-display-container">
      {/* Original Spoken Text Section */}
      <div className="original-text-section">
        <div className="section-header">
          <h3>📝 Original Transcript</h3>
          {answer.stt_confidence !== undefined && (
            <span className="confidence-badge">
              Confidence: {(answer.stt_confidence * 100).toFixed(0)}%
            </span>
          )}
        </div>
        
        <div className="original-text-box">
          <p className="original-text">
            {answer.original_text || answer.cleaned_text || 'No transcript available'}
          </p>
        </div>

        {answer.created_at && (
          <div className="timestamp">
            <span className="timestamp-icon">🕐</span>
            {new Date(answer.created_at).toLocaleString()}
          </div>
        )}
      </div>

      {/* Tokenized Format Section */}
      {answer.tokens && answer.tokens.length > 0 && (
        <div className="tokens-section">
          <div className="section-header">
            <h3>🔤 Tokenized Format</h3>
            <div className="tokens-controls">
              <span className="token-count-badge">
                {answer.token_count || answer.tokens.length} tokens
              </span>
              <button
                className="toggle-tokens-btn"
                onClick={() => setShowTokens(!showTokens)}
                aria-label={showTokens ? 'Hide tokens' : 'Show tokens'}
              >
                {showTokens ? '▼ Hide' : '▶ Show'}
              </button>
            </div>
          </div>

          {showTokens && (
            <div className="tokens-grid">
              {answer.tokens.map((token, idx) => (
                <span key={idx} className="token-badge" title={`Token ${idx + 1}`}>
                  {token}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Quality Scores Section */}
      {answer.quality_score !== undefined && (
        <div className="scores-section">
          <AnswerScores analysisData={answer} />
        </div>
      )}

      {/* Embedding Info */}
      {answer.embedding_present && (
        <div className="embedding-info">
          <span className="embedding-badge">
            ✓ Vector embedding generated ({answer.embedding?.length || 384} dimensions)
          </span>
        </div>
      )}
    </div>
  );
};

export default AnswerDisplay;
