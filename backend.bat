@echo off
REM AI-GYM Backend Runner for Windows
REM Starts the FastAPI + WebSocket server on http://localhost:8000

cd backend
python -m uvicorn src.server.app:app --reload --port 8000
cd ..
