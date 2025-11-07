"""
Audio Processing Module with Whisper Speech-to-Text
Handles audio chunking, transcription, and confidence scoring
"""

import os
import tempfile
import logging
from typing import Tuple, List, Dict
from datetime import datetime
import asyncio
from pydub import AudioSegment

logger = logging.getLogger(__name__)

# Try to import Whisper, fall back to mock if not available
try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
    logger.info("✓ Whisper loaded successfully")
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("⚠️ Whisper not available - using mock transcription")

class AudioProcessor:
    def __init__(self, model_size: str = "base", chunk_duration: int = 30):
        """
        Initialize Audio Processor
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            chunk_duration: Duration of audio chunks in seconds for long files
        """
        self.model_size = model_size
        self.chunk_duration = chunk_duration
        self.model = None
        
        if WHISPER_AVAILABLE:
            try:
                self.model = whisper.load_model(model_size)
                logger.info(f"✓ Whisper model '{model_size}' loaded")
            except Exception as e:
                logger.error(f"✗ Failed to load Whisper model: {e}")
                WHISPER_AVAILABLE = False
    
    async def process_audio(
        self,
        audio_file_path: str,
        language: str = None,
        timeout: int = 300
    ) -> Dict:
        """
        Process audio file with Whisper STT
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (e.g., 'en'), None for auto-detect
            timeout: Maximum processing time in seconds
            
        Returns:
            Dict with transcription results
        """
        start_time = datetime.utcnow()
        
        try:
            # Get audio duration
            duration = await self._get_audio_duration(audio_file_path)
            logger.info(f"📊 Audio duration: {duration:.2f}s")
            
            # Determine if chunking is needed
            if duration > self.chunk_duration:
                logger.info(f"🔪 Audio too long, chunking into {self.chunk_duration}s segments")
                result = await self._process_chunked_audio(audio_file_path, language, timeout)
            else:
                result = await self._process_single_audio(audio_file_path, language, timeout)
            
            # Add processing metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result['duration_seconds'] = duration
            result['processing_time_seconds'] = processing_time
            result['stt_timestamp'] = datetime.utcnow()
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"⏱️ Audio processing timeout after {timeout}s")
            raise Exception(f"Audio processing timed out after {timeout}s")
        except Exception as e:
            logger.error(f"✗ Audio processing error: {e}")
            raise
    
    async def _process_single_audio(
        self,
        audio_file_path: str,
        language: str = None,
        timeout: int = 300
    ) -> Dict:
        """Process a single audio file without chunking"""
        try:
            if not WHISPER_AVAILABLE or self.model is None:
                # Mock transcription for testing
                return {
                    'original_text': "[Mock transcription - Whisper not available]",
                    'stt_confidence': 0.0,
                    'partial': False,
                    'chunk_count': 1,
                    'language': language or 'unknown'
                }
            
            # Run Whisper transcription
            logger.info("🎤 Running Whisper transcription...")
            
            options = {
                'task': 'transcribe',
                'fp16': torch.cuda.is_available()
            }
            if language:
                options['language'] = language
            
            result = await asyncio.wait_for(
                asyncio.to_thread(self.model.transcribe, audio_file_path, **options),
                timeout=timeout
            )
            
            # Extract results
            text = result.get('text', '').strip()
            language_detected = result.get('language', 'unknown')
            
            # Calculate average confidence from segments
            segments = result.get('segments', [])
            if segments:
                confidence = sum(seg.get('no_speech_prob', 0.0) for seg in segments) / len(segments)
                confidence = 1.0 - confidence  # Invert no_speech_prob to get confidence
            else:
                confidence = 0.5  # Default if no segments
            
            logger.info(f"✓ Transcription complete: {len(text)} characters, confidence: {confidence:.2f}")
            
            return {
                'original_text': text,
                'stt_confidence': round(confidence, 3),
                'partial': False,
                'chunk_count': 1,
                'language': language_detected
            }
            
        except Exception as e:
            logger.error(f"✗ Single audio processing error: {e}")
            raise
    
    async def _process_chunked_audio(
        self,
        audio_file_path: str,
        language: str = None,
        timeout: int = 300
    ) -> Dict:
        """Process long audio by splitting into chunks"""
        try:
            # Load audio with pydub
            audio = AudioSegment.from_file(audio_file_path)
            duration_ms = len(audio)
            chunk_duration_ms = self.chunk_duration * 1000
            
            chunks = []
            chunk_results = []
            
            # Split into chunks
            for i in range(0, duration_ms, chunk_duration_ms):
                chunk = audio[i:i + chunk_duration_ms]
                chunks.append(chunk)
            
            logger.info(f"🔪 Split audio into {len(chunks)} chunks")
            
            # Process each chunk
            temp_dir = tempfile.mkdtemp()
            try:
                for idx, chunk in enumerate(chunks):
                    chunk_path = os.path.join(temp_dir, f"chunk_{idx}.wav")
                    chunk.export(chunk_path, format="wav")
                    
                    try:
                        chunk_result = await self._process_single_audio(chunk_path, language, timeout // len(chunks))
                        chunk_results.append(chunk_result)
                        logger.info(f"✓ Chunk {idx + 1}/{len(chunks)} processed")
                    except Exception as e:
                        logger.warning(f"⚠️ Chunk {idx + 1} failed: {e}")
                        chunk_results.append({
                            'original_text': '',
                            'stt_confidence': 0.0
                        })
            finally:
                # Cleanup temp files
                for f in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, f))
                os.rmdir(temp_dir)
            
            # Merge results
            merged_text = ' '.join(r['original_text'] for r in chunk_results if r['original_text'])
            avg_confidence = sum(r['stt_confidence'] for r in chunk_results) / len(chunk_results)
            
            # Mark as partial if any chunks failed
            all_chunks_succeeded = all(r['original_text'] for r in chunk_results)
            
            logger.info(f"✓ Chunked processing complete: {len(chunk_results)} chunks merged")
            
            return {
                'original_text': merged_text,
                'stt_confidence': round(avg_confidence, 3),
                'partial': not all_chunks_succeeded,
                'chunk_count': len(chunks),
                'language': language or 'unknown'
            }
            
        except Exception as e:
            logger.error(f"✗ Chunked audio processing error: {e}")
            raise
    
    async def _get_audio_duration(self, audio_file_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            audio = AudioSegment.from_file(audio_file_path)
            return len(audio) / 1000.0  # Convert ms to seconds
        except Exception as e:
            logger.warning(f"⚠️ Could not determine audio duration: {e}")
            return 0.0
    
    def validate_audio_file(self, file_path: str, max_size_mb: int = 50) -> Tuple[bool, str]:
        """
        Validate audio file
        
        Returns:
            (is_valid, error_message)
        """
        try:
            # Check file exists
            if not os.path.exists(file_path):
                return False, "Audio file not found"
            
            # Check file size
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > max_size_mb:
                return False, f"Audio file too large: {file_size_mb:.1f}MB (max {max_size_mb}MB)"
            
            # Try to load with pydub to validate format
            try:
                audio = AudioSegment.from_file(file_path)
                if len(audio) == 0:
                    return False, "Audio file is empty"
            except Exception as e:
                return False, f"Invalid audio format: {str(e)}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

# Global processor instance
_audio_processor = None

def get_audio_processor(model_size: str = "base", chunk_duration: int = 30) -> AudioProcessor:
    """Get or create audio processor instance"""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor(model_size, chunk_duration)
    return _audio_processor
