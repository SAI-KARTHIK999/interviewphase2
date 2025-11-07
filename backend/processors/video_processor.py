"""
Video Processing Module with MediaPipe
Extracts face frames and performs attention/emotion analysis
"""

import os
import cv2
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import MediaPipe
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    logger.info("✓ MediaPipe loaded successfully")
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("⚠️ MediaPipe not available - using mock analysis")

class VideoProcessor:
    def __init__(self):
        self.mp_face_detection = None
        self.mp_face_mesh = None
        
        if MEDIAPIPE_AVAILABLE:
            try:
                self.mp_face_detection = mp.solutions.face_detection
                self.mp_face_mesh = mp.solutions.face_mesh
                logger.info("✓ MediaPipe modules initialized")
            except Exception as e:
                logger.error(f"✗ MediaPipe initialization error: {e}")
    
    async def process_video(self, video_file_path: str, sample_rate: int = 30) -> Dict:
        """
        Process video to extract faces and analyze attention/emotion
        
        Args:
            video_file_path: Path to video file
            sample_rate: Process every Nth frame
            
        Returns:
            Dict with analysis results
        """
        start_time = datetime.utcnow()
        
        try:
            if not MEDIAPIPE_AVAILABLE or self.mp_face_detection is None:
                # Mock results
                return {
                    'frames_processed': 0,
                    'faces_detected': 0,
                    'attention_score': None,
                    'emotion_summary': None,
                    'processing_time_seconds': 0.0
                }
            
            cap = cv2.VideoCapture(video_file_path)
            if not cap.isOpened():
                raise Exception("Cannot open video file")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            frames_processed = 0
            faces_detected = 0
            attention_scores = []
            
            with self.mp_face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=0.5
            ) as face_detection:
                frame_idx = 0
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Sample frames
                    if frame_idx % sample_rate == 0:
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = face_detection.process(rgb_frame)
                        
                        if results.detections:
                            faces_detected += len(results.detections)
                            # Calculate attention score (simplified - face center in frame)
                            for detection in results.detections:
                                bbox = detection.location_data.relative_bounding_box
                                center_x = bbox.xmin + bbox.width / 2
                                center_y = bbox.ymin + bbox.height / 2
                                # Score based on how centered the face is
                                attention = 1.0 - abs(0.5 - center_x) - abs(0.4 - center_y)
                                attention_scores.append(max(0, min(1, attention)))
                        
                        frames_processed += 1
                    
                    frame_idx += 1
            
            cap.release()
            
            # Calculate metrics
            avg_attention = sum(attention_scores) / len(attention_scores) if attention_scores else 0.0
            
            # Mock emotion summary (would need additional model)
            emotion_summary = {
                'neutral': 0.7,
                'happy': 0.2,
                'engaged': 0.8
            }
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✓ Video processed: {frames_processed} frames, {faces_detected} faces detected")
            
            return {
                'frames_processed': frames_processed,
                'faces_detected': faces_detected,
                'attention_score': round(avg_attention, 3),
                'emotion_summary': emotion_summary,
                'processing_time_seconds': round(processing_time, 2)
            }
            
        except Exception as e:
            logger.error(f"✗ Video processing error: {e}")
            raise

_video_processor = None

def get_video_processor() -> VideoProcessor:
    global _video_processor
    if _video_processor is None:
        _video_processor = VideoProcessor()
    return _video_processor
