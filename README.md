# soulsync
 
Convenience tool for downloading music on macOS

## What it does

- Monitors your download folders
- Recursively scans for audio files with configurable extensions, extracting zip-files in the process
- Converts audio files to ALAC (Apple Lossless) format
- Embeds artwork if none is present in the metadata
- Transfers the converted files to the Apple Music "Automatically Add to Music.localized" folder for automatic import

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

## Configuration

You can specify which download folders to monitor and which file extensions to process by editing the config.yaml file:

### Example download folders:

- /Users/yourname/Downloads
- /Users/yourname/Desktop/Music

### Example extensions:

- mp3
- flac
- wav

## Requirements

- macOS
- Python 3.8+
- Setup.sh handles the rest

## What setup.sh does

- Creates Python virtual environment
- Installs dependencies
- Creates wrapper script
