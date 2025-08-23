import os
from file_helpers import extract_metadata, extract_audio_properties, compute_audio_hash

def construct_audio_dest(library_folder, new_file, ext):
    """
    Construct the expected destination path for a file based on its metadata and extension.
    """
    # Retrieve metadata for constructing expected audio file destination

    path_metafields = ['artist', 'album', 'title', 'discnumber', 'tracknumber'] 
    metadata = extract_metadata(new_file, path_metafields)
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
    constructed_path = os.path.join(library_folder, artist, album, filename)
    return constructed_path


def is_duplicate(new_file, existing_file, dup_criteria):
    """
    Create expected path of potential duplicate and compare metadata 
    and audio properties with the newly downloaded audio file
    """

    # Metafields and audio property fields for duplicate checking
    dup_metafields = [k for k, v in dup_criteria.get('METADATA', {}).items() if v is True]
    dup_propfields = [k for k, v in dup_criteria.get('AUDIO_PROPERTIES', {}).items() if v is True]
    use_hash = dup_criteria.get('AUDIO_HASH', False) is True

    # If hash is enabled, only compare hashes and skip all other checks
    if use_hash:
        new_hash = compute_audio_hash(new_file)
        exist_hash = compute_audio_hash(existing_file)
        print(f"[DEBUG] Comparing audio_hash only: new='{new_hash}', existing='{exist_hash}'")
        if new_hash == exist_hash:
            print("[DEBUG] Files are considered duplicates (hash match).")
            return True
        else:
            print("[DEBUG] Files are NOT duplicates (hash mismatch).")
            return False

    # Otherwise, compare metadata and/or properties 
    existing_info = {'metadata': extract_metadata(existing_file, dup_metafields)}
    if dup_propfields:
        existing_info['audio_properties'] = extract_audio_properties(existing_file, dup_propfields)

    new_file_info = {'metadata': extract_metadata(new_file, dup_metafields)}
    if dup_propfields:
        new_file_info['audio_properties'] = extract_audio_properties(new_file, dup_propfields)

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

