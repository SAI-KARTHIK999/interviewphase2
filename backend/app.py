import os
import tempfile
import threading
import json
from datetime import datetime, timedelta
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

# Ensure uploads and data directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_FOLDER, exist_ok=True)
JSON_STORAGE_FILE = os.path.join(DATA_FOLDER, 'interview_responses.json')
DELETION_LOG_FILE = os.path.join(DATA_FOLDER, 'deletion_log.json')

# Data retention policy constants
RETENTION_DAYS = 30
RETENTION_SECONDS = RETENTION_DAYS * 24 * 60 * 60  # 2592000 seconds

# Initialize database connection with error handling
try:
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.server_info()  # quick ping to check connection
    db = client['interview_db']
    interviews = db['interviews']
    deletion_log = db['deletion_log']
    user_consent_logs = db['user_consent_logs']
    
    print("✓ Connected to MongoDB at mongodb://localhost:27017/")
    print(f"✓ Using database: interview_db, collection: interviews")
    
    # Setup TTL index for automatic deletion after 30 days
    try:
        # Create TTL index on createdAt field
        interviews.create_index("createdAt", expireAfterSeconds=RETENTION_SECONDS)
        print(f"✓ TTL index created: Data auto-deletes after {RETENTION_DAYS} days")
    except Exception as idx_error:
        print(f"⚠️  TTL index warning: {idx_error}")
    
    # Setup indexes for user_consent_logs collection
    try:
        user_consent_logs.create_index("user_id")
        user_consent_logs.create_index("timestamp")
        user_consent_logs.create_index([("user_id", 1), ("timestamp", -1)])
        print("✓ Consent logs indexes created")
    except Exception as idx_error:
        print(f"⚠️  Consent logs index warning: {idx_error}")
except Exception as e:
    print(f"✗ Warning: Could not connect to MongoDB: {e}")
    print(f"✓ Fallback: Using JSON file storage at {JSON_STORAGE_FILE}")
    interviews = None
    deletion_log = None
    user_consent_logs = None

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

@app.route('/api/consent', methods=['POST'])
def handle_consent():
    """Handle user consent before interview session begins"""
    try:
        data = request.get_json()
        
        # Extract consent data
        user_id = data.get('user_id', f"user_{int(datetime.utcnow().timestamp())}")
        allow_audio = data.get('allow_audio', False)
        allow_video = data.get('allow_video', False)
        allow_storage = data.get('allow_storage', False)
        session_mode = data.get('session_mode', 'practice')  # 'record' or 'practice'
        
        # Create consent record
        consent_record = {
            "consent_id": f"consent_{int(datetime.utcnow().timestamp())}_{os.urandom(4).hex()}",
            "user_id": user_id,
            "allow_audio": allow_audio,
            "allow_video": allow_video,
            "allow_storage": allow_storage,
            "session_mode": session_mode,
            "timestamp": datetime.utcnow(),
            "ip_address": request.remote_addr,
            "user_agent": request.headers.get('User-Agent', 'Unknown')
        }
        
        # Store consent in MongoDB
        if user_consent_logs is not None:
            try:
                result = user_consent_logs.insert_one(consent_record.copy())
                print(f"✓ Consent logged: {consent_record['consent_id']} for user {user_id}")
                consent_record['_id'] = str(result.inserted_id)
            except Exception as e:
                print(f"✗ Failed to log consent to MongoDB: {e}")
        else:
            # Fallback to JSON file
            consent_log_file = os.path.join(DATA_FOLDER, 'consent_logs.json')
            try:
                with open(consent_log_file, 'a', encoding='utf-8') as f:
                    json.dump({
                        **consent_record,
                        'timestamp': consent_record['timestamp'].isoformat()
                    }, f, ensure_ascii=False)
                    f.write('\n')
                print(f"✓ Consent logged to JSON file for user {user_id}")
            except Exception as e:
                print(f"✗ Failed to log consent to JSON: {e}")
        
        # Determine session mode based on consent
        if not allow_audio and not allow_video:
            session_mode = 'practice'
        elif allow_audio or allow_video:
            session_mode = 'record'
        
        return jsonify({
            "status": "success",
            "consent_id": consent_record['consent_id'],
            "user_id": user_id,
            "session_mode": session_mode,
            "message": f"Consent recorded. Session mode: {session_mode}",
            "permissions": {
                "audio": allow_audio,
                "video": allow_video,
                "storage": allow_storage
            }
        }), 200
        
    except Exception as e:
        print(f"Error handling consent: {str(e)}")
        return jsonify({"error": f"Consent processing failed: {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    storage_info = "MongoDB" if interviews is not None else "JSON File"
    return jsonify({
        "status": "healthy",
        "database_connected": interviews is not None,
        "storage_type": storage_info,
        "nlp_functions_loaded": True
    })

@app.route('/api/interview/history', methods=['GET'])
def get_interview_history():
    """Retrieve all stored interview responses with remaining days counter"""
    try:
        if interviews is not None:
            # Get from MongoDB
            responses = list(interviews.find({}, {'_id': 0}).sort('createdAt', -1).limit(50))
            
            # Add remaining days counter to each response
            for resp in responses:
                if 'createdAt' in resp:
                    created_date = resp['createdAt']
                    expiry_date = created_date + timedelta(days=RETENTION_DAYS)
                    remaining_days = (expiry_date - datetime.utcnow()).days
                    resp['days_until_deletion'] = max(0, remaining_days)
                    resp['deletion_date'] = expiry_date.isoformat()
                else:
                    resp['days_until_deletion'] = 'N/A'
                    resp['deletion_date'] = 'N/A'
            
            return jsonify({
                "count": len(responses), 
                "data": responses, 
                "source": "MongoDB",
                "retention_policy": f"Auto-deletion after {RETENTION_DAYS} days"
            })
        else:
            # Get from JSON file
            if os.path.exists(JSON_STORAGE_FILE):
                with open(JSON_STORAGE_FILE, 'r', encoding='utf-8') as f:
                    responses = [json.loads(line) for line in f if line.strip()]
                return jsonify({"count": len(responses), "data": responses, "source": "JSON"})
            else:
                return jsonify({"count": 0, "data": [], "source": "JSON"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/data/delete', methods=['POST'])
def delete_user_data():
    """Manual data deletion endpoint - triggered by 'Delete my data now' command"""
    try:
        data = request.get_json()
        delete_command = data.get('command', '').strip().lower()
        user_id = data.get('user_id') or data.get('id')
        
        # Validate delete command
        if delete_command != 'delete my data now':
            return jsonify({
                "error": "Invalid command",
                "hint": "Type exactly: 'Delete my data now' to confirm deletion"
            }), 400
        
        if not user_id:
            return jsonify({"error": "user_id or id is required"}), 400
        
        deleted_count = 0
        deleted_files = []
        
        if interviews is not None:
            # Find documents to delete
            docs_to_delete = list(interviews.find({"id": user_id}))
            
            if not docs_to_delete:
                return jsonify({
                    "status": "not_found",
                    "message": "No data found for the provided ID"
                }), 404
            
            # Delete video files
            for doc in docs_to_delete:
                # Prefer stored path; otherwise reconstruct from filename
                video_path = doc.get('video_filepath') or (
                    os.path.join(app.config['UPLOAD_FOLDER'], doc.get('video_filename', '')) if doc.get('video_filename') else None
                )
                if video_path and os.path.exists(video_path):
                    try:
                        os.remove(video_path)
                        deleted_files.append(video_path)
                        print(f"✓ Deleted video file: {video_path}")
                    except Exception as e:
                        print(f"✗ Failed to delete video: {e}")
            
            # Delete MongoDB documents
            result = interviews.delete_many({"id": user_id})
            deleted_count = result.deleted_count
            
            # Log the deletion
            if deletion_log is not None:
                log_entry = {
                    "deleted_at": datetime.utcnow(),
                    "user_id": user_id,
                    "deleted_count": deleted_count,
                    "deleted_files": deleted_files,
                    "deletion_type": "manual",
                    "command": delete_command
                }
                deletion_log.insert_one(log_entry)
                print(f"✓ Deletion logged to MongoDB")
        else:
            # JSON file deletion (fallback)
            if os.path.exists(JSON_STORAGE_FILE):
                with open(JSON_STORAGE_FILE, 'r', encoding='utf-8') as f:
                    all_data = [json.loads(line) for line in f if line.strip()]
                
                # Filter out matching records
                filtered_data = [d for d in all_data if d.get('id') != user_id]
                deleted_count = len(all_data) - len(filtered_data)
                
                # Rewrite file
                with open(JSON_STORAGE_FILE, 'w', encoding='utf-8') as f:
                    for record in filtered_data:
                        json.dump(record, f, ensure_ascii=False)
                        f.write('\n')
                
                # Log to file
                log_entry = {
                    "deleted_at": datetime.utcnow().isoformat(),
                    "user_id": user_id,
                    "deleted_count": deleted_count,
                    "deletion_type": "manual"
                }
                with open(DELETION_LOG_FILE, 'a', encoding='utf-8') as f:
                    json.dump(log_entry, f)
                    f.write('\n')
        
        return jsonify({
            "status": "success",
            "message": "Your interview data has been permanently deleted",
            "deleted_records": deleted_count,
            "deleted_files": len(deleted_files),
            "deleted_at": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error in deletion: {str(e)}")
        return jsonify({"error": f"Deletion failed: {str(e)}"}), 500

@app.route('/api/data/retention-info', methods=['GET'])
def get_retention_info():
    """Get data retention policy information"""
    return jsonify({
        "retention_policy": {
            "auto_deletion_days": RETENTION_DAYS,
            "description": f"All interview data is automatically deleted after {RETENTION_DAYS} days",
            "data_stored": [
                "Video recordings",
                "Audio transcriptions",
                "Facial analysis results",
                "Assessment scores"
            ],
            "manual_deletion": {
                "command": "Delete my data now",
                "endpoint": "/api/data/delete",
                "method": "POST",
                "required_fields": ["command", "id or user_id"]
            }
        },
        "privacy_compliance": "GDPR & Data Minimization"
    })

@app.route('/api/interview/video', methods=['POST'])
def handle_video_interview():
    try:
        print("\n" + "="*50)
        print("📹 Video Upload Request Received")
        print("="*50)
        
        # --- Consent & data handling flags (required) ---
        consent_record = (request.form.get('consent_record', 'false').lower() == 'true')
        consent_analyze = (request.form.get('consent_analyze', 'false').lower() == 'true')
        opt_in_save = (request.form.get('opt_in_data_save', 'false').lower() == 'true')
        opt_in_share = (request.form.get('opt_in_data_share', 'false').lower() == 'true')
        consent_version = request.form.get('consent_version', 'v1')
        consent_id = request.form.get('consent_id', None)
        user_id_form = request.form.get('user_id', None)
        # --- Question context (optional but recommended) ---
        question_id = request.form.get('question_id')
        question_text = request.form.get('question_text')
        
        print(f"Consent Record: {consent_record}")
        print(f"Consent Analyze: {consent_analyze}")
        print(f"Opt-in Save: {opt_in_save}")
        print(f"Consent ID: {consent_id}")
        print(f"User ID: {user_id_form}")
        print(f"Question ID: {question_id}")
        print(f"Question Text: {question_text}")

        if not (consent_record and consent_analyze):
            print("❌ Consent validation failed")
            return jsonify({
                "error": "Consent required",
                "hint": "You must consent to recording and analysis to proceed."
            }), 400

        if 'video' not in request.files:
            print("❌ No video file in request")
            print("Available form fields:", list(request.form.keys()))
            print("Available files:", list(request.files.keys()))
            return jsonify({"error": "No video file provided"}), 400
        
        file = request.files['video']
        if file.filename == '':
            print("❌ Empty filename")
            return jsonify({"error": "No selected file"}), 400
        
        print(f"✓ Video file received: {file.filename}")

        # Check file size before processing
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        print(f"File size: {file_size / 1024 / 1024:.2f} MB")
        
        if file_size > app.config['MAX_CONTENT_LENGTH']:
            print("❌ File too large")
            return jsonify({"error": "File too large. Maximum size is 50MB"}), 413
            
        if file_size < 1024:  # Less than 1KB
            print("❌ File too small")
            return jsonify({"error": "File too small. Please upload a valid video file"}), 400

        # Use secure filename with timestamp to avoid conflicts
        import time
        timestamp = int(time.time())
        original_filename = secure_filename(file.filename)
        filename = f"{timestamp}_{original_filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        print(f"Saving to: {filepath}")
        
        # Stream save for better memory usage with large files
        try:
            with open(filepath, 'wb') as f:
                while True:
                    chunk = file.stream.read(8192)  # Read in 8KB chunks
                    if not chunk:
                        break
                    f.write(chunk)
            print(f"✓ File saved successfully")
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return jsonify({"error": f"Failed to save file: {str(e)}"}), 500
        
        # --- Analysis Pipeline (with error handling) ---
        print("\n🔍 Starting analysis pipeline...")
        try:
            print("  - Transcribing video...")
            transcribed_text = transcribe_video(filepath)
            print(f"  ✓ Transcription: {transcribed_text[:100]}..." if len(transcribed_text) > 100 else f"  ✓ Transcription: {transcribed_text}")
        except Exception as e:
            transcribed_text = f"Transcription failed: {e}"
            print(f"  ⚠️ Transcription warning: {e}")
        
        try:
            print("  - Analyzing facial expressions...")
            facial_analysis = analyze_facial_expressions(filepath)
            print(f"  ✓ Facial analysis complete")
        except Exception as e:
            facial_analysis = {"error": f"facial analysis failed: {e}"}
            print(f"  ⚠️ Facial analysis warning: {e}")

        try:
            anonymized_text = anonymize_text(transcribed_text)
        except Exception:
            anonymized_text = transcribed_text
        
        try:
            print("  - Assessing answer...")
            assessment = assess_answer(anonymized_text, interview_data["1"]["model_answer"])
            print(f"  ✓ Assessment complete: Score = {assessment.get('score', 0.0)}")
        except Exception as e:
            assessment = {"score": 0.0, "feedback": f"Assessment failed: {e}"}
            print(f"  ⚠️ Assessment warning: {e}")

        # Calculate deletion date
        created_at = datetime.utcnow()
        deletion_date = created_at + timedelta(days=RETENTION_DAYS)
        
        print(f"\n💾 Storage decision: {'SAVE' if opt_in_save else 'NO SAVE (immediate delete)'}")
        
        result_to_save = {
            "id": f"{timestamp}_{os.urandom(4).hex()}",
            "createdAt": created_at,  # For TTL index
            "timestamp": created_at.isoformat(),
            "deletion_date": deletion_date.isoformat(),
            "days_until_deletion": RETENTION_DAYS,
            "question": interview_data["1"]["question"],
            # Store BOTH raw transcription and anonymized version
            "transcribed_text": transcribed_text,      # ✅ Raw STT output (original speech)
            "anonymized_answer": anonymized_text,      # ✅ Tokenized/anonymized version
            "answer": anonymized_text,                 # ✅ Canonical answer field for simple queries
            "facial_analysis": facial_analysis,
            "score": assessment.get('score', 0.0),
            "feedback": assessment.get('feedback', ''),
            "video_filename": filename,
            "video_filepath": filepath,
            "video_mime": file.mimetype if hasattr(file, 'mimetype') else 'video/webm',
            "video_size_bytes": file_size,
            # question context
            "question_id": question_id or "1",
            "question": question_text or interview_data["1"]["question"],
            # Link to consent record
            "consent_id": consent_id,
            "user_id": user_id_form,
            "consent": {
                "record": consent_record,
                "analyze": consent_analyze,
                "opt_in_save": opt_in_save,
                "opt_in_share": opt_in_share,
                "version": consent_version
            }
        }

        saved_successfully = False
        storage_method = None
        
        if opt_in_save:
            # Try MongoDB first
            if interviews is not None:
                try:
                    result = interviews.insert_one(result_to_save.copy())
                    saved_successfully = True
                    storage_method = "MongoDB"
                    print(f"✓ Successfully saved to MongoDB with ID: {result.inserted_id}")
                    
                    # Verify the save
                    verify = interviews.find_one({"id": result_to_save["id"]})
                    if verify:
                        print(f"✓ Verified: Document exists in MongoDB")
                    else:
                        print(f"✗ Warning: Document not found in verification")
                except Exception as e:
                    print(f"✗ MongoDB save failed: {e}")
                    print(f"→ Attempting JSON fallback...")
            
            # Fallback to JSON file storage
            if not saved_successfully:
                try:
                    with open(JSON_STORAGE_FILE, 'a', encoding='utf-8') as f:
                        json.dump(result_to_save, f, ensure_ascii=False)
                        f.write('\n')
                    saved_successfully = True
                    storage_method = "JSON"
                    print(f"✓ Successfully saved to JSON file: {JSON_STORAGE_FILE}")
                    
                    # Verify the save
                    if os.path.exists(JSON_STORAGE_FILE):
                        file_size_kb = os.path.getsize(JSON_STORAGE_FILE) / 1024
                        print(f"✓ Verified: JSON file size: {file_size_kb:.2f} KB")
                except Exception as e:
                    print(f"✗ JSON save also failed: {e}")
                    storage_method = "FAILED"
        else:
            # Do not persist; delete file immediately after analysis
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"✓ Deleted uploaded file immediately due to no-save consent: {filename}")
            except Exception as e:
                print(f"✗ Failed to delete temporary file: {e}")
        
        if opt_in_save and not saved_successfully:
            print(f"❍ CRITICAL: Data not saved anywhere though opt_in_save was true!")
            print(f"Data attempted to save: {result_to_save}")
        
        response_data = {
            "assessment": assessment,
            "saved_record": {
                "question_id": result_to_save.get("question_id"),
                "question": result_to_save.get("question"),
                "timestamp": result_to_save.get("timestamp"),
                "video_filename": result_to_save.get("video_filename"),
                "id": result_to_save.get("id") if saved_successfully else None
            },
            "storage": {
                "saved": saved_successfully,
                "method": storage_method,
                "id": result_to_save["id"] if saved_successfully else None
            },
            "consent": result_to_save["consent"],
            "data_retention": {
                "auto_deletion_days": RETENTION_DAYS,
                "deletion_date": result_to_save['deletion_date'] if saved_successfully else None,
                "message": (f"Your data will be automatically deleted after {RETENTION_DAYS} days." if saved_successfully 
                            else "Your data was not saved per your consent; video file has been deleted.")
            }
        }
        
        print(f"\n✅ SUCCESS: Returning response to frontend")
        print(f"Assessment score: {assessment.get('score', 0.0)}")
        print(f"Storage saved: {saved_successfully}")
        print("="*50 + "\n")
        
        return jsonify(response_data)
        
    except RequestEntityTooLarge:
        print("❌ RequestEntityTooLarge error")
        return jsonify({"error": "File too large. Maximum size is 50MB"}), 413
    except Exception as e:
        print(f"\n❌ ERROR processing video upload:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*50 + "\n")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    # Allow the port to be overridden by environment for deployments
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting Flask app on port {port} (debug=True)")
    app.run(debug=True, port=port, host='0.0.0.0')
