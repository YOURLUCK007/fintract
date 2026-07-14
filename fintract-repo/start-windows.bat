@echo off
REM FinTract - one-click launcher for Windows
REM Double-click this file or run it from the fintract folder

cd /d "%~dp0"

echo.
echo ==== FinTract setup ====

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Download from https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
echo Installing dependencies (first run only)...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt

echo.
echo ==== Starting FinTract at http://localhost:8000 ====
start "" http://localhost:8000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
