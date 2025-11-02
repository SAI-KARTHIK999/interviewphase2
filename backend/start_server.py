#!/usr/bin/env python3
"""
Simple startup script for the Flask server with better error handling.
"""

import os
import sys

def main():
    print("Starting AI Interview Bot Backend Server...")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")
    
    try:
        # Import the app
        from app import app
        
        print("Flask app imported successfully")
        print("Server will be available at: http://localhost:5001")
        print("Available endpoints:")
        print("   - GET  /                    (Homepage)")
        print("   - GET  /api/status         (Status check)")
        print("   - GET  /api/health         (Health check)")  
        print("   - POST /api/interview/video (Video interview)")
        print("\nStarting server...")
        print("Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start the server
        port = int(os.environ.get('PORT', 5001))
        app.run(debug=True, port=port, host='0.0.0.0')
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Try installing missing dependencies:")
        print("   pip install flask flask-cors pymongo werkzeug")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()