#!/usr/bin/env bash
# Run from the project root: ./start_frontend.sh
set -e

cd "$(dirname "$0")/frontend"

echo "Installing Node dependencies..."
npm install

echo "Starting ChainWatch frontend on http://localhost:5173"
npm run dev
