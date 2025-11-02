#!/usr/bin/env python3
"""
Simple script to run both frontend and backend servers
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def main():
    print("AI Interview Bot - Starting both servers")
    print("=" * 40)
    
    base_dir = Path(__file__).parent
    backend_dir = base_dir / "backend"
    frontend_dir = base_dir / "frontend"
    
    # Start backend in a new window
    print("Starting backend server...")
    backend_cmd = f'start "Backend Server" /D "{backend_dir}" python start_server.py'
    os.system(backend_cmd)
    
    # Wait a moment
    time.sleep(3)
    
    # Start frontend in a new window
    print("Starting frontend server...")
    frontend_cmd = f'start "Frontend Server" /D "{frontend_dir}" npm start'
    os.system(frontend_cmd)
    
    # Wait for servers to start
    time.sleep(5)
    
    # Test backend
    try:
        import requests
        response = requests.get("http://localhost:5001/api/status", timeout=10)
        if response.status_code == 200:
            print("Backend server is running on http://localhost:5001")
        else:
            print(f"Backend responded with status {response.status_code}")
    except ImportError:
        print("Installing requests...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
        response = requests.get("http://localhost:5001/api/status", timeout=10)
        if response.status_code == 200:
            print("Backend server is running on http://localhost:5001")
    except Exception as e:
        print(f"Could not connect to backend: {e}")
    
    print()
    print("Both servers should now be running:")
    print("- Frontend: http://localhost:3000")
    print("- Backend:  http://localhost:5001")
    print()
    print("Opening browser...")
    
    # Open browser to frontend
    try:
        webbrowser.open("http://localhost:3000")
        print("Browser opened to frontend")
    except:
        print("Could not open browser automatically")
    
    print("Check the separate console windows for server logs")
    print("Press Enter to exit this script (servers will keep running)")
    input()

if __name__ == "__main__":
    main()