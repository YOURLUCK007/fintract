@echo off
REM ============================================================
REM  FinTract - one-click launcher for Windows
REM  Double-click this file inside the extracted "fintract" folder.
REM ============================================================
setlocal

cd /d "%~dp0backend"

echo.
echo ==== FinTract setup ====
echo.

REM 1) Make sure Python is installed.
py --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python is not installed.
  echo Download it from https://www.python.org/downloads/
  echo During install, TICK the box "Add python.exe to PATH", then re-run this file.
  echo.
  pause
  exit /b 1
)

REM 2) Create a virtual environment the first time.
if not exist ".venv" (
  echo Creating virtual environment...
  py -m venv .venv
)

REM 3) Install dependencies.
echo Installing dependencies (first run only, ~1 min)...
call ".venv\Scripts\activate"
py -m pip install --upgrade pip >nul
py -m pip install -r requirements.txt

REM 4) Start the app and open the browser.
echo.
echo ==== Starting FinTract at http://localhost:8000 ====
echo Keep this window open. Close it to stop the app.
echo.
start "" http://localhost:8000
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000

endlocal
