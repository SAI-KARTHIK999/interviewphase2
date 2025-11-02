import os
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import ffmpeg
import whisper
import cv2  # OpenCV for video processing
from deepface import DeepFace # The DeepFace library
import subprocess

# --- Load Models ---
nlp = spacy.load("en_core_web_sm")
whisper_model = whisper.load_model("medium")

# --- NEW Facial Analysis Function ---
def analyze_facial_expressions(video_filepath):
    """
    Analyzes the dominant emotion in a video, frame by frame.
    """
    print("Starting facial expression analysis...")
    emotions = {}
    
    # Open the video file
    cap = cv2.VideoCapture(video_filepath)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Analyze one frame per second to be efficient
        if frame_count % int(frame_rate) == 0:
            try:
                # The core analysis function from DeepFace
                analysis = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=True)
                
                # DeepFace returns a list of faces; we'll use the first one
                if isinstance(analysis, list) and len(analysis) > 0:
                    dominant_emotion = analysis[0]['dominant_emotion']
                    emotions[dominant_emotion] = emotions.get(dominant_emotion, 0) + 1

            except Exception as e:
                # This exception is often thrown if no face is detected in the frame
                pass
        
        frame_count += 1

    cap.release()
    print("Facial analysis complete.")
    return emotions


# --- Transcription Function ---
def transcribe_video(video_filepath):
    """
    Enhanced video transcription with better audio preprocessing and error handling.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def preprocess_audio(input_path, output_path):
        """Preprocess audio to improve transcription quality."""
        try:
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file if it exists
                '-i', input_path,
                '-ac', '1',  # Convert to mono
                '-ar', '16000',  # Sample rate 16kHz
                '-acodec', 'pcm_s16le',  # PCM 16-bit little-endian
                '-af', 'highpass=f=300,lowpass=f=3000,volume=2.0,compand=attacks=0:points=-80/-80|-30/-10|0/0',  # Noise reduction and normalization
                '-f', 'wav',
                output_path
            ]
            
            logger.info(f"Running audio preprocessing command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                logger.error("FFmpeg output file is empty or not created")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error in audio preprocessing: {str(e)}")
            return False

    try:
        logger.info(f"Starting transcription for: {video_filepath}")
        
        # Verify input file
        if not os.path.exists(video_filepath):
            raise FileNotFoundError(f"Video file not found: {video_filepath}")
            
        file_size = os.path.getsize(video_filepath)
        if file_size == 0:
            raise ValueError("Video file is empty (0 bytes)")
            
        logger.info(f"Processing video file (size: {file_size/1024/1024:.2f} MB)")
        
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, "audio.wav")
        
        # Extract and preprocess audio
        logger.info("Extracting and preprocessing audio...")
        if not preprocess_audio(video_filepath, audio_path):
            raise RuntimeError("Audio preprocessing failed")
            
        logger.info("Audio preprocessing completed successfully")
        
        # Load model with optimized settings
        logger.info("Initializing Whisper model...")
        model = whisper.load_model("medium")
        
        # Transcribe with optimized parameters
        logger.info("Starting transcription...")
        result = model.transcribe(
            audio_path,
            language='en',
            fp16=False,  # Disable mixed precision for better compatibility
            verbose=False,
            temperature=0.2,  # Lower temperature for more deterministic output
            best_of=3,  # Take best of 3 samples
            beam_size=5  # Use beam search with 5 beams
        )
        
        transcribed_text = result.get("text", "").strip()
        
        if not transcribed_text:
            raise ValueError("Transcription returned empty result")
            
        logger.info(f"Transcription successful. Length: {len(transcribed_text)} characters")
        return transcribed_text
        
    except Exception as e:
        error_msg = f"Transcription failed: {str(e)}"
        logger.error(error_msg)
        return f"[Transcription Error: {str(e)}]"
        
    finally:
        # Cleanup
        try:
            if 'audio_path' in locals() and os.path.exists(audio_path):
                os.remove(audio_path)
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception as e:
            logger.warning(f"Cleanup failed: {str(e)}")
        
        logger.info("Transcription process completed")


# --- Text Analysis Functions ---
def anonymize_text(text):
    """Enhanced text anonymization with better entity recognition and handling."""
    if not text or not isinstance(text, str):
        return text

    doc = nlp(text)
    anonymized = []
    last_end = 0
    
    # Sort entities by start position (in reverse to handle replacements correctly)
    ents = sorted(doc.ents, key=lambda x: x.start_char)
    
    for ent in ents:
        # Add text before the entity
        anonymized.append(text[last_end:ent.start_char])
        
        # Replace entity based on its type
        if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "FAC", "PRODUCT", "EVENT", "WORK_OF_ART", "LAW", "LANGUAGE"]:
            anonymized.append(f"[{ent.label_}]")
        elif ent.label_ == "DATE":
            anonymized.append("[DATE]")
        elif ent.label_ == "TIME":
            anonymized.append("[TIME]")
        elif ent.label_ == "PERCENT":
            anonymized.append("[PERCENT]")
        elif ent.label_ == "MONEY":
            anonymized.append("[MONEY]")
        elif ent.label_ == "QUANTITY":
            anonymized.append("[QUANTITY]")
        else:
            anonymized.append(ent.text)
            
        last_end = ent.end_char
    
    # Add remaining text
    anonymized.append(text[last_end:])
    return "".join(anonymized)

def assess_answer(candidate_answer, model_answer):
    # (Code for assessment is unchanged)
    vectorizer = TfidfVectorizer().fit_transform([candidate_answer, model_answer])
    vectors = vectorizer.toarray()
    similarity_score = cosine_similarity(vectors)[0, 1]
    feedback = ""
    if similarity_score > 0.6:
        feedback = "Excellent! Your answer is comprehensive."
    elif similarity_score > 0.3:
        feedback = "Good answer, but could add more detail."
    else:
        feedback = "Your answer seems to be missing some key information."
    return {"score": round(similarity_score, 2), "feedback": feedback}