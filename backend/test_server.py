#!/usr/bin/env python3
"""
Simple test script to verify that the Flask server starts and endpoints are accessible.
"""

import requests
import time
import subprocess
import sys
import threading

def test_endpoints():
    """Test the server endpoints"""
    base_url = "http://localhost:5001"
    
    # Wait a moment for server to start
    time.sleep(2)
    
    try:
        # Test root endpoint
        print("Testing root endpoint...")
        response = requests.get(f"{base_url}/")
        print(f"Root endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        
        # Test status endpoint
        print("\nTesting status endpoint...")
        response = requests.get(f"{base_url}/api/status")
        print(f"Status endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        
        # Test health endpoint
        print("\nTesting health endpoint...")
        response = requests.get(f"{base_url}/api/health")
        print(f"Health endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            
        print("\n✅ All endpoints are working correctly!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the Flask server is running on port 5001")
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")

if __name__ == "__main__":
    # Check if requests is available
    try:
        import requests
    except ImportError:
        print("Installing requests...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    
    print("🚀 Testing Flask server endpoints...")
    test_endpoints()