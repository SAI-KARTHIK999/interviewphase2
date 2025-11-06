"""
Setup script to install AI features for interview analysis
Run this to enable transcription and facial analysis
"""
import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    print(f"\n{'='*60}")
    print(f"Installing {package}...")
    print('='*60)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}: {e}")
        return False

def main():
    print("\n🤖 AI INTERVIEW FEATURE SETUP")
    print("="*60)
    print("This will install the following AI features:")
    print("  1. Whisper - For video transcription")
    print("  2. DeepFace - For facial expression analysis")
    print("  3. FFmpeg - For audio/video processing")
    print("\nNote: This may take 5-10 minutes and requires ~2GB download")
    print("="*60)
    
    response = input("\nDo you want to continue? (y/n): ")
    if response.lower() != 'y':
        print("Setup cancelled.")
        return
    
    packages = [
        "openai-whisper",
        "deepface",
        "opencv-python",
        "tensorflow",  # Required by DeepFace
    ]
    
    results = {}
    for package in packages:
        results[package] = install_package(package)
    
    print("\n" + "="*60)
    print("INSTALLATION SUMMARY")
    print("="*60)
    
    for package, success in results.items():
        status = "✓ INSTALLED" if success else "✗ FAILED"
        print(f"{package:30s} {status}")
    
    print("\n" + "="*60)
    
    if all(results.values()):
        print("✓ All packages installed successfully!")
        print("\nNEXT STEPS:")
        print("1. Restart your Flask backend server")
        print("2. Record a new interview video")
        print("3. You should now see:")
        print("   - Real transcriptions (not 'unavailable')")
        print("   - Facial expression analysis")
        print("   - AI assessment scores")
    else:
        print("⚠️  Some packages failed to install")
        print("\nTROUBLESHOOTING:")
        print("1. Make sure you have Python 3.8+ installed")
        print("2. Try running as administrator")
        print("3. Check your internet connection")
        print("4. You may need to install Visual C++ Build Tools for Windows")
        print("   Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
    
    print("\n")

if __name__ == "__main__":
    main()
