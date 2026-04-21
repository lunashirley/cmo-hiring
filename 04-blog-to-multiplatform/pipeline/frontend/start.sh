#!/usr/bin/env bash
# Start the frontend dev server from the pipeline/frontend directory
set -e
cd "$(dirname "$0")"
if [ ! -d "node_modules" ]; then
  npm install
fi
echo "Starting frontend on http://localhost:5173"
npm run dev
