#!/bin/bash

# Start both frontend and backend for development

echo "🚀 Starting Local Mind Development Environment..."

# Kill any existing processes on our ports first
echo "🧹 Cleaning up existing processes..."

# Kill backend processes on port 52817
BACKEND_PIDS=$(lsof -ti:52817 2>/dev/null)
if [ -n "$BACKEND_PIDS" ]; then
    echo "   Killing existing backend processes on port 52817..."
    echo "$BACKEND_PIDS" | xargs kill -9 2>/dev/null
    sleep 1
fi

# Kill frontend processes on port 1420 (Vite dev server)
FRONTEND_PIDS=$(lsof -ti:1420 2>/dev/null)
if [ -n "$FRONTEND_PIDS" ]; then
    echo "   Killing existing frontend processes on port 1420..."
    echo "$FRONTEND_PIDS" | xargs kill -9 2>/dev/null
    sleep 1
fi

# Also kill any lingering vite or tauri processes for this project
pkill -f "vite.*local-mind" 2>/dev/null
pkill -f "uvicorn.*main:app" 2>/dev/null

echo "✅ Cleanup complete!"

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    # Also clean up ports on exit
    lsof -ti:52817 2>/dev/null | xargs kill -9 2>/dev/null
    lsof -ti:1420 2>/dev/null | xargs kill -9 2>/dev/null
    exit
}

trap cleanup EXIT INT TERM

# Start backend in background
echo "🐍 Starting Python backend..."
./bin/start_backend.sh &
BACKEND_PID=$!

# Wait for backend to start
echo "⏳ Waiting for backend to be ready..."
while ! curl -s http://localhost:52817/health > /dev/null; do
    sleep 1
done
echo "✅ Backend is running!"

# Start Tauri dev
echo "🦀 Starting Tauri development server..."
bun tauri dev
