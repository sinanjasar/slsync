import os 
import zipfile
from mutagen import File as MutagenFile


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