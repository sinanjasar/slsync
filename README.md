# Slsync
An automated music library manager for macOS. Slsync monitors specified download folders for new files, extracts archives, converts audio to ALAC format, organizes your music library, and handles artwork automatically.

## Features
- Monitors multiple download folders simultaneously
- Extracts zip files
- Recursively scans for audio files with configurable extensions
- Converts audio to ALAC (Apple Lossless) format
- Organizes files into your music library
- Embeds artwork from included images or fetches from web

## Installation
Clone the repo and run:
```sh
bash setup.sh
```

## Usage
Start monitoring:
```sh
slsync
```

## Requirements
- macOS
- Python 3.8+
- Setup.sh handles the rest

## What setup.sh does
- Creates Python virtual environment
- Installs dependencies
- Creates wrapper script
