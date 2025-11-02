import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';

function Interview() {
  const webcamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const [isRecording, setIsRecording] = useState(false);
  const [recordedChunks, setRecordedChunks] = useState([]);
  const [feedback, setFeedback] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(''); // 'uploading', 'processing', 'complete', 'error'
  const [recordingTime, setRecordingTime] = useState(0);
  const [recordingTimer, setRecordingTimer] = useState(null);

  const question = "Tell me about a challenging project you worked on.";

  // All your handleStartRecording, handleStopRecording, and handleSubmit
  // functions remain exactly the same.
  const handleStartRecording = useCallback(() => {
    setIsRecording(true);
    setRecordingTime(0);
    setFeedback(null);
    
    // Start recording timer
    const timer = setInterval(() => {
      setRecordingTime(prev => prev + 1);
    }, 1000);
    setRecordingTimer(timer);
    
    mediaRecorderRef.current = new MediaRecorder(webcamRef.current.stream, { mimeType: "video/webm" });
    mediaRecorderRef.current.addEventListener("dataavailable", handleDataAvailable);
    mediaRecorderRef.current.start();
  }, [webcamRef, setIsRecording, mediaRecorderRef]);

  const handleDataAvailable = useCallback(({ data }) => { /* ... no changes ... */
    if (data.size > 0) {
      setRecordedChunks((prev) => prev.concat(data));
    }
  }, [setRecordedChunks]);

  const handleStopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Clear recording timer
      if (recordingTimer) {
        clearInterval(recordingTimer);
        setRecordingTimer(null);
      }
    }
  }, [mediaRecorderRef, setIsRecording, isRecording, recordingTimer]);

  const handleSubmit = useCallback(async () => {
    if (recordedChunks.length) {
      const blob = new Blob(recordedChunks, { type: "video/webm" });
      
      // Validate file size (50MB limit)
      const maxSize = 50 * 1024 * 1024; // 50MB in bytes
      if (blob.size > maxSize) {
        setFeedback({ 
          feedback: "Error: Video file is too large (max 50MB). Please record a shorter video.",
          error: true 
        });
        return;
      }
      
      if (blob.size < 1024) { // Less than 1KB
        setFeedback({ 
          feedback: "Error: Video file is too small. Please record a longer video.",
          error: true 
        });
        return;
      }
      
      setIsLoading(true);
      setUploadStatus('uploading');
      setUploadProgress(0);
      setFeedback(null);
      
      const formData = new FormData();
      formData.append("video", blob, "interview-response.webm");
      
      try {
        // Simulate upload progress
        const progressInterval = setInterval(() => {
          setUploadProgress(prev => {
            if (prev >= 90) {
              clearInterval(progressInterval);
              return 90; // Stop at 90% until we get response
            }
            return prev + 10;
          });
        }, 200);
        
        const response = await fetch('http://localhost:5001/api/interview/video', { 
          method: 'POST', 
          body: formData 
        });
        
        clearInterval(progressInterval);
        setUploadProgress(100);
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        setUploadStatus('processing');
        const data = await response.json();
        
        setTimeout(() => {
          setUploadStatus('complete');
          setFeedback(data.assessment);
        }, 500);
        
      } catch (error) {
        setUploadStatus('error');
        setFeedback({ 
          feedback: `Error: ${error.message}`,
          error: true 
        });
      } finally {
        setTimeout(() => {
          setRecordedChunks([]);
          setIsLoading(false);
          setUploadProgress(0);
          setUploadStatus('');
        }, 2000);
      }
    }
  }, [recordedChunks]);

  return (
    <div className="interview-page">
      <div className="interview-header">
        <div className="header-content">
          <div className="interview-badge">
            <span className="badge-icon">🎙️</span>
            <span>Live Interview Session</span>
          </div>
          <h1>AI Interview Practice</h1>
          <div className="question-display">
            <div className="question-label">💬 Interview Question:</div>
            <p className="question-text">{question}</p>
          </div>
        </div>
      </div>
      
      <div className="interview-content">
        <div className="webcam-section">
        <div className="webcam-container">
          <Webcam 
            audio={{
              echoCancellation: true,
              noiseSuppression: true,
              autoGainControl: true,
              suppressLocalAudioPlayback: true  // This prevents audio playback through speakers
            }}
            ref={webcamRef} 
            width="100%"
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
        
        {/* Upload Progress */}
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
        
        {/* Video Info */}
        {recordedChunks.length > 0 && !isRecording && (
          <div className="video-info">
            <div className="video-stats">
              <span>📹 Video recorded</span>
              <span>⏱️ Duration: {Math.floor(recordingTime / 60)}:{String(recordingTime % 60).padStart(2, '0')}</span>
              <span>📦 Size: {(new Blob(recordedChunks).size / 1024 / 1024).toFixed(2)} MB</span>
            </div>
          </div>
        )}
        
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
        </div>
        
        <div className="interview-controls">
        {isRecording ? (
          <button onClick={handleStopRecording} className="button button-destructive">Stop Recording</button>
        ) : (
          <button onClick={handleStartRecording} className="button button-primary" disabled={recordedChunks.length > 0}>Start Recording</button>
        )}

        {recordedChunks.length > 0 && !isRecording && (
          <button onClick={handleSubmit} className="button button-primary" disabled={isLoading}>
            {isLoading ? 'Uploading...' : 'Submit Video'}
          </button>
        )}
        </div>
      </div>
    </div>
  );
}

export default Interview;