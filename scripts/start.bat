@echo off
REM Claude Token Monitor - Windows Quick Start Script
REM Auto-creates venv, installs dependencies, and launches the app

setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "VENV_DIR=%PROJECT_DIR%\.venv"
set "REQ_FILE=%PROJECT_DIR%\requirements.txt"

REM Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python 3.10+.
    pause
    exit /b 1
)

python --version

REM Create venv if missing
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

REM Activate venv
call "%VENV_DIR%\Scripts\activate.bat"

REM Install dependencies
echo Installing dependencies...
pip install -q --upgrade pip
pip install -q -r "%REQ_FILE%"

REM Launch the app
echo Starting Claude Token Monitor...
python -m claude_token_monitor

pause
