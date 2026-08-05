#!/usr/bin/env bash
# Create virtual environment and install all dependencies for the omnibrain evaluation
set -e
cd "$(dirname "$0")/.."

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment ..."
source "$VENV_DIR/bin/activate"

echo "Installing dependencies ..."
pip install --upgrade pip -q
pip install -r requirements.txt

echo ""
echo "Done. Activate with:"
echo "  source omnibrain/.venv/bin/activate"
