#!/usr/bin/env bash
# setup.sh: Create Python venv and install dependencies

set -e

VENV_DIR=".venv"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "Created virtual environment in $VENV_DIR"
else
    echo "Virtual environment already exists in $VENV_DIR"
fi

# Activate venv and install dependencies
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install watchdog mutagen ffmpeg-python pyyaml requests tqdm

echo "Dependencies installed in $VENV_DIR."
