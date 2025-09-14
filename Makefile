# Makefile for Dispo-Python project
# Run 'make help' to see available commands

.PHONY: help run gui api dev test install clean backup init lint format

# Variables
PYTHON := python3
VENV := venv_new
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
SRC_DIR := src
TEST_DIR := tests

# Default target
help:
	@echo "Dispo-Python Makefile Commands"
	@echo "=============================="
	@echo "  make install    - Create venv and install dependencies"
	@echo "  make run        - Run interactive menu"
	@echo "  make gui        - Run GUI application"
	@echo "  make api        - Run API server"
	@echo "  make dev        - Run in development mode"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run code linting"
	@echo "  make format     - Format code with black"
	@echo "  make clean      - Clean cache and temp files"
	@echo "  make backup     - Backup database"
	@echo "  make init       - Initialize database"
	@echo ""

# Setup virtual environment and install dependencies
install:
	@echo "🔧 Setting up virtual environment..."
	@$(PYTHON) -m venv $(VENV)
	@$(VENV_PIP) install --upgrade pip
	@echo "📦 Installing dependencies..."
	@$(VENV_PIP) install -r requirements.txt
	@echo "✅ Installation complete!"

# Run interactive menu
run:
	@./run.sh

# Run GUI application
gui:
	@./run-gui.sh

# Run API server
api:
	@./run-api.sh

# Run in development mode
dev:
	@./run-dev.sh

# Run tests
test:
	@echo "🧪 Running tests..."
	@$(VENV_PYTHON) -m pytest $(TEST_DIR) -v --cov=$(SRC_DIR)

# Lint code
lint:
	@echo "🔍 Linting code..."
	@$(VENV_PYTHON) -m flake8 $(SRC_DIR) --max-line-length=100
	@$(VENV_PYTHON) -m mypy $(SRC_DIR) --ignore-missing-imports

# Format code with black
format:
	@echo "✨ Formatting code..."
	@$(VENV_PYTHON) -m black $(SRC_DIR) --line-length=100

# Clean cache and temporary files
clean:
	@echo "🧹 Cleaning cache and temp files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Backup database
backup:
	@echo "💾 Creating database backup..."
	@$(VENV_PYTHON) $(SRC_DIR)/main.py --mode cli backup

# Initialize database
init:
	@echo "🔧 Initializing database..."
	@$(VENV_PYTHON) $(SRC_DIR)/main.py --mode cli init

# Create user
create-admin:
	@echo "👤 Creating admin user..."
	@$(VENV_PYTHON) $(SRC_DIR)/main.py --mode cli user create \
		--username admin \
		--email admin@example.com \
		--password admin123 \
		--full-name "Administrator" \
		--role admin

# Show database statistics
stats:
	@$(VENV_PYTHON) $(SRC_DIR)/main.py --mode cli stats