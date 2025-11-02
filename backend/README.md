# Backend - AI Interview Bot

This folder contains the Flask backend used to accept interview video uploads, run transcription and analysis, and persist results.

Quick start (Windows PowerShell):

1. Create and activate a virtual environment

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
# Note: 'whisper' may require additional system dependencies (ffmpeg). Install ffmpeg for Windows and ensure it's on PATH.
```

3. Run the server

```powershell
python app.py
```

Notes:
- If you don't have MongoDB running locally, the app will continue in 'no-db' mode and still accept uploads and run local analysis functions.
- Large models (whisper, DeepFace) can use significant RAM and may take time to load. Consider using smaller models or running on a machine with enough resources.
