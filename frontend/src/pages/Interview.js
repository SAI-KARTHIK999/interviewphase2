import React, { useState, useRef, useCallback, useEffect } from 'react';
import Webcam from 'react-webcam';
import ConsentModal from '../components/ConsentModal';

function Interview({ user }) {
  const webcamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const [isRecording, setIsRecording] = useState(false);
  const [recordedChunks, setRecordedChunks] = useState([]);
  const [feedback, setFeedback] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [recordingTime, setRecordingTime] = useState(0);
  const [recordingTimer, setRecordingTimer] = useState(null);

  // Sequenced interview state
  const questions = [
    { id: 'q1', text: 'Tell me about a challenging project you worked on.' },
    { id: 'q2', text: 'Describe a situation where you had to learn something new quickly.' },
    { id: 'q3', text: 'Walk me through how you would approach debugging a complex issue.' }
  ];
  const [currentIndex, setCurrentIndex] = useState(0);
  const [canGoNext, setCanGoNext] = useState(false);

  // New consent state management
  const [showOverview, setShowOverview] = useState(true);
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [consentGiven, setConsentGiven] = useState(false);
  const [consentData, setConsentData] = useState(null);
  const [sessionMode, setSessionMode] = useState(null);
  const [userId, setUserId] = useState(null);
  const [consentId, setConsentId] = useState(null);
  const [retentionInfo, setRetentionInfo] = useState(null);

  useEffect(() => {
    // Set user ID from props or generate a temporary one
    if (user && user.email) {
      setUserId(user.email);
    } else {
      setUserId(`guest_${Date.now()}`);
    }

    // Fetch retention info
    fetch('http://localhost:5001/api/data/retention-info')
      .then(res => res.json())
      .then(setRetentionInfo)
      .catch(() => {});
  }, [user]);

  // Derived current question
  const currentQuestion = questions[currentIndex];

  // Handle consent submission
  const handleConsentSubmit = async (permissions) => {
    try {
      // Send consent to backend
      const response = await fetch('http://localhost:5001/api/consent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: userId,
          allow_audio: permissions.allow_audio,
          allow_video: permissions.allow_video,
          allow_storage: permissions.allow_storage,
          session_mode: permissions.session_mode
        })
      });

      if (!response.ok) {
        throw new Error('Failed to record consent');
      }

      const data = await response.json();
      
      // Store consent data and session info
      setConsentData(permissions);
      setSessionMode(data.session_mode);
      setConsentId(data.consent_id);
      setConsentGiven(true);
      setShowConsentModal(false);

      console.log('Consent recorded:', data);
    } catch (error) {
      console.error('Error submitting consent:', error);
      alert('Failed to record consent. Please try again.');
    }
  };

  // Handle modal close without consent
  const handleConsentModalClose = () => {
    alert('You must provide consent to continue with the interview.');
  };

  const handleDataAvailable = useCallback(({ data }) => {
    if (data.size > 0) {
      setRecordedChunks((prev) => prev.concat(data));
    }
  }, [setRecordedChunks]);

  const handleStartRecording = useCallback(() => {
    if (sessionMode === 'practice') {
      alert('Recording is disabled in practice mode. Please restart with recording consent.');
      return;
    }
    
    if (!consentData || (!consentData.allow_audio && !consentData.allow_video)) {
      alert('You must consent to recording before starting.');
      return;
    }
    
    setIsRecording(true);
    setRecordingTime(0);
    setFeedback(null);
    setCanGoNext(false);
    
    const timer = setInterval(() => {
      setRecordingTime(prev => prev + 1);
    }, 1000);
    setRecordingTimer(timer);
    
    mediaRecorderRef.current = new MediaRecorder(webcamRef.current.stream, { mimeType: "video/webm" });
    mediaRecorderRef.current.addEventListener("dataavailable", handleDataAvailable);
    mediaRecorderRef.current.start();
  }, [webcamRef, setIsRecording, mediaRecorderRef, consentData, sessionMode, handleDataAvailable]);

  const handleStopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (recordingTimer) {
        clearInterval(recordingTimer);
        setRecordingTimer(null);
      }
    }
  }, [mediaRecorderRef, setIsRecording, isRecording, recordingTimer]);

  const handleSubmit = useCallback(async () => {
    if (recordedChunks.length) {
      const blob = new Blob(recordedChunks, { type: "video/webm" });
      
      console.log('Submitting video:', {
        size: blob.size,
        type: blob.type,
        consentId: consentId,
        userId: userId,
        consentData: consentData
      });
      
      const maxSize = 50 * 1024 * 1024;
      if (blob.size > maxSize) {
        setFeedback({ 
          feedback: "Error: Video file is too large (max 50MB). Please record a shorter video.",
          error: true 
        });
        return;
      }
      
      if (blob.size < 1024) {
        setFeedback({ 
          feedback: "Error: Video file is too small. Please record a longer video.",
          error: true 
        });
        return;
      }
      
      // Validate consent data
      if (!consentData || !consentId || !userId) {
        setFeedback({ 
          feedback: "Error: Consent information is missing. Please refresh and provide consent again.",
          error: true 
        });
        console.error('Missing consent data:', { consentData, consentId, userId });
        return;
      }
      
      setIsLoading(true);
      setUploadStatus('uploading');
      setUploadProgress(0);
      setFeedback(null);
      setCanGoNext(false);
      
      const formData = new FormData();
      formData.append("video", blob, "interview-response.webm");
      formData.append('consent_record', String(consentData.allow_audio || consentData.allow_video));
      formData.append('consent_analyze', String(true));
      formData.append('opt_in_data_save', String(consentData.allow_storage));
      formData.append('opt_in_data_share', String(false));
      formData.append('consent_version', 'v2.0');
      formData.append('consent_id', consentId || '');
      formData.append('user_id', userId || '');
      // Attach question context
      formData.append('question_id', currentQuestion?.id || String(currentIndex + 1));
      formData.append('question_text', currentQuestion?.text || '');
      
      console.log('FormData prepared with:', {
        consent_record: consentData.allow_audio || consentData.allow_video,
        consent_analyze: true,
        opt_in_data_save: consentData.allow_storage,
        consent_id: consentId,
        user_id: userId
      });
      
      try {
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => {
            if (prev >= 90) {
              clearInterval(progressInterval);
              return 90;
            }
            return prev + 10;
          });
        }, 200);
        
        console.log('Sending request to backend...');
        const response = await fetch('http://localhost:5001/api/interview/video', { 
          method: 'POST', 
          body: formData 
        });
        
        clearInterval(progressInterval);
        setUploadProgress(100);
        
        console.log('Response received:', response.status, response.statusText);
        
        if (!response.ok) {
          let errorData;
          try {
            errorData = await response.json();
          } catch (e) {
            errorData = { error: `Server returned ${response.status}: ${response.statusText}` };
          }
          console.error('Server error:', errorData);
          throw new Error(errorData.error || errorData.hint || `HTTP error! status: ${response.status}`);
        }
        
        setUploadStatus('processing');
        const data = await response.json();
        
        console.log('Response data:', data);
        
        if (!data.assessment) {
          console.warn('No assessment in response:', data);
        }
        
        setTimeout(() => {
          setUploadStatus('complete');
          setFeedback(data.assessment || { 
            score: 0, 
            feedback: 'Analysis complete, but no detailed feedback available.' 
          });
          setCanGoNext(true);
        }, 500);
        
      } catch (error) {
        console.error('Video upload error:', error);
        setUploadStatus('error');
        
        // Provide more detailed error information
        let errorMessage = 'Failed to upload video. ';
        if (error.message.includes('Failed to fetch')) {
          errorMessage += 'Cannot connect to server. Please ensure the backend is running on http://localhost:5001';
        } else if (error.message.includes('NetworkError')) {
          errorMessage += 'Network error. Please check your connection.';
        } else {
          errorMessage += error.message;
        }
        
        setFeedback({ 
          feedback: errorMessage,
          error: true 
        });
      } finally {
        // Keep recordedChunks until Next is clicked, so user can retry submit if needed
        setIsLoading(false);
      }
    }
  }, [recordedChunks, consentData, consentId, userId, currentQuestion, currentIndex]);

  // Show overview first
  if (showOverview) {
    return (
      <div className="interview-page">
        <div className="interview-overview">
          <div className="overview-header">
            <div className="interview-badge">
              <span className="badge-icon">🎯</span>
              <span>AI-Powered Interview Practice</span>
            </div>
            <h1>Welcome to Your Interview Session</h1>
            <p className="overview-subtitle">
              Get ready to practice with our AI interview bot that provides real-time feedback and analysis
            </p>
            <div className="overview-header-actions">
              <button 
                className="button button-primary button-large"
                onClick={() => {
                  setShowOverview(false);
                  setShowConsentModal(true);
                }}
              >
                <span>Start Interview</span>
                <span className="button-icon">→</span>
              </button>
              <p className="overview-note">
                You'll be asked to provide consent for recording and data storage before beginning
              </p>
            </div>
          </div>

          <div className="overview-content">
            <div className="overview-grid">
              {/* Purpose Section */}
              <div className="overview-card">
                <div className="card-icon">🎯</div>
                <h3>Purpose</h3>
                <p>
                  This interview session helps you practice answering common interview questions while receiving 
                  AI-powered feedback on your responses. Improve your communication skills, confidence, and 
                  interview performance.
                </p>
              </div>

              {/* Question Count */}
              <div className="overview-card">
                <div className="card-icon">❓</div>
                <h3>Questions</h3>
                <p>
                  You'll answer <strong>{questions.length} questions</strong> covering different aspects of 
                  interview preparation, including behavioral scenarios, technical knowledge, and problem-solving skills.
                </p>
              </div>

              {/* Duration */}
              <div className="overview-card">
                <div className="card-icon">⏱️</div>
                <h3>Duration</h3>
                <p>
                  Estimated time: <strong>15-20 minutes</strong>. Each question allows you to record your response 
                  at your own pace. Take your time to think and provide thoughtful answers.
                </p>
              </div>

              {/* Guidelines */}
              <div className="overview-card guidelines-card">
                <div className="card-icon">📋</div>
                <h3>Guidelines</h3>
                <ul className="guidelines-list">
                  <li>
                    <strong>Be yourself:</strong> Answer naturally and authentically, as you would in a real interview
                  </li>
                  <li>
                    <strong>Take your time:</strong> Think before you speak. There's no rush—quality over speed
                  </li>
                  <li>
                    <strong>Use examples:</strong> Support your answers with specific examples from your experience
                  </li>
                  <li>
                    <strong>Stay focused:</strong> Keep your answers relevant and concise, typically 2-3 minutes per question
                  </li>
                  <li>
                    <strong>Review feedback:</strong> After each question, review the AI feedback to improve your next response
                  </li>
                  <li>
                    <strong>Privacy first:</strong> You control what data is recorded and stored. Choose your privacy preferences in the next step
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show consent modal after overview
  if (showConsentModal || !consentGiven) {
    return (
      <ConsentModal 
        onConsentSubmit={handleConsentSubmit}
        onClose={handleConsentModalClose}
      />
    );
  }

  // Show practice mode UI if user declined recording
  if (sessionMode === 'practice') {
    return (
      <div className="interview-page practice-mode">
        <div className="interview-header">
          <div className="header-content">
            <div className="interview-badge practice">
              <span className="badge-icon">📝</span>
              <span>Practice Mode (Text-Only)</span>
            </div>
            <h1>AI Interview Practice</h1>
            <div className="question-display">
              <div className="question-label">💬 Question {currentIndex + 1} of {questions.length}</div>
              <p className="question-text">{currentQuestion.text}</p>
            </div>
          </div>
        </div>

        <div className="interview-content">
          <div className="interview-grid">
            <div className="question-panel card">
              <h3 className="panel-title">Current Question</h3>
              <p className="panel-text">{currentQuestion.text}</p>
              <div className="panel-footer">
                <button
                  className="button button-secondary"
                  onClick={() => {
                    setCurrentIndex((idx) => idx + 1);
                  }}
                >
                  {currentIndex + 1 < questions.length ? 'Next Question →' : 'Finish Practice'}
                </button>
              </div>
            </div>

            <div className="answer-panel card">
              <div className="practice-mode-info">
                <h3>🔒 Privacy Protected</h3>
                <p>You're practicing without recording. Write your answer below:</p>
              </div>
              <div className="text-answer-section">
                <textarea
                  className="text-answer-input"
                  placeholder="Type your answer here..."
                  rows="10"
                />
                <div className="panel-actions">
                  <button className="button button-primary">Submit (Not Saved)</button>
                  <button
                    className="button button-ghost"
                    onClick={() => {
                      setShowConsentModal(true);
                      setConsentGiven(false);
                    }}
                  >
                    Change Consent Settings
                  </button>
                </div>
              </div>
              <p className="muted" style={{ marginTop: '0.75rem' }}>
                Note: In practice mode, no audio or video is recorded. Your text answer will not be saved.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Completed interview screen
  if (currentIndex >= questions.length) {
    return (
      <div className="interview-page">
        <div className="interview-header">
          <div className="header-content">
            <div className="interview-badge">
              <span className="badge-icon">✅</span>
              <span>Interview Complete</span>
            </div>
            <h1>Great work!</h1>
            <div className="question-display">
              <div className="question-label">You’ve completed all questions.</div>
              <p className="question-text">Your responses and videos have been saved{consentData?.allow_storage ? ' (for 30 days).' : ' per your consent settings.'}</p>
            </div>
          </div>
        </div>
        <div className="interview-content">
          <div className="next-control">
            <button className="button button-primary" onClick={() => setCurrentIndex(0)}>
              Restart Interview
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Full interview mode with recording
  return (
    <div className="interview-page interview-active">
      <div className="interview-content">
        {/* Compact Consent Status */}
        <div className="consent-status-compact">
          <div className="consent-status-left">
            <span className="status-indicator">●</span>
            <span className="status-text">Recording Active</span>
            {consentData && !consentData.allow_storage && (
              <span className="status-badge">🔒 Not Saving</span>
            )}
          </div>
          <button 
            className="button button-ghost button-small"
            onClick={() => {
              setShowConsentModal(true);
              setConsentGiven(false);
            }}
          >
            Modify Consent
          </button>
        </div>

        <div className="interview-grid">
          {/* Left: Question Panel */}
          <div className="question-panel card">
            <div className="question-header-compact">
              <div className="question-counter">
                Question {currentIndex + 1} of {questions.length}
              </div>
            </div>
            <div className="question-content-main">
              <h3 className="panel-title">Current Question</h3>
              <p className="panel-text">{currentQuestion.text}</p>
            </div>
            
            {feedback && (
              <div className={`feedback-section ${feedback.error ? 'error' : 'success'}`}>
                <h3>{feedback.error ? 'Error' : 'Analysis Results'}</h3>
                {!feedback.error && (
                  <div className="score-display">
                    <div className="score-circle">
                      <span className="score-value">{feedback.score !== undefined ? Math.round(feedback.score * 100) : 'N/A'}</span>
                      <span className="score-label">%</span>
                    </div>
                  </div>
                )}
                <div className="feedback-text">
                  <p>{feedback.feedback}</p>
                </div>
              </div>
            )}

            {canGoNext && (
              <div className="next-control">
                <button
                  className="button button-secondary"
                  onClick={() => {
                    setCurrentIndex((idx) => idx + 1);
                    setRecordedChunks([]);
                    setRecordingTime(0);
                    setFeedback(null);
                    setUploadProgress(0);
                    setUploadStatus('');
                    setCanGoNext(false);
                  }}
                >
                  {currentIndex + 1 < questions.length ? 'Next Question →' : 'Finish Interview'}
                </button>
              </div>
            )}
          </div>

          {/* Right: Video Panel */}
          <div className="video-panel card">
            <div className="video-panel-header">
              <h3 className="panel-title">Video Recording</h3>
            </div>
            <div className="webcam-section">
              <div className="webcam-container">
                <Webcam 
                  audio={{
                    echoCancellation: { exact: true },
                    noiseSuppression: { exact: true },
                    autoGainControl: { exact: true },
                    sampleRate: 48000,
                    channelCount: 1
                  }}
                  ref={webcamRef} 
                  width="100%"
                  muted={true}
                  videoConstraints={{
                    facingMode: 'user',
                    width: 1280,
                    height: 720
                  }}
                />
                {isRecording && (
                  <div className="recording-overlay">
                    <div className="recording-indicator">
                      <div className="recording-dot"></div>
                      <span>Recording: {Math.floor(recordingTime / 60)}:{String(recordingTime % 60).padStart(2, '0')}</span>
                    </div>
                  </div>
                )}
              </div>

              {isLoading && (
                <div className="upload-progress-container">
                  <div className="upload-status">
                    {uploadStatus === 'uploading' && <span>📤 Uploading video...</span>}
                    {uploadStatus === 'processing' && <span>🤖 Analyzing your response...</span>}
                    {uploadStatus === 'complete' && <span>✅ Analysis complete!</span>}
                    {uploadStatus === 'error' && <span>❌ Upload failed</span>}
                  </div>
                  <div className="progress-bar-container">
                    <div className="progress-bar-fill" style={{ width: `${uploadProgress}%` }}></div>
                  </div>
                  <div className="progress-text">{uploadProgress}%</div>
                </div>
              )}

              {recordedChunks.length > 0 && !isRecording && (
                <div className="video-info">
                  <div className="video-stats">
                    <span>📹 Video recorded</span>
                    <span>⏱️ Duration: {Math.floor(recordingTime / 60)}:{String(recordingTime % 60).padStart(2, '0')}</span>
                    <span>📦 Size: {(new Blob(recordedChunks).size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                </div>
              )}

              <div className="interview-controls">
                {isRecording ? (
                  <button onClick={handleStopRecording} className="button button-destructive">Stop Recording</button>
                ) : (
                  <button onClick={handleStartRecording} className="button button-primary" disabled={isLoading || (recordedChunks.length > 0 && !isRecording)}>
                    Start Recording
                  </button>
                )}

                {recordedChunks.length > 0 && !isRecording && (
                  <button onClick={handleSubmit} className="button button-primary" disabled={isLoading}>
                    {isLoading ? 'Uploading...' : 'Submit Video'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Interview;
