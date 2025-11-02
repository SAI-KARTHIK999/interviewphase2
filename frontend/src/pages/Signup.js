import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Signup = ({ onLogin }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    phone: '',
    profession: '',
    experience: '',
    agreeToTerms: false,
    subscribeNewsletter: true
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);
  
  const navigate = useNavigate();

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (error) setError('');
    
    // Check password strength
    if (name === 'password') {
      setPasswordStrength(calculatePasswordStrength(value));
    }
  };

  const calculatePasswordStrength = (password) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    return strength;
  };

  const validateStep1 = () => {
    if (!formData.firstName.trim()) return 'First name is required';
    if (!formData.lastName.trim()) return 'Last name is required';
    if (!formData.email.trim()) return 'Email is required';
    if (!/\S+@\S+\.\S+/.test(formData.email)) return 'Please enter a valid email';
    return null;
  };

  const validateStep2 = () => {
    if (!formData.password) return 'Password is required';
    if (formData.password.length < 8) return 'Password must be at least 8 characters';
    if (formData.password !== formData.confirmPassword) return 'Passwords do not match';
    if (!formData.agreeToTerms) return 'You must agree to the terms and conditions';
    return null;
  };

  const handleNext = () => {
    const error = validateStep1();
    if (error) {
      setError(error);
      return;
    }
    setCurrentStep(2);
    setError('');
  };

  const handleBack = () => {
    setCurrentStep(1);
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const error = validateStep2();
    if (error) {
      setError(error);
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const userData = {
        id: Date.now(),
        name: `${formData.firstName} ${formData.lastName}`,
        firstName: formData.firstName,
        lastName: formData.lastName,
        email: formData.email,
        phone: formData.phone,
        profession: formData.profession,
        experience: formData.experience,
        avatar: '👤',
        joinDate: new Date().toISOString().split('T')[0],
        lastLogin: new Date().toISOString(),
        subscribeNewsletter: formData.subscribeNewsletter,
        stats: {
          interviewsCompleted: 0,
          averageScore: 0,
          totalPracticeTime: '0m',
          improvementRate: '0%'
        }
      };
      
      // Store user data in localStorage
      localStorage.setItem('user', JSON.stringify(userData));
      localStorage.setItem('isAuthenticated', 'true');
      
      // Call parent login handler
      onLogin(userData);
      
      // Navigate to home with welcome message
      navigate('/');
    } catch (error) {
      setError(error.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const professionOptions = [
    'Software Developer',
    'Data Scientist',
    'Product Manager',
    'Marketing Specialist',
    'Sales Representative',
    'Consultant',
    'Designer',
    'Analyst',
    'Student',
    'Other'
  ];

  const experienceOptions = [
    'No experience',
    '0-1 years',
    '1-3 years',
    '3-5 years',
    '5-10 years',
    '10+ years'
  ];

  const getPasswordStrengthText = () => {
    switch (passwordStrength) {
      case 0:
      case 1: return { text: 'Weak', color: '#ef4444' };
      case 2:
      case 3: return { text: 'Medium', color: '#f59e0b' };
      case 4:
      case 5: return { text: 'Strong', color: '#10b981' };
      default: return { text: 'Weak', color: '#ef4444' };
    }
  };

  return (
    <div className={`auth-container ${isVisible ? 'fade-in' : ''}`}>
      <div className="auth-content signup">
        {/* Header */}
        <div className="auth-header">
          <div className="auth-badge">
            <span className="badge-icon">🚀</span>
            <span>Join AI Interview Bot</span>
          </div>
          <h1>Create Your Account</h1>
          <p>Start your journey to interview success</p>
          
          {/* Progress Indicator */}
          <div className="progress-indicator">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${(currentStep / 2) * 100}%` }}
              ></div>
            </div>
            <div className="progress-steps">
              <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>
                <span>1</span>
                <label>Basic Info</label>
              </div>
              <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
                <span>2</span>
                <label>Security & Preferences</label>
              </div>
            </div>
          </div>
        </div>

        {/* Signup Form */}
        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* Step 1: Basic Information */}
          {currentStep === 1 && (
            <div className="form-step">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="firstName">First Name</label>
                  <div className="input-container">
                    <span className="input-icon">👤</span>
                    <input
                      type="text"
                      id="firstName"
                      name="firstName"
                      value={formData.firstName}
                      onChange={handleInputChange}
                      placeholder="Enter your first name"
                      required
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="lastName">Last Name</label>
                  <div className="input-container">
                    <span className="input-icon">👤</span>
                    <input
                      type="text"
                      id="lastName"
                      name="lastName"
                      value={formData.lastName}
                      onChange={handleInputChange}
                      placeholder="Enter your last name"
                      required
                    />
                  </div>
                </div>
              </div>

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
                    placeholder="Enter your email address"
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="phone">Phone Number (Optional)</label>
                <div className="input-container">
                  <span className="input-icon">📱</span>
                  <input
                    type="tel"
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    placeholder="Enter your phone number"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="profession">Profession</label>
                  <div className="input-container">
                    <span className="input-icon">💼</span>
                    <select
                      id="profession"
                      name="profession"
                      value={formData.profession}
                      onChange={handleInputChange}
                    >
                      <option value="">Select profession</option>
                      {professionOptions.map(option => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="experience">Experience Level</label>
                  <div className="input-container">
                    <span className="input-icon">⭐</span>
                    <select
                      id="experience"
                      name="experience"
                      value={formData.experience}
                      onChange={handleInputChange}
                    >
                      <option value="">Select experience</option>
                      {experienceOptions.map(option => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <button
                type="button"
                className="auth-button primary"
                onClick={handleNext}
              >
                <span>Continue</span>
                <span className="button-icon">→</span>
              </button>
            </div>
          )}

          {/* Step 2: Security & Preferences */}
          {currentStep === 2 && (
            <div className="form-step">
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
                    placeholder="Create a strong password"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? '👁️' : '🙈'}
                  </button>
                </div>
                {formData.password && (
                  <div className="password-strength">
                    <div className="strength-bar">
                      <div 
                        className="strength-fill" 
                        style={{ 
                          width: `${(passwordStrength / 5) * 100}%`,
                          backgroundColor: getPasswordStrengthText().color
                        }}
                      ></div>
                    </div>
                    <span 
                      className="strength-text"
                      style={{ color: getPasswordStrengthText().color }}
                    >
                      {getPasswordStrengthText().text}
                    </span>
                  </div>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm Password</label>
                <div className="input-container">
                  <span className="input-icon">🔒</span>
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    placeholder="Confirm your password"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? '👁️' : '🙈'}
                  </button>
                </div>
              </div>

              <div className="form-checkboxes">
                <label className="checkbox-container">
                  <input
                    type="checkbox"
                    name="agreeToTerms"
                    checked={formData.agreeToTerms}
                    onChange={handleInputChange}
                    required
                  />
                  <span className="checkmark"></span>
                  <span>
                    I agree to the{' '}
                    <Link to="/terms" className="auth-link">Terms of Service</Link>
                    {' '}and{' '}
                    <Link to="/privacy" className="auth-link">Privacy Policy</Link>
                  </span>
                </label>

                <label className="checkbox-container">
                  <input
                    type="checkbox"
                    name="subscribeNewsletter"
                    checked={formData.subscribeNewsletter}
                    onChange={handleInputChange}
                  />
                  <span className="checkmark"></span>
                  <span>Send me interview tips and updates</span>
                </label>
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  className="auth-button secondary"
                  onClick={handleBack}
                >
                  <span className="button-icon">←</span>
                  <span>Back</span>
                </button>

                <button
                  type="submit"
                  className={`auth-button primary ${isLoading ? 'loading' : ''}`}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <span className="spinner"></span>
                      <span>Creating Account...</span>
                    </>
                  ) : (
                    <>
                      <span>Create Account</span>
                      <span className="button-icon">✨</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="auth-link">
              Sign In
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

export default Signup;