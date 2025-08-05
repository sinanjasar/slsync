import os
import time
import shutil
import zipfile
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from mutagen import File as MutagenFile
import ffmpeg
import yaml
from tqdm import tqdm

# Load config from config.yaml
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
DOWNLOAD_FOLDERS = config['DOWNLOAD_FOLDERS']
DEST_FOLDER = config['DEST_FOLDER']
SUPPORTED_EXTENSIONS = set(config['SUPPORTED_EXTENSIONS'])

# Helper functions
def is_audio_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    return ext in SUPPORTED_EXTENSIONS

def is_alac(filepath):
    audio = MutagenFile(filepath)
    if audio and audio.info:
        return getattr(audio.info, 'codec', None) == 'alac'

def convert_to_alac(src):
    try:
        # Convert src to ALAC, output in same directory, same base name, .m4a extension
        print(f"[INFO] Converting audio file to ALAC format: {src}")
        base = os.path.splitext(os.path.basename(src))[0]
        out_path = os.path.join(os.path.dirname(src), base + '.m4a')
        (
            ffmpeg
            .input(src)
            .output(out_path, acodec='alac', loglevel='error')
            .overwrite_output()
            .run()
        )
        if os.path.exists(out_path):
            filename = os.path.basename(src)
            alac_filename = os.path.basename(out_path)
            print(f"[SUCCESS] Converted to ALAC: {filename} -> {alac_filename}")
            os.remove(src)
            return out_path
        else:
            print(f"[ERROR] Conversion failed: output file was not created for {os.path.basename(src)}")
            return
    except Exception as e:
        print(f"[ERROR] Convert failed: {os.path.basename(src)} -> ALAC | {e}")
        os.remove(out_path)
        os.remove(src)
        return

def extract_zip(zip_path, extract_to):
    """Extract zip file and return list of extracted files"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            extracted_files = [os.path.join(extract_to, name) for name in zip_ref.namelist()]
            print(f"[INFO] Extracted {len(extracted_files)} files from {os.path.basename(zip_path)}")
            return extracted_files
    except Exception as e:
        print(f"[ERROR] Failed to extract {os.path.basename(zip_path)}: {e}")
        return []

def process_file(filepath):
    """Process audio file - convert to ALAC if needed and move to destination"""

    print(f"[INFO] Processing audio file: {os.path.basename(filepath)}")
    
    # Create destination path
    filename = os.path.basename(filepath)
    dest_path = os.path.join(DEST_FOLDER, filename)
    
    # Ensure destination directory exists
    os.makedirs(DEST_FOLDER, exist_ok=True)
    
    try:
        if is_alac(filepath):
            # Already ALAC, just move it
            shutil.move(filepath, dest_path)
            print(f"[SUCCESS] Moved ALAC file: {filename}")
        else:
            # Convert to ALAC
            alac_filepath = convert_to_alac(filepath)
            if alac_filepath:
                process_file(alac_filepath)
    except Exception as e:
        print(f"[ERROR] Failed to process {filename}: {e}")

def scan_directory_for_audio(directory):
    """Scan directory recursively for audio files and process them"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if is_audio_file(filepath):
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
                    if os.path.isfile(extracted_file) and is_audio_file(extracted_file):
                        process_file(extracted_file)
                
                # Optionally remove the zip file after extraction
                try:
                    os.remove(filepath)
                    print(f"[INFO] Removed zip file: {os.path.basename(filepath)}")
                except Exception as e:
                    print(f"[WARNING] Could not remove zip file: {e}")
                    
            elif is_audio_file(filepath):
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
    # Ensure destination folder exists
    os.makedirs(DEST_FOLDER, exist_ok=True)
    
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