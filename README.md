# slsync-audio-tool

This Python tool monitors specified download folders for new files. When a new file is detected, it:

1. Unzips ZIP files.
2. Checks for audio files.
3. Converts non-ALAC audio files to ALAC.
4. Moves ALAC files to `/path/to/your/music/import/folder` for automatic import into Apple Music.

## Configuration

Edit the script to specify your download folders and destination folder if needed.
