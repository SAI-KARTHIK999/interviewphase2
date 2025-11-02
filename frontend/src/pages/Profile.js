import React, { useState, useEffect } from 'react';

const Profile = ({ user }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [activeSection, setActiveSection] = useState('overview');
  const [userStats] = useState({
    interviewsCompleted: user?.stats?.interviewsCompleted || 12,
    averageScore: user?.stats?.averageScore || 87,
    totalPracticeTime: user?.stats?.totalPracticeTime || '2h 34m',
    improvementRate: user?.stats?.improvementRate || '+23%',
    lastInterview: '2 days ago'
  });

  const [privacySettings, setPrivacySettings] = useState({
    dataSharing: false,
    analyticsTracking: true,
    personalizedFeedback: true,
    emailNotifications: false
  });

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handlePrivacyToggle = (setting) => {
    setPrivacySettings(prev => ({
      ...prev,
      [setting]: !prev[setting]
    }));
  };

  const achievements = [
    {
      title: "First Steps",
      description: "Completed your first interview",
      icon: "🥇",
      earned: true,
      date: "2 weeks ago"
    },
    {
      title: "Consistent Learner",
      description: "Practiced 5 days in a row",
      icon: "📚",
      earned: true,
      date: "1 week ago"
    },
    {
      title: "High Performer",
      description: "Scored above 80% in 5 interviews",
      icon: "⭐",
      earned: false,
      progress: "4/5"
    },
    {
      title: "Interview Master",
      description: "Complete 20 practice interviews",
      icon: "👑",
      earned: false,
      progress: "12/20"
    }
  ];

  const recentActivity = [
    {
      type: "interview",
      title: "Behavioral Interview Practice",
      score: 89,
      date: "2 days ago",
      icon: "🎯"
    },
    {
      type: "practice",
      title: "Technical Questions Review",
      duration: "15 min",
      date: "3 days ago",
      icon: "💻"
    },
    {
      type: "achievement",
      title: "Earned 'Consistent Learner' badge",
      date: "1 week ago",
      icon: "🏆"
    }
  ];

  return (
    <div className={`profile-container ${isVisible ? 'fade-in' : ''}`}>
      {/* Profile Header */}
      <div className="profile-header">
        <div className="profile-info">
          <div className="avatar">
            <span className="avatar-icon">{user?.avatar || '👤'}</span>
          </div>
          <div className="user-details">
            <h1>Hello, {user?.name || user?.firstName || 'User'}!</h1>
            <p className="user-subtitle">{user?.email || 'user@example.com'}</p>
            <div className="user-info">
              <span className="info-item">📅 Joined: {user?.joinDate || 'Recently'}</span>
              {user?.profession && <span className="info-item">💼 {user.profession}</span>}
              {user?.experience && <span className="info-item">⭐ {user.experience}</span>}
            </div>
            <div className="user-badges">
              <span className="badge premium">🎯 Active Learner</span>
              <span className="badge streak">🔥 7-day streak</span>
            </div>
          </div>
        </div>
        <div className="profile-stats">
          <div className="stat-card">
            <span className="stat-value">{userStats.averageScore}%</span>
            <span className="stat-label">Average Score</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{userStats.interviewsCompleted}</span>
            <span className="stat-label">Interviews</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{userStats.improvementRate}</span>
            <span className="stat-label">Improvement</span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="profile-navigation">
        <button 
          className={`nav-tab ${activeSection === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveSection('overview')}
        >
          📊 Overview
        </button>
        <button 
          className={`nav-tab ${activeSection === 'achievements' ? 'active' : ''}`}
          onClick={() => setActiveSection('achievements')}
        >
          🏆 Achievements
        </button>
        <button 
          className={`nav-tab ${activeSection === 'privacy' ? 'active' : ''}`}
          onClick={() => setActiveSection('privacy')}
        >
          🔒 Privacy & Data
        </button>
      </div>

      {/* Content Sections */}
      <div className="profile-content">
        {activeSection === 'overview' && (
          <div className="overview-section">
            {/* Performance Chart */}
            <div className="performance-card">
              <h3>📈 Performance Overview</h3>
              <div className="progress-stats">
                <div className="progress-item">
                  <label>Interview Confidence</label>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{width: '87%'}}></div>
                  </div>
                  <span className="progress-value">87%</span>
                </div>
                <div className="progress-item">
                  <label>Technical Skills</label>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{width: '73%'}}></div>
                  </div>
                  <span className="progress-value">73%</span>
                </div>
                <div className="progress-item">
                  <label>Communication</label>
                  <div className="progress-bar">
                    <div className="progress-fill" style={{width: '92%'}}></div>
                  </div>
                  <span className="progress-value">92%</span>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="activity-card">
              <h3>📝 Recent Activity</h3>
              <div className="activity-list">
                {recentActivity.map((activity, index) => (
                  <div key={index} className="activity-item">
                    <div className="activity-icon">{activity.icon}</div>
                    <div className="activity-details">
                      <h4>{activity.title}</h4>
                      <div className="activity-meta">
                        {activity.score && <span className="score">Score: {activity.score}%</span>}
                        {activity.duration && <span className="duration">{activity.duration}</span>}
                        <span className="date">{activity.date}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeSection === 'achievements' && (
          <div className="achievements-section">
            <h3>🏆 Your Achievements</h3>
            <p>Track your progress and unlock new milestones</p>
            <div className="achievements-grid">
              {achievements.map((achievement, index) => (
                <div key={index} className={`achievement-card ${achievement.earned ? 'earned' : 'locked'}`}>
                  <div className="achievement-icon">{achievement.icon}</div>
                  <h4>{achievement.title}</h4>
                  <p>{achievement.description}</p>
                  {achievement.earned ? (
                    <div className="earned-badge">
                      ✅ Earned {achievement.date}
                    </div>
                  ) : (
                    <div className="progress-badge">
                      📊 Progress: {achievement.progress}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeSection === 'privacy' && (
          <div className="privacy-section">
            <div className="privacy-header">
              <h3>🔒 Privacy & Data Settings</h3>
              <p>Control how your data is used to improve your experience</p>
            </div>
            
            <div className="privacy-card">
              <h4>🛡️ Data Protection</h4>
              <p>Your privacy is our priority. All interview data is processed securely and can be deleted at any time.</p>
              
              <div className="privacy-settings">
                <div className="setting-item">
                  <div className="setting-info">
                    <label>Data Anonymization</label>
                    <span>All personal data is automatically anonymized before analysis</span>
                  </div>
                  <div className="setting-control">
                    <span className="always-on">✅ Always On</span>
                  </div>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Analytics Tracking</label>
                    <span>Help us improve the platform with anonymous usage data</span>
                  </div>
                  <div className="setting-control">
                    <label className="toggle-switch">
                      <input 
                        type="checkbox" 
                        checked={privacySettings.analyticsTracking}
                        onChange={() => handlePrivacyToggle('analyticsTracking')}
                      />
                      <span className="slider"></span>
                    </label>
                  </div>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Personalized Feedback</label>
                    <span>Use your history to provide tailored recommendations</span>
                  </div>
                  <div className="setting-control">
                    <label className="toggle-switch">
                      <input 
                        type="checkbox" 
                        checked={privacySettings.personalizedFeedback}
                        onChange={() => handlePrivacyToggle('personalizedFeedback')}
                      />
                      <span className="slider"></span>
                    </label>
                  </div>
                </div>

                <div className="setting-item">
                  <div className="setting-info">
                    <label>Email Notifications</label>
                    <span>Receive tips and reminders to continue practicing</span>
                  </div>
                  <div className="setting-control">
                    <label className="toggle-switch">
                      <input 
                        type="checkbox" 
                        checked={privacySettings.emailNotifications}
                        onChange={() => handlePrivacyToggle('emailNotifications')}
                      />
                      <span className="slider"></span>
                    </label>
                  </div>
                </div>
              </div>

              <div className="data-actions">
                <button className="action-button secondary">📥 Export My Data</button>
                <button className="action-button danger">🗑️ Delete All Data</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Profile;
