import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const Home = ({ user }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [statsVisible, setStatsVisible] = useState(false);
  
  useEffect(() => {
    const timer1 = setTimeout(() => setIsVisible(true), 100);
    const timer2 = setTimeout(() => setStatsVisible(true), 600);
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, []);

  const features = [
    {
      icon: '🎯',
      title: 'Smart Analysis',
      description: 'Our AI analyzes your verbal responses, body language, and communication patterns to provide comprehensive feedback.'
    },
    {
      icon: '🔒',
      title: 'Privacy First',
      description: 'Your data is automatically anonymized and processed securely. We prioritize your privacy above all else.'
    },
    {
      icon: '📈',
      title: 'Real-time Feedback',
      description: 'Get instant, actionable feedback on your performance with detailed scoring and improvement suggestions.'
    },
    {
      icon: '🎪',
      title: 'Realistic Simulation',
      description: 'Experience authentic interview scenarios that prepare you for real-world situations.'
    }
  ];

  const stats = [
    { label: 'Interviews Conducted', value: '10K+' },
    { label: 'Success Rate', value: '94%' },
    { label: 'Average Score Improvement', value: '87%' }
  ];

  return (
    <div className="home-container">
      {/* Hero Section */}
      <div className={`hero-section ${isVisible ? 'fade-in' : ''}`}>
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-icon">🚀</span>
            <span>AI-Powered Interview Practice</span>
          </div>
          <div className="welcome-message">
            <h1 className="hero-title">
              Welcome back, 
              <span className="highlight-text">{user?.name || user?.firstName || 'User'}!</span>
            </h1>
            <p className="user-greeting">
              Ready to continue your interview preparation journey?
            </p>
          </div>
          <h2 className="hero-subtitle-main">
            Master Your Next Interview
          </h2>
          <p className="hero-subtitle">
            Practice with our advanced AI interview bot that provides real-time feedback,
            analyzes your performance, and helps you build confidence—all while keeping your data completely private.
          </p>
          <div className="hero-actions">
            <Link to="/interview" className="cta-button primary">
              <span>Start Interview</span>
              <span className="button-icon">→</span>
            </Link>
            <Link to="/practice" className="cta-button secondary">
              <span>Practice Mode</span>
            </Link>
          </div>
        </div>
        <div className="hero-visual">
          <div className="floating-card">
            <div className="mock-interview">
              <div className="interview-header">
                <div className="status-indicator"></div>
                <span>Live Interview Session</span>
              </div>
              <div className="interview-content">
                <div className="question-bubble">
                  "Tell me about a challenging project..."
                </div>
                <div className="progress-bar">
                  <div className="progress-fill"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className={`stats-section ${statsVisible ? 'slide-up' : ''}`}>
        <div className="stats-grid">
          {stats.map((stat, index) => (
            <div key={index} className="stat-card" style={{ animationDelay: `${index * 100}ms` }}>
              <div className="stat-value">{stat.value}</div>
              <div className="stat-label">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Features Section */}
      <div className="features-section">
        <div className="section-header">
          <h2>Why Choose Our AI Interview Bot?</h2>
          <p>Cutting-edge technology meets personalized learning</p>
        </div>
        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card" data-index={index}>
              <div className="feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="cta-section">
        <div className="cta-content">
          <h2>Ready to Ace Your Next Interview?</h2>
          <p>Join thousands of successful candidates who improved their interview skills with our AI bot</p>
          <div className="cta-actions">
            <Link to="/interview" className="cta-button primary large">
              Get Started Now
            </Link>
            <Link to="/profile" className="cta-button ghost large">
              View Profile
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
