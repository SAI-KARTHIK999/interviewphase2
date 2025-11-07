import React, { useState, useEffect } from 'react';
import InterviewResponseDisplay from '../components/InterviewResponseDisplay';
import './AdminReview.css';

/**
 * Admin/Review page to view all interview responses
 * Shows both transcribed_text (raw STT) and anonymized_answer (tokenized)
 * for transparency and debugging during AI assessment
 */
const AdminReview = () => {
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, high-score, low-score
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchInterviewHistory();
  }, []);

  const fetchInterviewHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5001/api/interview/history');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setResponses(data.data || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch interview history:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Filter responses based on score
  const getFilteredResponses = () => {
    let filtered = responses;

    // Apply score filter
    if (filter === 'high-score') {
      filtered = filtered.filter(r => (r.score || 0) >= 70);
    } else if (filter === 'low-score') {
      filtered = filtered.filter(r => (r.score || 0) < 70);
    }

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(r => 
        (r.transcribed_text?.toLowerCase().includes(query)) ||
        (r.anonymized_answer?.toLowerCase().includes(query)) ||
        (r.id?.toLowerCase().includes(query)) ||
        (r.user_id?.toLowerCase().includes(query))
      );
    }

    return filtered;
  };

  const filteredResponses = getFilteredResponses();

  if (loading) {
    return (
      <div className="admin-review-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading interview responses...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-review-page">
        <div className="error-container">
          <h2>❌ Error Loading Data</h2>
          <p>{error}</p>
          <button onClick={fetchInterviewHistory} className="retry-button">
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-review-page">
      {/* Header */}
      <div className="admin-header">
        <div className="header-content">
          <h1>🔍 Interview Response Review</h1>
          <p className="header-subtitle">
            Admin view showing both raw transcriptions and anonymized versions
          </p>
        </div>
        <button onClick={fetchInterviewHistory} className="refresh-button">
          🔄 Refresh
        </button>
      </div>

      {/* Statistics Panel */}
      <div className="stats-panel">
        <div className="stat-card">
          <div className="stat-value">{responses.length}</div>
          <div className="stat-label">Total Responses</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {responses.filter(r => r.transcribed_text).length}
          </div>
          <div className="stat-label">With Transcription</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {responses.filter(r => r.anonymized_answer).length}
          </div>
          <div className="stat-label">With Anonymization</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {responses.length > 0 
              ? Math.round(responses.reduce((sum, r) => sum + (r.score || 0), 0) / responses.length)
              : 0}%
          </div>
          <div className="stat-label">Avg Score</div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="controls-panel">
        <div className="filter-buttons">
          <button 
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            📊 All ({responses.length})
          </button>
          <button 
            className={`filter-btn ${filter === 'high-score' ? 'active' : ''}`}
            onClick={() => setFilter('high-score')}
          >
            ⭐ High Score ({responses.filter(r => (r.score || 0) >= 70).length})
          </button>
          <button 
            className={`filter-btn ${filter === 'low-score' ? 'active' : ''}`}
            onClick={() => setFilter('low-score')}
          >
            📉 Low Score ({responses.filter(r => (r.score || 0) < 70).length})
          </button>
        </div>

        <div className="search-box">
          <input 
            type="text"
            placeholder="🔍 Search by text, ID, or user..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          {searchQuery && (
            <button 
              onClick={() => setSearchQuery('')}
              className="clear-search"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Results Count */}
      <div className="results-info">
        <p>
          Showing {filteredResponses.length} of {responses.length} responses
          {searchQuery && ` matching "${searchQuery}"`}
        </p>
      </div>

      {/* Response List */}
      <div className="responses-container">
        {filteredResponses.length === 0 ? (
          <div className="no-responses">
            <h3>📭 No Responses Found</h3>
            <p>
              {searchQuery 
                ? 'Try adjusting your search or filters'
                : 'No interview responses have been recorded yet'}
            </p>
          </div>
        ) : (
          filteredResponses.map((response, index) => (
            <InterviewResponseDisplay 
              key={response.id || response._id || index} 
              response={response} 
            />
          ))
        )}
      </div>

      {/* Data Notice */}
      <div className="data-notice">
        <div className="notice-icon">🔒</div>
        <div className="notice-content">
          <h4>Privacy & Data Transparency</h4>
          <p>
            This admin view shows both the original transcribed speech and the anonymized version 
            used for AI analysis. All data is automatically deleted after 30 days per the retention policy.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdminReview;
