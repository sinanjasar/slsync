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

echo "Installing dependencies..."
pip install \
    'watchdog>=3.0,<4.0' \
    'mutagen>=1.45,<2.0' \
    'ffmpeg-python>=0.2,<1.0' \
    'pyyaml>=6.0,<7.0' \
    'requests>=2.28,<3.0' \
    'tqdm>=4.64,<5.0' \
    'pydub>=0.25,<1.0'

echo "Dependencies installed in $VENV_DIR."


# Get the directory of the setup script (assumes main.py is in the same directory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Remove any existing symlink or file
if [ -L /usr/local/bin/slsync ] || [ -e /usr/local/bin/slsync ]; then
    sudo rm /usr/local/bin/slsync
fi


# Create wrapper script
sudo tee /usr/local/bin/slsync > /dev/null << EOF
#!/bin/bash
cd "$SCRIPT_DIR"
source .venv/bin/activate
exec python main.py "\$@"
EOF

# Make it executable
sudo chmod +x /usr/local/bin/slsync

echo "Wrapper script created: /usr/local/bin/slsync"