#!/usr/bin/env python3


import os
import time
import shutil

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import yaml

# Import duplicate checking logic
from duplication_helpers import extract_metadata, construct_expected_lib_path, is_duplicate

# Import file manipulation logic
from file_helpers import is_audio_file, is_alac, convert_to_alac, extract_zip

# Load config from config.yaml
script_dir = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(script_dir, 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)
DOWNLOAD_FOLDERS = config['DOWNLOAD_FOLDERS']
DEST_FOLDER = config['DEST_FOLDER']
SUPPORTED_EXTENSIONS = set(config['SUPPORTED_EXTENSIONS'])


def process_file(filepath):
    """Process audio file - convert to ALAC if needed and move to destination"""

    print(f"[INFO] Processing audio file: {os.path.basename(filepath)}")

    # Folder locations
    dest_folder = config.get('DEST_FOLDER')
    library_folder = config.get('LIBRARY_FOLDER')

    # Metafields for constructing path
    path_metafields = ['artist', 'album', 'title', 'discnumber', 'DISCNUMBER', 'disc', 'discc', 'tracknumber', 'TRACKNUMBER', 'track'] 

    # Extract metadata for new file path
    metadata_for_path = extract_metadata(filepath, path_metafields)
    try:
        library_path = construct_expected_lib_path(library_folder, metadata_for_path, '.m4a')
    except Exception as e:
        print(f"[ERROR] Could not construct library path: {e}")
        return

    # Check for duplicate if enabled
    enabled_value = config.get('SKIP_DUPLICATES', {}).get('ENABLED', 'NO')
    print(f"[DEBUG] SKIP_DUPLICATES.ENABLED value: {enabled_value} (type: {type(enabled_value)})")
    skip_duplicates = enabled_value is True

    print(f"SKIP DUPLICATES: {skip_duplicates}")
    print(f"LIBRARY_PATH: {library_path}")
    if skip_duplicates and os.path.exists(library_path):        
        dup_criteria = config.get('SKIP_DUPLICATES', {}).get('CRITERIA', {})
        if is_duplicate(filepath, library_path, dup_criteria):
            print(f"[DUPLICATE] Skipping duplicate: {filepath} (matches {library_path})")
            return    
    
    try:
        if is_alac(filepath):
            # Already ALAC, just move it to the expected path
            shutil.move(filepath, dest_folder)
            print(f"[SUCCESS] Moved ALAC file: {os.path.basename(filepath)} -> {library_path}")
        else:
            # Convert to ALAC
            alac_filepath = convert_to_alac(filepath)
            if alac_filepath:
                shutil.move(alac_filepath, dest_folder)
                print(f"[SUCCESS] Moved ALAC file: {os.path.basename(alac_filepath)} -> {library_path}")
    except Exception as e:
        print(f"[ERROR] Failed to process {os.path.basename(filepath)}: {e}")

def scan_directory_for_audio(directory):
    """Scan directory recursively for audio files and process them"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if is_audio_file(filepath, SUPPORTED_EXTENSIONS):
                process_file(filepath)

class DownloadHandler(FileSystemEventHandler):
    
    def __init__(self):
        self.processed_files = set()
    
    def on_created(self, event):
        if event.is_directory:
            # New directory appeared - scan it for audio files
            # This handles cases like extracted zip folders or drag-dropped music folders
            print(f"[INFO] New directory detected: {os.path.basename(event.src_path)}")
            time.sleep(2)  # Wait a bit for any files to finish copying
            scan_directory_for_audio(event.src_path)
            return
            
        filepath = event.src_path
        
        # Avoid processing the same file multiple times
        if filepath in self.processed_files:
            return
        
        # Wait a moment for file to be fully written
        time.sleep(1)
        
        # Check if file still exists (might have been moved/deleted)
        if not os.path.exists(filepath):
            return
            
        self.processed_files.add(filepath)
        
        try:
            if filepath.lower().endswith('.zip'):
                print(f"[INFO] Found zip file: {os.path.basename(filepath)}")
                
                # Extract to same directory as zip file
                extract_dir = os.path.dirname(filepath)
                extracted_files = extract_zip(filepath, extract_dir)
                
                # Process any audio files that were extracted
                for extracted_file in extracted_files:
                    if os.path.isfile(extracted_file) and is_audio_file(extracted_file, SUPPORTED_EXTENSIONS):
                        process_file(extracted_file)
                
                # Optionally remove the zip file after extraction
                try:
                    os.remove(filepath)
                    print(f"[INFO] Removed zip file: {os.path.basename(filepath)}")
                except Exception as e:
                    print(f"[WARNING] Could not remove zip file: {e}")
                    
            elif is_audio_file(filepath, SUPPORTED_EXTENSIONS):
                # Skip invalid/corrupt .m4a files before processing
                if filepath.lower().endswith('.m4a') and not is_alac(filepath):
                    return
                process_file(filepath)
                
        except Exception as e:
            print(f"[ERROR] Error processing {os.path.basename(filepath)}: {e}")
    
    def on_moved(self, event):
        # Handle renamed/moved files
        if not event.is_directory:
            self.on_created(event)

if __name__ == '__main__':

    # Initial scan of existing files in download folders
    print("[INFO] Performing initial scan of download folders...")
    for folder in DOWNLOAD_FOLDERS:
        if os.path.exists(folder):
            scan_directory_for_audio(folder)
        else:
            print(f"[WARNING] Download folder does not exist: {folder}")
    
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
    
    print('[INFO] Monitoring download folders... Press Ctrl+C to stop')
    
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