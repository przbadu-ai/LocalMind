@echo off
REM Start both frontend and backend for development (Windows)

echo Starting Local Mind Development Environment...

REM Start backend in new window
echo Starting Python backend...
start "LocalMind Backend" cmd /c bin\start_backend.bat

REM Wait for backend to start
echo Waiting for backend to be ready...
:wait_backend
timeout /t 2 /nobreak > nul
curl -s http://localhost:8000/api/v1/health > nul 2>&1
if %errorlevel% neq 0 goto wait_backend

echo Backend is running!

REM Start Tauri dev
echo Starting Tauri development server...
bun tauri dev