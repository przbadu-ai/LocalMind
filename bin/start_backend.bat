@echo off
REM Development backend starter for Tauri (Windows)

REM Get the script's directory and project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "BACKEND_DIR=%PROJECT_ROOT%\backend"

REM Change to backend directory
cd /d "%BACKEND_DIR%"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
pip install -q -r requirements.txt

REM Start the backend server
set DEBUG=true
python main.py