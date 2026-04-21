#!/usr/bin/env bash
# Start the backend dev server from the pipeline/backend directory
set -e

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python -m venv .venv
  .venv/Scripts/pip install -r requirements.txt
fi

echo "Starting FastAPI backend on http://localhost:8000"
.venv/Scripts/uvicorn main:app --reload --host 0.0.0.0 --port 8000
