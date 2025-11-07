"""
Tone Analyzer Module
Analyzes tone and emotion from text and optionally audio prosodic features.
"""

import numpy as np
from typing import Dict, Optional, Tuple
from transformers import pipeline
import logging
import time

logger = logging.getLogger(__name__)

# Try to import librosa for audio processing (optional)
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not available. Audio prosody analysis disabled.")


class ToneAnalyzer:
    """
    Analyzes tone and emotion from text and optionally audio features.
    Provides tone_score (0-100) and tone_label (calm/enthusiastic/hesitant/etc.).
    """
    
    def __init__(
        self,
        tone_model: str = "distilbert-base-uncased-finetuned-sst-2-english",
        device: str = "cpu"
    ):
        """
        Initialize tone analyzer.
        
        Args:
            tone_model: Model for sentiment/emotion analysis
            device: Device to run on (cuda/cpu)
        """
        self.device = device
        
        # Initialize text-based emotion/sentiment model
        try:
            self.emotion_classifier = pipeline(
                "sentiment-analysis",
                model=tone_model,
                device=0 if device == "cuda" else -1,
                truncation=True
            )
            logger.info(f"Loaded tone model: {tone_model}")
        except Exception as e:
            logger.error(f"Failed to load tone model: {e}")
            self.emotion_classifier = None
    
    def analyze_text_tone(self, text: str) -> Tuple[float, str]:
        """
        Analyze tone from text using sentiment analysis.
        
        Args:
            text: Input text
            
        Returns:
            (tone_score, tone_label)
        """
        if not text:
            return 50.0, "neutral"
        
        tone_score = 50.0
        tone_label = "neutral"
        
        if self.emotion_classifier:
            try:
                result = self.emotion_classifier(text[:512])[0]
                confidence = result['score']
                sentiment = result['label']
                
                # Map sentiment to tone
                if sentiment == 'POSITIVE':
                    tone_score = 50 + (confidence * 50)  # 50-100
                    if tone_score > 80:
                        tone_label = "enthusiastic"
                    elif tone_score > 65:
                        tone_label = "positive"
                    else:
                        tone_label = "calm"
                else:  # NEGATIVE
                    tone_score = 50 - (confidence * 50)  # 0-50
                    if tone_score < 20:
                        tone_label = "anxious"
                    elif tone_score < 35:
                        tone_label = "hesitant"
                    else:
                        tone_label = "reserved"
                        
            except Exception as e:
                logger.warning(f"Text tone analysis failed: {e}")
        
        return tone_score, tone_label
    
    def analyze_audio_prosody(self, audio_path: str) -> Optional[Dict]:
        """
        Extract prosodic features from audio (pitch variance, speaking rate, etc.).
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with prosodic features or None
        """
        if not LIBROSA_AVAILABLE:
            return None
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Extract features
            # Pitch (F0) using piptrack
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            # Speaking rate (zero crossing rate as proxy)
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            avg_zcr = np.mean(zcr)
            
            # Energy/intensity
            rms = librosa.feature.rms(y=y)[0]
            avg_energy = np.mean(rms)
            energy_variance = np.var(rms)
            
            # Pitch statistics
            if pitch_values:
                pitch_mean = np.mean(pitch_values)
                pitch_std = np.std(pitch_values)
                pitch_range = np.max(pitch_values) - np.min(pitch_values)
            else:
                pitch_mean = pitch_std = pitch_range = 0.0
            
            return {
                "pitch_mean": float(pitch_mean),
                "pitch_std": float(pitch_std),
                "pitch_range": float(pitch_range),
                "speaking_rate_proxy": float(avg_zcr),
                "energy_mean": float(avg_energy),
                "energy_variance": float(energy_variance)
            }
            
        except Exception as e:
            logger.error(f"Audio prosody analysis failed: {e}")
            return None
    
    def compute_prosody_tone_score(self, prosody: Dict) -> Tuple[float, str]:
        """
        Compute tone score from prosodic features.
        
        Args:
            prosody: Prosodic features dictionary
            
        Returns:
            (tone_score, tone_label)
        """
        # Normalize and score prosodic features
        tone_score = 50.0  # Base neutral score
        tone_label = "neutral"
        
        # High pitch variance + high energy = enthusiastic
        pitch_std = prosody.get("pitch_std", 0)
        energy_var = prosody.get("energy_variance", 0)
        speaking_rate = prosody.get("speaking_rate_proxy", 0)
        
        # Scoring heuristics (would be calibrated with labeled data)
        if pitch_std > 50 and energy_var > 0.01:
            tone_score += 20
            tone_label = "enthusiastic"
        elif pitch_std < 20 and energy_var < 0.005:
            tone_score -= 15
            tone_label = "monotone"
        
        if speaking_rate > 0.15:
            tone_score += 10  # Fast speaking = engaged
        elif speaking_rate < 0.05:
            tone_score -= 10  # Slow speaking = hesitant
        
        tone_score = max(0, min(100, tone_score))
        
        return tone_score, tone_label
    
    def analyze_tone(
        self,
        text: str,
        audio_path: Optional[str] = None
    ) -> Dict:
        """
        Comprehensive tone analysis from text and optionally audio.
        
        Args:
            text: Transcript text
            audio_path: Optional path to audio file
            
        Returns:
            Dictionary with tone_score, tone_label, and features
        """
        start_time = time.time()
        
        # Text-based tone analysis
        text_score, text_label = self.analyze_text_tone(text)
        
        result = {
            "tone_score": text_score,
            "tone_label": text_label,
            "text_tone_score": text_score,
            "text_tone_label": text_label,
            "audio_prosody": None,
            "audio_tone_score": None,
            "combined_analysis": False
        }
        
        # Audio prosody analysis if available
        if audio_path and LIBROSA_AVAILABLE:
            prosody = self.analyze_audio_prosody(audio_path)
            if prosody:
                audio_score, audio_label = self.compute_prosody_tone_score(prosody)
                
                # Combine text and audio scores (60% text, 40% audio)
                combined_score = 0.6 * text_score + 0.4 * audio_score
                
                # Determine combined label
                if combined_score > 75:
                    combined_label = "enthusiastic"
                elif combined_score > 60:
                    combined_label = "engaged"
                elif combined_score > 40:
                    combined_label = "calm"
                elif combined_score > 25:
                    combined_label = "reserved"
                else:
                    combined_label = "hesitant"
                
                result.update({
                    "tone_score": combined_score,
                    "tone_label": combined_label,
                    "audio_prosody": prosody,
                    "audio_tone_score": audio_score,
                    "audio_tone_label": audio_label,
                    "combined_analysis": True
                })
        
        processing_time = (time.time() - start_time) * 1000
        result["processing_time_ms"] = processing_time
        
        logger.debug(f"Tone analysis took {processing_time:.2f}ms")
        
        return result
