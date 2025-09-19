#!/bin/bash

# Start both frontend and backend for development

echo "🚀 Starting Local Mind Development Environment..."

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    exit
}

trap cleanup EXIT INT TERM

# Start backend in background
echo "🐍 Starting Python backend..."
./bin/start_backend.sh &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to be ready..."
while ! curl -s http://localhost:52817/api/v1/health > /dev/null; do
    sleep 1
done
echo "✅ Backend is running!"

# Start Tauri dev
echo "🦀 Starting Tauri development server..."
bun tauri dev