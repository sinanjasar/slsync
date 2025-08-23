#!/usr/bin/env python3


import os
import time
import shutil
import yaml


from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import duplicate checking logic
from duplication_helpers import  is_duplicate, construct_audio_dest

# Import file manipulation logic
from file_helpers import is_alac, convert_to_alac, find_audio_files

# Load config from config.yaml
script_dir = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(script_dir, 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

DOWNLOAD_FOLDERS = config['DOWNLOAD_FOLDERS']
DEST_FOLDER = config['DEST_FOLDER']
LIBRARY_FOLDER = config.get('LIBRARY_FOLDER', None)
SUPPORTED_EXTENSIONS = set(config['SUPPORTED_EXTENSIONS'])
should_skip_duplicates = config.get('SKIP_DUPLICATES', {}).get('ENABLED', 'NO')
print(f"[DEBUG] SKIP_DUPLICATES.ENABLED value: {should_skip_duplicates}")
dup_criteria = config.get('SKIP_DUPLICATES', {}).get('CRITERIA', {})

def convert_and_move(filepath):
    """Convert to ALAC if needed and move to destination"""
    print(f"[INFO] Processing audio file: {os.path.basename(filepath)}")
    try:
        if is_alac(filepath):
            # Already ALAC, just move it to dest
            shutil.move(filepath, DEST_FOLDER)
        else:
            # Convert to ALAC
            alac_filepath = convert_to_alac(filepath)
            if alac_filepath:
                shutil.move(alac_filepath, DEST_FOLDER)
        print(f"[SUCCESS] Moved ALAC file to your library: {os.path.basename(filepath)}")
    except Exception as e:
        print(f"[ERROR] Failed to process {os.path.basename(filepath)}: {e}")

def process_path(path):
        """Common processing logic for both created and moved events"""
        # Ignore browsers download process
        if '.download' in path:
            return 
        try:
            audio_files = find_audio_files(path, SUPPORTED_EXTENSIONS)
            for audio_file in audio_files:
                dest_path = construct_audio_dest(LIBRARY_FOLDER, audio_file, '.m4a')
                if should_skip_duplicates and os.path.exists(dest_path):
                    if is_duplicate(audio_file, dest_path, dup_criteria):
                        print(f"[DUPLICATE] Skipping duplicate: {audio_file}")
                        continue
                convert_and_move(audio_file)
        except Exception as e:
            print(f"[ERROR] Error processing {os.path.basename(path)}: {e}")
    

class DownloadHandler(FileSystemEventHandler):
    
    def __init__(self):
        self.processed= set()

    def on_created(self, event):
        process_path(event.src_path)
    
    def on_moved(self, event):
        # Only handle browsers download completion: .download -> final file
        if '.download' in event.src_path and '.download' not in event.dest_path:
            print(f"[INFO] Browser completed download: {os.path.basename(event.dest_path)}")
            process_path(event.dest_path)

if __name__ == '__main__':
    # Start monitoring
    observers = []
    for folder in DOWNLOAD_FOLDERS:
        if os.path.exists(folder):
            event_handler = DownloadHandler()
            observer = Observer()
            observer.schedule(event_handler, folder, recursive=True)
            observer.start()
            observers.append(observer)
            print(f"[INFO] Monitoring: {folder}")
        else:
            print(f"[WARNING] Skipping non-existent folder: {folder}")

    # Now perform the initial scan
    print("[INFO] Performing initial scan of download folders...")
    for folder in DOWNLOAD_FOLDERS:
        if os.path.exists(folder) and os.path.isdir(folder):
            print(f"[INFO] Looking for audio files in folder: {folder}")
            process_path(folder)
        else:
            print(f"[WARNING] Download folder does not exist: {folder}")

    print('[INFO] Press Ctrl+C to stop monitoring')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping monitors...")
        for observer in observers:
            observer.stop()

    for observer in observers:
        observer.join()

    print("[INFO] Monitoring stopped")