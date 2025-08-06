import os
import requests
from mutagen import File as MutagenFile

def has_embedded_art(filepath):
    audio = MutagenFile(filepath)
    if audio is None:
        return False
    # MP3
    if hasattr(audio, 'tags') and audio.tags is not None:
        for tag in audio.tags.keys():
            if tag.startswith('APIC'):
                return True
    # FLAC
    if hasattr(audio, 'pictures') and audio.pictures:
        return True
    # M4A/ALAC
    if hasattr(audio, 'tags') and audio.tags is not None:
        if 'covr' in audio.tags:
            return True
    return False

def find_local_art(directory):
    for fname in ['cover.jpg', 'folder.jpg', 'artwork.jpg', 'cover.png', 'folder.png', 'artwork.png']:
        path = os.path.join(directory, fname)
        if os.path.exists(path):
            return path
    return None

def fetch_album_art_from_musicbrainz(artist, album, dest_path):
    # Search for release group
    query = f'https://musicbrainz.org/ws/2/release-group/?query=artist:{artist}%20AND%20releasegroup:{album}&fmt=json'
    resp = requests.get(query)
    if resp.status_code != 200:
        return False
    data = resp.json()
    if not data.get('release-groups'):
        return False
    release_group = data['release-groups'][0]
    mbid = release_group['id']
    # Fetch cover art
    art_url = f'https://coverartarchive.org/release-group/{mbid}/front'
    art_resp = requests.get(art_url)
    if art_resp.status_code == 200:
        with open(dest_path, 'wb') as f:
            f.write(art_resp.content)
        return True
    return False

def ensure_album_art(filepath, extract_dir):
    if has_embedded_art(filepath):
        print(f"[ART] Embedded album art found in {filepath}")
        return True
    local_art = find_local_art(extract_dir)
    if local_art:
        print(f"[ART] Found local album art: {local_art}")
        # Optionally, embed this art into the audio file here
        return True
    # Try to fetch from MusicBrainz
    audio = MutagenFile(filepath)
    artist = None
    album = None
    if audio is not None:
        if 'artist' in audio.tags:
            artist = audio.tags['artist'][0] if isinstance(audio.tags['artist'], list) else audio.tags['artist']
        if 'album' in audio.tags:
            album = audio.tags['album'][0] if isinstance(audio.tags['album'], list) else audio.tags['album']
    if artist and album:
        dest_path = os.path.join(extract_dir, 'cover.jpg')
        if fetch_album_art_from_musicbrainz(artist, album, dest_path):
            print(f"[ART] Downloaded album art from MusicBrainz: {dest_path}")
            return True
        else:
            print(f"[ART] Could not fetch album art from MusicBrainz for {artist} - {album}")
    else:
        print(f"[ART] No artist/album metadata found for {filepath}")
    return False
