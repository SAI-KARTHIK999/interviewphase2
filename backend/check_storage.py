import os
import json
from datetime import datetime

def check_mongodb():
    """Check MongoDB storage"""
    print("=" * 60)
    print("CHECKING MONGODB STORAGE")
    print("=" * 60)
    try:
        from pymongo import MongoClient
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.server_info()
        
        db = client['interview_db']
        interviews = db['interviews']
        
        count = interviews.count_documents({})
        print(f"✓ MongoDB connection successful")
        print(f"✓ Total documents in 'interviews' collection: {count}")
        
        if count > 0:
            print("\n--- Recent Interviews (Last 5) ---")
            recent = list(interviews.find({}, {'_id': 0}).sort('timestamp', -1).limit(5))
            for idx, doc in enumerate(recent, 1):
                print(f"\n{idx}. ID: {doc.get('id', 'N/A')}")
                print(f"   Timestamp: {doc.get('timestamp', 'N/A')}")
                print(f"   Question: {doc.get('question', 'N/A')}")
                print(f"   Score: {doc.get('score', 0)}")
                print(f"   Video: {doc.get('video_filename', 'N/A')}")
                print(f"   Transcription: {doc.get('transcribed_text', 'N/A')[:100]}...")
        
        return True
    except Exception as e:
        print(f"✗ MongoDB check failed: {e}")
        return False

def check_json_storage():
    """Check JSON file storage"""
    print("\n" + "=" * 60)
    print("CHECKING JSON FILE STORAGE")
    print("=" * 60)
    
    json_file = os.path.join(os.path.dirname(__file__), 'data', 'interview_responses.json')
    
    if not os.path.exists(json_file):
        print(f"✗ JSON file not found at: {json_file}")
        return False
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            lines = [line for line in f if line.strip()]
        
        count = len(lines)
        file_size = os.path.getsize(json_file) / 1024
        
        print(f"✓ JSON file found: {json_file}")
        print(f"✓ File size: {file_size:.2f} KB")
        print(f"✓ Total records: {count}")
        
        if count > 0:
            print("\n--- Recent Interviews (Last 5) ---")
            for idx, line in enumerate(lines[-5:], 1):
                try:
                    doc = json.loads(line)
                    print(f"\n{idx}. ID: {doc.get('id', 'N/A')}")
                    print(f"   Timestamp: {doc.get('timestamp', 'N/A')}")
                    print(f"   Question: {doc.get('question', 'N/A')}")
                    print(f"   Score: {doc.get('score', 0)}")
                    print(f"   Video: {doc.get('video_filename', 'N/A')}")
                    print(f"   Transcription: {doc.get('transcribed_text', 'N/A')[:100]}...")
                except json.JSONDecodeError as e:
                    print(f"✗ Error parsing line {idx}: {e}")
        
        return True
    except Exception as e:
        print(f"✗ JSON file check failed: {e}")
        return False

def check_uploads():
    """Check uploaded video files"""
    print("\n" + "=" * 60)
    print("CHECKING UPLOADED VIDEO FILES")
    print("=" * 60)
    
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    
    if not os.path.exists(upload_dir):
        print(f"✗ Upload directory not found: {upload_dir}")
        return False
    
    files = [f for f in os.listdir(upload_dir) if f.endswith(('.webm', '.mp4', '.avi'))]
    
    if not files:
        print(f"✓ Upload directory exists but no video files found")
        return True
    
    print(f"✓ Upload directory: {upload_dir}")
    print(f"✓ Total video files: {len(files)}")
    
    total_size = sum(os.path.getsize(os.path.join(upload_dir, f)) for f in files)
    print(f"✓ Total size: {total_size / (1024*1024):.2f} MB")
    
    print("\n--- Recent Videos (Last 5) ---")
    for idx, filename in enumerate(sorted(files, reverse=True)[:5], 1):
        filepath = os.path.join(upload_dir, filename)
        file_size = os.path.getsize(filepath) / (1024*1024)
        mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        print(f"{idx}. {filename} ({file_size:.2f} MB) - Modified: {mod_time}")
    
    return True

if __name__ == "__main__":
    print("\n" + "🔍 AI INTERVIEW DATA STORAGE CHECK" + "\n")
    
    mongo_ok = check_mongodb()
    json_ok = check_json_storage()
    uploads_ok = check_uploads()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"MongoDB Storage:  {'✓ WORKING' if mongo_ok else '✗ NOT AVAILABLE'}")
    print(f"JSON Storage:     {'✓ WORKING' if json_ok else '✗ NOT AVAILABLE'}")
    print(f"Video Uploads:    {'✓ WORKING' if uploads_ok else '✗ NOT AVAILABLE'}")
    
    if not (mongo_ok or json_ok):
        print("\n⚠️  WARNING: No storage method is working!")
    elif mongo_ok:
        print("\n✓ Data is being saved to MongoDB")
    elif json_ok:
        print("\n✓ Data is being saved to JSON file (MongoDB unavailable)")
    
    print("\n")
