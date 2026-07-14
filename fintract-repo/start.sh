#!/bin/bash
# FinTract — one-command startup
# Requires Python 3.11+

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting FinTract..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload
