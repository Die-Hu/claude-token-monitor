#!/bin/bash
# Claude Token Monitor - Quick Start Script
# Auto-creates venv, installs dependencies, and launches the app

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"
REQ_FILE="$PROJECT_DIR/requirements.txt"

# Check Python 3
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "Error: Python 3 not found. Please install Python 3.10+."
    exit 1
fi

echo "Using Python: $($PYTHON --version)"

# Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install / update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r "$REQ_FILE"

# Launch the app
echo "Starting Claude Token Monitor..."
exec python -m claude_token_monitor
