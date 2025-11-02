import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Login = ({ onLogin }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const navigate = useNavigate();

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // For demo purposes, accept any email/password combination
      if (formData.email && formData.password) {
        const userData = {
          id: Date.now(),
          name: formData.email.split('@')[0],
          email: formData.email,
          avatar: '👤',
          joinDate: new Date().toISOString().split('T')[0],
          lastLogin: new Date().toISOString()
        };
        
        // Store user data in localStorage
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('isAuthenticated', 'true');
        
        // Call parent login handler
        onLogin(userData);
        
        // Navigate to home
        navigate('/');
      } else {
        throw new Error('Please fill in all fields');
      }
    } catch (error) {
      setError(error.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setFormData({
      email: 'demo@aiinterviewbot.com',
      password: 'demo123'
    });
    
    setTimeout(() => {
      handleSubmit({ preventDefault: () => {} });
    }, 100);
  };

  return (
    <div className={`auth-container ${isVisible ? 'fade-in' : ''}`}>
      <div className="auth-content">
        {/* Header */}
        <div className="auth-header">
          <div className="auth-badge">
            <span className="badge-icon">🔐</span>
            <span>Secure Login</span>
          </div>
          <h1>Welcome Back!</h1>
          <p>Sign in to continue your interview preparation journey</p>
        </div>

        {/* Login Form */}
        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <div className="input-container">
              <span className="input-icon">📧</span>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Enter your email"
                required
                disabled={isLoading}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-container">
              <span className="input-icon">🔒</span>
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Enter your password"
                required
                disabled={isLoading}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? '👁️' : '🙈'}
              </button>
            </div>
          </div>

          <div className="form-options">
            <label className="remember-me">
              <input type="checkbox" />
              <span className="checkmark"></span>
              <span>Remember me</span>
            </label>
            <Link to="/forgot-password" className="forgot-link">
              Forgot password?
            </Link>
          </div>

          <button
            type="submit"
            className={`auth-button primary ${isLoading ? 'loading' : ''}`}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                <span>Signing In...</span>
              </>
            ) : (
              <>
                <span>Sign In</span>
                <span className="button-icon">→</span>
              </>
            )}
          </button>

          <div className="divider">
            <span>or</span>
          </div>

          <button
            type="button"
            className="auth-button demo"
            onClick={handleDemoLogin}
            disabled={isLoading}
          >
            <span className="demo-icon">🚀</span>
            <span>Try Demo Account</span>
          </button>
        </form>

        {/* Footer */}
        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <Link to="/signup" className="auth-link">
              Create Account
            </Link>
          </p>
        </div>
      </div>

      {/* Background Animation */}
      <div className="auth-background">
        <div className="floating-shape shape-1"></div>
        <div className="floating-shape shape-2"></div>
        <div className="floating-shape shape-3"></div>
      </div>
    </div>
  );
};

export default Login;