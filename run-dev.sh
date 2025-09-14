#!/bin/bash

# Development mode launcher
# Runs the application with debug mode and auto-reload

echo "🔧 Launching Dispo-Python in Development Mode..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

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

# Set development environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1
export PYTHONDONTWRITEBYTECODE=1
export LOG_LEVEL=DEBUG

echo "🐛 Debug mode: ON"
echo "🔄 Auto-reload: ON"
echo "📝 Log level: DEBUG"
echo ""

# Check if API or GUI mode
if [ "$1" == "api" ]; then
    echo "Starting API in development mode..."
    # Use uvicorn with reload for API development
    if command -v uvicorn &> /dev/null; then
        uvicorn src.api.main:app --reload --port 5000 --log-level debug
    else
        pip install uvicorn
        uvicorn src.api.main:app --reload --port 5000 --log-level debug
    fi
else
    echo "Starting GUI in development mode..."
    python src/main.py --mode gui --debug
fi

# Deactivate on exit
deactivate 2>/dev/null