import os
import time
import shutil
import zipfile
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
    try:
        audio = MutagenFile(filepath)
        if audio and audio.info:
            return getattr(audio.info, 'codec', None) == 'alac'
    except Exception:
        pass
    return filepath.lower().endswith('.alac') or filepath.lower().endswith('.m4a')

def convert_to_alac(src, dest):
    try:
        ffmpeg.input(src).output(dest, acodec='alac').run(overwrite_output=True)
        return True
    except Exception as e:
        print(f'Error converting {src} to ALAC: {e}')
        return False


# Add this global set to track moved files
moved_files = set()

def process_file(filepath, show_log=True):
    if not os.path.exists(filepath):
        return
    # Only process ZIP files that are fully downloaded (not .crdownload, .part, or Unconfirmed)
    zip_ext = os.path.splitext(filepath)[1].lower()
    base_name = os.path.basename(filepath)
    if zip_ext == '.zip' and not base_name.startswith('Unconfirmed') and not zip_ext in ['.crdownload', '.part']:
        extract_dir = os.path.splitext(filepath)[0]
        print(f"[LOG] Extracting ZIP: {filepath} to {extract_dir}")
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"[LOG] Finished extracting ZIP: {filepath} to {extract_dir}")
        # Remove the ZIP file after extraction
        try:
            os.remove(filepath)
            print(f"[LOG] Removed ZIP file: {filepath}")
        except Exception as e:
            print(f"[LOG] Error removing ZIP file {filepath}: {e}")
        # Collect all audio files in extracted dir
        audio_files = []
        for root, dirs, files in os.walk(extract_dir):
            print(f"[LOG] Walking directory: {root}, dirs: {dirs}, files: {files}")
            for f in files:
                full_path = os.path.join(root, f)
                if is_audio_file(full_path):
                    audio_files.append(full_path)
        if audio_files:
            for f in tqdm(audio_files, desc=f"Moving files from {extract_dir}"):
                process_file(f, show_log=False)
        return
    if is_audio_file(filepath):
        if not is_alac(filepath):
            alac_path = os.path.splitext(filepath)[0] + '.m4a'
            if convert_to_alac(filepath, alac_path):
                filepath = alac_path
        dest_path = os.path.join(DEST_FOLDER, os.path.basename(filepath))
        if filepath in moved_files:
            return
        moved_files.add(filepath)
        if os.path.exists(filepath):
            try:
                shutil.move(filepath, dest_path)
                if show_log:
                    print(f"[LOG] Moved file: {filepath} -> {dest_path}")
            except Exception as e:
                print(f"Error moving {filepath}: {e}")
        else:
            if show_log:
                print(f"File {filepath} does not exist, skipping.")

class DownloadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            # Collect all audio files in the new directory
            audio_files = []
            for root, _, files in os.walk(event.src_path):
                for f in files:
                    full_path = os.path.join(root, f)
                    if is_audio_file(full_path):
                        audio_files.append(full_path)
            if audio_files:
                for f in tqdm(audio_files, desc=f"Moving files from {event.src_path}"):
                    process_file(f, show_log=False)
        else:
            process_file(event.src_path, show_log=True)

if __name__ == '__main__':
    observers = []
    for folder in DOWNLOAD_FOLDERS:
        event_handler = DownloadHandler()
        observer = Observer()
        observer.schedule(event_handler, folder, recursive=True)
        observer.start()
        observers.append(observer)
    print('Monitoring download folders...')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
    for observer in observers:
        observer.join()
