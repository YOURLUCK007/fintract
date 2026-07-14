#!/usr/bin/env bash
# FinTract - one-click launcher for macOS / Linux
# Run:  bash start-mac-linux.sh   (from the fintract folder)
set -e
cd "$(dirname "$0")"

echo ""
echo "==== FinTract setup ===="

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] Python 3 is not installed. Install it from https://www.python.org/downloads/"
  exit 1
fi

[ -d .venv ] || { echo "Creating virtual environment..."; python3 -m venv .venv; }
source .venv/bin/activate
echo "Installing dependencies (first run only)..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

echo ""
echo "==== Starting FinTract at http://localhost:8000 (Ctrl+C to stop) ===="
( sleep 3; (command -v open >/dev/null && open http://localhost:8000) || (command -v xdg-open >/dev/null && xdg-open http://localhost:8000) ) >/dev/null 2>&1 &
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
