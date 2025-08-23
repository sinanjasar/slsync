import os 
import zipfile
from collections import deque
from mutagen import File as MutagenFile


# def find_audio_files(folder, supported_extensions):
#     """
#     Find all audio files in a folder, including inside subfolders and zip files,
#     processing directories and their contents before moving on to later items,
#     and preserving the original order of items in each directory.
#     """
#     audio_files = []
#     stack = [folder]
#     while stack:
#         current = stack.pop()  # LIFO: process most recently added item first
#         if os.path.isdir(current):
#             try:
#                 entries = [os.path.join(current, e) for e in os.listdir(current)]
#             except Exception:
#                 continue
#             stack.extend(reversed(entries))  # Add in reverse order so first entry is processed first
#         elif os.path.isfile(current):
#             if current.lower().endswith('.zip'):
#                 extracted_files = extract_zip(current)
#                 stack.extend(reversed(extracted_files))  # Also preserve order for extracted files
#             elif is_audio_file(current, supported_extensions):
#                 audio_files.append(current)
#     return audio_files


def find_audio_files(path, supported_extensions):
    """
    Find all audio files in a file or folder, including inside subfolders and zip files.
    Accepts either a file or a directory as input.
    """
    audio_files = []
    queue = [path]

    while queue:
        current = queue.pop(0)
        if os.path.isdir(current):
            for entry in sorted(os.listdir(current)):
                queue.append(os.path.join(current, entry))
        elif os.path.isfile(current):
            if current.lower().endswith('.zip'):
                print(f"[INFO] Found zip file: {os.path.basename(current)}")
                extract_zip(current)
                # queue.extend(extracted_files)
                continue # on_created will re-scan the directory after extraction
            elif is_audio_file(current, supported_extensions):
                audio_files.append(current)
    return audio_files


def is_audio_file(filepath, supported_extensions):
    ext = os.path.splitext(filepath)[1].lower()
    return ext in supported_extensions

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

        # Build ffmpeg command: encode audio as ALAC, copy video streams if present (as in working shell command)
        import subprocess
        cmd = [
            'ffmpeg',
            '-y',
            '-i', src,
            '-c:a', 'alac',
            '-c:v', 'copy',
            out_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ERROR] ffmpeg error: {result.stderr}")
            return
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
        if os.path.exists(out_path):
            os.remove(out_path)
        if os.path.exists(src):
            os.remove(src)
        return

# def extract_zip(zip_path):
#     """Extract zip file and return list of extracted files. Remove zip after extraction."""
#     try:
#         with zipfile.ZipFile(zip_path, 'r') as zip_ref:
#             zip_ref.extractall(os.path.dirname(zip_path))
#             extracted_files = [os.path.join(os.path.dirname(zip_path), name) for name in zip_ref.namelist()]
#             print(f"[INFO] Extracted {len(extracted_files)} files from {os.path.basename(zip_path)}")
#             try:
#                 os.remove(zip_path)
#                 print(f"[INFO] Removed zip file: {os.path.basename(zip_path)}")
#             except Exception as e:
#                 print(f"[WARNING] Could not remove zip file: {e}")
#             return extracted_files
#     except Exception as e:
#         print(f"[ERROR] Failed to extract {os.path.basename(zip_path)}: {e}")
#         return []
def extract_zip(zip_path):
    """Extract zip file and return list of extracted files. Remove zip after extraction."""
    # DEBUG: Print the exact path being passed
    print(f"[DEBUG] extract_zip called with path: '{zip_path}'")
    print(f"[DEBUG] File exists: {os.path.exists(zip_path)}")
    
    extracted_files = []
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(zip_path))
            extracted_files = [os.path.join(os.path.dirname(zip_path), name) for name in zip_ref.namelist()]
            print(f"[INFO] Extracted {len(extracted_files)} files from {os.path.basename(zip_path)}")
        
        # Remove the zip file AFTER successful extraction
        try:
            print(f"[DEBUG] Attempting to remove: '{zip_path}'")
            os.remove(zip_path)
            print(f"[INFO] Removed zip file: {os.path.basename(zip_path)}")
        except Exception as e:
            print(f"[WARNING] Could not remove zip file: {e}")
            
    except Exception as e:
        print(f"[ERROR] Failed to extract {os.path.basename(zip_path)}: {e}")
        
    return extracted_files

def extract_metadata(filepath, fields): ## Returns a dict of requested metadata fields.
    """
    Extract specified metadata fields from an audio file using mutagen.
    Returns a dict of field: value.
    """
    from mutagen import File
    audio = File(filepath, easy=True)
    if audio is None:
        raise ValueError(f"Unsupported or unreadable file: {filepath}")
    # Print all raw tags for debugging
    # Always extract discnumber and tracknumber for path construction
    always_fields = ['discnumber', 'DISCNUMBER', 'disc', 'discc', 'tracknumber', 'TRACKNUMBER', 'track']
    all_fields = list(set(fields) | set(always_fields))
    result = {}
    for field in all_fields:
        value = audio.get(field)
        if isinstance(value, list):
            value = value[0] if value else None
        result[field] = value
    return result

def extract_audio_properties(filepath, fields):
    """
    Extract specified audio properties (e.g., duration, bitrate, sample rate, channels, codec).
    Returns a dict of property: value. Uses ffprobe for bitrate if mutagen fails.
    """
    from mutagen import File
    import subprocess
    import json
    audio = File(filepath)
    if audio is None:
        raise ValueError(f"Unsupported or unreadable file: {filepath}")
    info = getattr(audio, 'info', None)
    if info is None:
        raise ValueError(f"No audio info found for file: {filepath}")
    result = {}
    for field in fields:
        key = field.upper()
        if key == "DURATION":
            result[field] = getattr(info, 'length', None)
        elif key == "BITRATE":
            # Use ffprobe for bitrate extraction
            try:
                cmd = [
                    'ffprobe',
                    '-v', 'error',
                    '-select_streams', 'a:0',
                    '-show_entries', 'stream=bit_rate',
                    '-of', 'json',
                    filepath
                ]
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
                data = json.loads(output.decode("utf-8"))
                streams = data.get('streams', [])
                if streams and 'bit_rate' in streams[0]:
                    bitrate = int(streams[0]['bit_rate'])
                else:
                    bitrate = None
            except Exception:
                bitrate = None
            result[field] = bitrate
        elif key == "SAMPLE_RATE":
            result[field] = getattr(info, 'sample_rate', None)
        elif key == "CHANNELS":
            result[field] = getattr(info, 'channels', None)
        elif key == "CODEC":
            result[field] = type(info).__name__
        else:
            result[field] = None
    return result

def compute_audio_hash(filepath):
    """
    Compute a hash of the audio content (raw PCM data) using pydub and hashlib.
    Returns a hex digest string.
    """
    import hashlib
    from pydub import AudioSegment
    audio = AudioSegment.from_file(filepath)
    raw_data = audio.raw_data
    return hashlib.sha256(raw_data).hexdigest()

