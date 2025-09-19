#!/bin/bash

# Development server startup script

echo "🚀 Starting Local Mind Backend Server..."

# Get the script's directory and the project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Change to backend directory
cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run the server with DEBUG mode for development
echo "🔥 Starting FastAPI server on http://localhost:52817"
echo "📚 API documentation available at http://localhost:52817/docs"
echo "🔧 Running in DEBUG mode"
DEBUG=true python main.py