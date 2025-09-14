#!/bin/bash

# Quick launcher for API mode
# This script activates venv and runs the API server

echo "🌐 Launching Dispo-Python API Server..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Get port from argument or use default
PORT=${1:-5000}

# Check for virtual environment
if [ -d "venv_new" ]; then
    VENV_DIR="venv_new"
elif [ -d "venv" ]; then
    VENV_DIR="venv"
else
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv_new
    VENV_DIR="venv_new"
    source "$VENV_DIR/bin/activate"
    pip install -r requirements.txt
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

echo "📡 Starting API server on port $PORT..."
echo "📚 API Documentation: http://localhost:$PORT/docs"
echo "🔄 Swagger UI: http://localhost:$PORT/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run API server
python src/main.py --mode api --port $PORT

# Deactivate on exit
deactivate 2>/dev/null