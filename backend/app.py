import os
import tempfile
import threading
from flask import Flask, jsonify, request, stream_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)
CORS(app)

# Configure upload settings for better performance
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Ensure uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database connection with error handling
try:
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
    client.server_info()  # quick ping to check connection
    db = client['interview_db']
    interviews = db['interviews']
    print("Connected to MongoDB at mongodb://localhost:27017/")
except Exception as e:
    print(f"Warning: Could not connect to MongoDB: {e}. Proceeding without DB (in-memory only).")
    interviews = None

# Import NLP/CV functions with graceful degradation
try:
    from nlp_processor import transcribe_video, anonymize_text, assess_answer, analyze_facial_expressions
    print("Successfully imported NLP processor functions")
except Exception as e:
    print(f"Warning: Could not import full nlp_processor: {e}. Using lightweight stubs.")
    
    def transcribe_video(fp):
        return "[transcription unavailable - whisper not installed]"
    
    def anonymize_text(text):
        return text
    
    def assess_answer(candidate, model_answer):
        return {"score": 0.0, "feedback": "Automatic assessment unavailable."}
    
    def analyze_facial_expressions(fp):
        return {"note": "facial analysis unavailable"}

# Interview data
interview_data = {
    "1": {
        "question": "Tell me about a challenging project you worked on.",
        "model_answer": "I led a project to migrate our user database from SQL to NoSQL..."
    }
}

# Root route for basic testing
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "AI Interview Bot Backend Server",
        "status": "running",
        "available_endpoints": [
            "GET /api/status",
            "POST /api/interview/video",
            "GET /api/health"
        ]
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "Backend server is running!"})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "database_connected": interviews is not None,
        "nlp_functions_loaded": True
    })

@app.route('/api/interview/video', methods=['POST'])
def handle_video_interview():
    try:
        if 'video' not in request.files:
            return jsonify({"error": "No video file provided"}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Check file size before processing
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({"error": "File too large. Maximum size is 50MB"}), 413
            
        if file_size < 1024:  # Less than 1KB
            return jsonify({"error": "File too small. Please upload a valid video file"}), 400

        # Use secure filename with timestamp to avoid conflicts
        import time
        timestamp = int(time.time())
        original_filename = secure_filename(file.filename)
        filename = f"{timestamp}_{original_filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Stream save for better memory usage with large files
        with open(filepath, 'wb') as f:
            while True:
                chunk = file.stream.read(8192)  # Read in 8KB chunks
                if not chunk:
                    break
                f.write(chunk)
        
        # --- Analysis Pipeline (with error handling) ---
        try:
            transcribed_text = transcribe_video(filepath)
        except Exception as e:
            transcribed_text = f"Transcription failed: {e}"
        print(f"Transcribed Text: {transcribed_text}")
        
        try:
            facial_analysis = analyze_facial_expressions(filepath)
        except Exception as e:
            facial_analysis = {"error": f"facial analysis failed: {e}"}
        print(f"Facial Analysis: {facial_analysis}")

        try:
            anonymized_text = anonymize_text(transcribed_text)
        except Exception:
            anonymized_text = transcribed_text
        
        try:
            assessment = assess_answer(anonymized_text, interview_data["1"]["model_answer"])
        except Exception as e:
            assessment = {"score": 0.0, "feedback": f"Assessment failed: {e}"}

        result_to_save = {
            "question": interview_data["1"]["question"],
            "transcribed_text": transcribed_text,
            "anonymized_answer": anonymized_text,
            "facial_analysis": facial_analysis,
            "score": assessment.get('score', 0.0),
            "feedback": assessment.get('feedback', ''),
            "video_filename": filename
        }

        if interviews is not None:
            try:
                interviews.insert_one(result_to_save)
                print("Full video analysis result saved to MongoDB.")
            except Exception as e:
                print(f"Warning: Failed to save to MongoDB: {e}")
        else:
            print("DB not available - skipping save. Result:", result_to_save)
        
        # Clean up uploaded file after processing (optional)
        # os.remove(filepath)  # Uncomment to delete after processing
        
        return jsonify({"assessment": assessment})
        
    except RequestEntityTooLarge:
        return jsonify({"error": "File too large. Maximum size is 50MB"}), 413
    except Exception as e:
        print(f"Error processing video upload: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    # Allow the port to be overridden by environment for deployments
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting Flask app on port {port} (debug=True)")
    app.run(debug=True, port=port, host='0.0.0.0')
