#!/bin/bash
# Activation script for Dispo-Python virtual environment

echo "🐍 Activating Dispo-Python virtual environment..."
source venv_new/bin/activate
echo "✅ Virtual environment activated!"
echo "📍 Python path: $(which python)"
echo "📦 Python version: $(python --version)"
echo ""
echo "Available commands:"
echo "  python src/main.py          - Run the GUI application"
echo "  python src/main.py --help   - Show all available options"
echo "  deactivate                  - Exit virtual environment"
echo ""