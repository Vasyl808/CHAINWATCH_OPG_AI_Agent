#!/usr/bin/env bash
# Run from the project root: ./start_backend.sh
set -e

cd "$(dirname "$0")/backend"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
  echo "WARNING: .env not found — copying from .env.example"
  cp .env.example .env
  echo "Please edit backend/.env and set OG_PRIVATE_KEY"
  exit 1
fi

echo "Starting ChainWatch backend on http://localhost:8000"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
