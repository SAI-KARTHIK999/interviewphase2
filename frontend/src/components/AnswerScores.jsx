/**
 * AnswerScores Component
 * Displays quality_score and component scores with visual bars and explanations.
 */

import React, { useState } from 'react';
import './AnswerScores.css';

const AnswerScores = ({ analysisData }) => {
  const [activeTooltip, setActiveTooltip] = useState(null);

  if (!analysisData) {
    return (
      <div className="answer-scores-container">
        <p className="no-data">No analysis data available</p>
      </div>
    );
  }

  const {
    quality_score,
    clarity,
    correctness,
    relevance,
    tone_score,
    stt_confidence,
    components,
    model_version,
    created_at
  } = analysisData;

  // Score color mapping
  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981'; // green
    if (score >= 60) return '#3b82f6'; // blue
    if (score >= 40) return '#f59e0b'; // orange
    return '#ef4444'; // red
  };

  // Score label
  const getScoreLabel = (score) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Needs Improvement';
  };

  const componentScores = [
    {
      name: 'Clarity',
      score: clarity,
      explanation: components?.clarity_explanation || 'Measures how clearly the answer is communicated',
      icon: '💬'
    },
    {
      name: 'Correctness',
      score: correctness,
      explanation: components?.correctness_explanation || 'Evaluates factual accuracy and completeness',
      icon: '✓'
    },
    {
      name: 'Relevance',
      score: relevance,
      explanation: components?.relevance_explanation || 'Assesses how well the answer addresses the question',
      icon: '🎯'
    },
    {
      name: 'Tone',
      score: tone_score,
      explanation: components?.tone_label ? `Tone detected: ${components.tone_label}` : 'Analyzes speaking confidence and engagement',
      icon: '🎤'
    }
  ];

  return (
    <div className="answer-scores-container">
      {/* Overall Quality Score */}
      <div className="quality-score-section">
        <div className="quality-score-header">
          <h2>Overall Quality Score</h2>
          <a
            href="/scoring-info"
            className="info-link"
            title="Learn about scoring"
            target="_blank"
            rel="noopener noreferrer"
          >
            <span className="info-icon">ℹ️</span>
          </a>
        </div>

        <div className="quality-score-display">
          <div className="score-circle" style={{ borderColor: getScoreColor(quality_score) }}>
            <div className="score-value">{quality_score.toFixed(1)}</div>
            <div className="score-max">/100</div>
          </div>
          <div className="score-label" style={{ color: getScoreColor(quality_score) }}>
            {getScoreLabel(quality_score)}
          </div>
        </div>

        {stt_confidence !== undefined && (
          <div className="stt-confidence">
            <span className="stt-label">Transcription Confidence:</span>
            <span className="stt-value">{(stt_confidence * 100).toFixed(0)}%</span>
          </div>
        )}
      </div>

      {/* Component Scores */}
      <div className="component-scores-section">
        <h3>Score Breakdown</h3>

        {componentScores.map((component, index) => (
          <div key={index} className="score-component">
            <div className="component-header">
              <span className="component-icon">{component.icon}</span>
              <span className="component-name">{component.name}</span>
              <span className="component-value">{component.score.toFixed(0)}</span>
              <button
                className="tooltip-trigger"
                onMouseEnter={() => setActiveTooltip(index)}
                onMouseLeave={() => setActiveTooltip(null)}
                aria-label={`Show explanation for ${component.name}`}
              >
                ?
              </button>
            </div>

            {/* Progress Bar */}
            <div className="score-bar-container">
              <div
                className="score-bar-fill"
                style={{
                  width: `${component.score}%`,
                  backgroundColor: getScoreColor(component.score)
                }}
              />
            </div>

            {/* Tooltip */}
            {activeTooltip === index && (
              <div className="score-tooltip">
                {component.explanation}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Metadata */}
      <div className="analysis-metadata">
        {model_version && (
          <span className="metadata-item">Model: {model_version}</span>
        )}
        {created_at && (
          <span className="metadata-item">
            Analyzed: {new Date(created_at).toLocaleString()}
          </span>
        )}
      </div>
    </div>
  );
};

export default AnswerScores;
