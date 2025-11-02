#!/usr/bin/env python3
"""
Script to run both frontend and backend servers simultaneously
"""

import subprocess
import sys
import os
import time
import threading
import signal
import webbrowser
from pathlib import Path

class ServerRunner:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.base_dir = Path(__file__).parent
        self.backend_dir = self.base_dir / "backend"
        self.frontend_dir = self.base_dir / "frontend"
        
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        # Check Python dependencies
        try:
            import flask
            import flask_cors
            print("✅ Python Flask dependencies found")
        except ImportError:
            print("❌ Missing Python dependencies. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-cors", "pymongo", "werkzeug"])
            print("✅ Python dependencies installed")
        
        # Check if Node.js is installed
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js found: {result.stdout.strip()}")
            else:
                print("❌ Node.js not found. Please install Node.js")
                return False
        except FileNotFoundError:
            print("❌ Node.js not found. Please install Node.js")
            return False
            
        # Check if npm dependencies are installed
        if not (self.frontend_dir / "node_modules").exists():
            print("📦 Installing frontend dependencies...")
            result = subprocess.run(["npm", "install"], cwd=self.frontend_dir, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Failed to install frontend dependencies: {result.stderr}")
                return False
            print("✅ Frontend dependencies installed")
        else:
            print("✅ Frontend dependencies found")
            
        return True
    
    def start_backend(self):
        """Start the backend server"""
        print("🚀 Starting backend server...")
        try:
            self.backend_process = subprocess.Popen(
                [sys.executable, "start_server.py"],
                cwd=self.backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor backend output
            def monitor_backend():
                for line in iter(self.backend_process.stdout.readline, ''):
                    if line:
                        print(f"[BACKEND] {line.strip()}")
                        
            backend_thread = threading.Thread(target=monitor_backend, daemon=True)
            backend_thread.start()
            
            # Wait a moment for backend to start
            time.sleep(3)
            
            if self.backend_process.poll() is None:
                print("✅ Backend server started successfully on http://localhost:5001")
                return True
            else:
                print("❌ Backend server failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the frontend server"""
        print("🎨 Starting frontend server...")
        try:
            # Set environment variable to avoid auto-opening browser
            env = os.environ.copy()
            env["BROWSER"] = "none"
            
            self.frontend_process = subprocess.Popen(
                ["npm", "start"],
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            # Monitor frontend output
            def monitor_frontend():
                for line in iter(self.frontend_process.stdout.readline, ''):
                    if line:
                        print(f"[FRONTEND] {line.strip()}")
                        
            frontend_thread = threading.Thread(target=monitor_frontend, daemon=True)
            frontend_thread.start()
            
            # Wait for frontend to start
            time.sleep(10)
            
            if self.frontend_process.poll() is None:
                print("✅ Frontend server started successfully on http://localhost:3000")
                return True
            else:
                print("❌ Frontend server failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Error starting frontend: {e}")
            return False
    
    def test_servers(self):
        """Test if both servers are responding"""
        print("🧪 Testing server connectivity...")
        
        try:
            import requests
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
            import requests
        
        # Test backend
        try:
            response = requests.get("http://localhost:5001/api/status", timeout=5)
            if response.status_code == 200:
                print("✅ Backend server is responding")
            else:
                print(f"⚠️  Backend responded with status {response.status_code}")
        except Exception as e:
            print(f"❌ Backend server not responding: {e}")
        
        # Test frontend (just check if port is open)
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                print("✅ Frontend server is responding")
            else:
                print(f"⚠️  Frontend responded with status {response.status_code}")
        except Exception as e:
            print(f"❌ Frontend server not responding: {e}")
    
    def stop_servers(self):
        """Stop both servers"""
        print("\n🛑 Stopping servers...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("✅ Backend server stopped")
            except:
                self.backend_process.kill()
                print("🔪 Backend server force killed")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print("✅ Frontend server stopped")
            except:
                self.frontend_process.kill()
                print("🔪 Frontend server force killed")
    
    def run(self):
        """Main run method"""
        print("🎯 AI Interview Bot - Full Stack Server Runner")
        print("=" * 50)
        
        try:
            # Check dependencies
            if not self.check_dependencies():
                return
            
            # Start backend
            if not self.start_backend():
                return
            
            # Start frontend
            if not self.start_frontend():
                self.stop_servers()
                return
            
            # Test servers
            self.test_servers()
            
            print("\n🎉 Both servers are running!")
            print("📱 Frontend: http://localhost:3000")
            print("🔧 Backend:  http://localhost:5001")
            print("📊 API Status: http://localhost:5001/api/status")
            print("\n💡 Press Ctrl+C to stop both servers")
            
            # Open browser
            time.sleep(2)
            try:
                webbrowser.open("http://localhost:3000")
                print("🌐 Browser opened to frontend")
            except:
                print("⚠️  Could not open browser automatically")
            
            # Wait for interrupt
            try:
                while True:
                    time.sleep(1)
                    # Check if processes are still running
                    if self.backend_process and self.backend_process.poll() is not None:
                        print("❌ Backend process died unexpectedly")
                        break
                    if self.frontend_process and self.frontend_process.poll() is not None:
                        print("❌ Frontend process died unexpectedly")
                        break
            except KeyboardInterrupt:
                print("\n📝 Received interrupt signal")
                
        finally:
            self.stop_servers()
            print("👋 Goodbye!")

def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    print("\n🛑 Interrupt received, stopping servers...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    runner = ServerRunner()
    runner.run()