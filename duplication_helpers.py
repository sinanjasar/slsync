import os
def load_config(path):
    """
    Load and parse the YAML configuration file.
    Returns a dictionary with config values.
    """
    import yaml
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    return config


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

def construct_expected_lib_path(dest_folder, metadata, ext):
    print(f"[DEBUG] All metadata fields: {metadata}")
    """
    Construct the expected destination path for a file based on its metadata and extension.
    """
    artist = metadata.get('artist') 
    album = metadata.get('album') 
    title = metadata.get('title') 
    disc = metadata.get('discnumber')   
    track = metadata.get('tracknumber')

    # Pad track number with leading zero if it's a digit and less than 10
    def pad_track(t):
        if t is None:
            return None
        try:
            t_int = int(t)
            return f"{t_int:02d}"
        except Exception:
            return t

    track = pad_track(track)

    if not (artist and album and title):
        raise ValueError(f"Missing required metadata for path construction: {metadata}")
    def sanitize(s):
        return str(s).strip().replace('/', '_').replace(':', '_') if s is not None else None
    
    artist = sanitize(artist)
    album = sanitize(album)
    title = sanitize(title)
    disc = sanitize(disc)
    track = sanitize(track)

    # Build filename according to Apple Music convention
    if disc and track:
        filename = f"{disc}-{track} {title}{ext}"
    elif track:
        filename = f"{track} {title}{ext}"
    else:
        filename = f"{title}{ext}"
    constructed_path = os.path.join(dest_folder, artist, album, filename)
    print(f"[DEBUG] construct_expected_lib_path: {constructed_path}")
    return constructed_path

def is_duplicate(new_filepath, existing_filepath, dup_criteria):
    """
    Compare new file info to existing files using criteria. Returns True if duplicate found.
    """
    
    # Metafields and audio property fields for duplicate checking
    dup_metafields = [k for k, v in dup_criteria.get('METADATA', {}).items() if v is True]
    dup_propfields = [k for k, v in dup_criteria.get('AUDIO_PROPERTIES', {}).items() if v is True]
    use_hash = dup_criteria.get('AUDIO_HASH', False) is True

    # If hash is enabled, only compare hashes and skip all other checks
    if use_hash:
        new_hash = compute_audio_hash(new_filepath)
        exist_hash = compute_audio_hash(existing_filepath)
        print(f"[DEBUG] Comparing audio_hash only: new='{new_hash}', existing='{exist_hash}'")
        if new_hash == exist_hash:
            print("[DEBUG] Files are considered duplicates (hash match).")
            return True
        else:
            print("[DEBUG] Files are NOT duplicates (hash mismatch).")
            return False

    # Otherwise, compare metadata and/or properties as configured
    existing_info = {'metadata': extract_metadata(existing_filepath, dup_metafields)}
    if dup_propfields:
        existing_info['audio_properties'] = extract_audio_properties(existing_filepath, dup_propfields)
    new_file_info = {'metadata': extract_metadata(new_filepath, dup_metafields)}
    if dup_propfields:
        new_file_info['audio_properties'] = extract_audio_properties(new_filepath, dup_propfields)

    print("[DEBUG] is_duplicate: comparing new_file_info and existing_info")
    print(f"[DEBUG] new_file_info: {new_file_info}")
    print(f"[DEBUG] existing_info: {existing_info}")

    match = True
    for field in dup_metafields:
        new_val = new_file_info['metadata'].get(field)
        exist_val = existing_info['metadata'].get(field)
        print(f"[DEBUG] Comparing metadata field '{field}': new='{new_val}' ({type(new_val)}), existing='{exist_val}' ({type(exist_val)})")
        if new_val != exist_val:
            print(f"[DEBUG] MISMATCH on metadata field '{field}'")
            match = False
            break
    if match and dup_propfields:
        for field in dup_propfields:
            new_val = new_file_info['audio_properties'].get(field.upper())
            exist_val = existing_info.get('audio_properties', {}).get(field.upper())
            print(f"[DEBUG] Comparing audio property '{field.upper()}': new='{new_val}' ({type(new_val)}), existing='{exist_val}' ({type(exist_val)})")
            if new_val != exist_val:
                print(f"[DEBUG] MISMATCH on audio property '{field.upper()}'")
                match = False
                break
    if match:
        print("[DEBUG] Files are considered duplicates.")
        return True
    print("[DEBUG] Files are NOT duplicates.")
    return False

def process_file(filepath, config):
    """
    Main logic for processing or skipping a file based on O(1) duplicate check.
    Returns True if processed, False if skipped.
    """
    criteria = config.get('SKIP_DUPLICATES', {}).get('CRITERIA', {})
    dest_folder = config.get('DEST_FOLDER')

    # For path construction (always needed)
    path_meta_fields = ['artist', 'album', 'title', 'discnumber', 'DISCNUMBER', 'disc', 'discc', 'tracknumber', 'TRACKNUMBER', 'track']

    # For duplicate checking (from config)
    dupcheck_meta_fields = [k for k, v in criteria.get('METADATA', {}).items() if v is True]

    prop_fields = list(criteria.get('AUDIO_PROPERTIES', {}).keys())
    use_hash = criteria.get('AUDIO_HASH', 'NO') == 'YES'
    # Extract metadata for new file
    path_metadata = extract_metadata(filepath, path_meta_fields)
    dupcheck_metadata = extract_metadata(filepath, dupcheck_meta_fields)

    ext = os.path.splitext(filepath)[1]
    try:
        expected_path = construct_expected_lib_path(dest_folder, path_metadata, ext)
    except Exception as e:
        print(f"[ERROR] Could not construct expected path: {e}")
        return False
    if os.path.exists(expected_path):
        pass
        
    print(f"Processing file: {filepath}")
    # Place your processing logic here
    return True

