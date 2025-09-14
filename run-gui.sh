#!/bin/bash

# Quick launcher for GUI mode
# This script activates venv and runs the GUI application directly

echo "🚀 Launching Dispo-Python GUI..."

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

# Run GUI application
python src/main.py --mode gui

# Deactivate on exit
deactivate 2>/dev/null