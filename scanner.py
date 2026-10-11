import os
import io
import re
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

try:
    import mutagen
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import ID3, APIC
    from mutagen.flac import FLAC, Picture
    from mutagen.mp4 import MP4
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


SUPPORTED_EXTENSIONS = {
    ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".wma"
}


def _clean_track_number(val: Any) -> Optional[int]:
    """Parse track or disc number from formats like 1, '1', '1/12', (1, 12)."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, (list, tuple)):
        if len(val) > 0:
            return _clean_track_number(val[0])
        return None
    if isinstance(val, str):
        match = re.match(r"^(\d+)", val.strip())
        if match:
            return int(match.group(1))
    return None


def _clean_total_tracks(val: Any) -> Optional[int]:
    """Extract total track count from formats like '1/12' or (1, 12)."""
    if val is None:
        return None
    if isinstance(val, (list, tuple)) and len(val) > 1:
        return _clean_track_number(val[1])
    if isinstance(val, str):
        parts = val.split('/')
        if len(parts) > 1:
            return _clean_track_number(parts[1])
    return None


def _clean_year(val: Any) -> Optional[int]:
    """Extract 4-digit year from date string or integer."""
    if val is None:
        return None
    if isinstance(val, (list, tuple)) and len(val) > 0:
        val = val[0]
    match = re.search(r"\b(19\d{2}|20\d{2})\b", str(val))
    if match:
        return int(match.group(1))
    return None


def _first_str(val: Any, default: str = "") -> str:
    """Safely get the first string value from a list, tuple, or string."""
    if val is None:
        return default
    if isinstance(val, (list, tuple)):
        return str(val[0]).strip() if len(val) > 0 else default
    return str(val).strip()


def extract_cover_art_bytes(file_path: str) -> Optional[bytes]:
    """Extract embedded cover artwork as raw image bytes (JPEG/PNG)."""
    if not MUTAGEN_AVAILABLE:
        return None
    try:
        audio = mutagen.File(file_path)
        if audio is None:
            return None

        # ID3 (MP3)
        if hasattr(audio, 'tags') and audio.tags:
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    return tag.data

        # FLAC
        if isinstance(audio, FLAC) and audio.pictures:
            return audio.pictures[0].data

        # MP4 / M4A
        if isinstance(audio, MP4) and 'covr' in audio.tags:
            covers = audio.tags['covr']
            if covers:
                return bytes(covers[0])

        # Ogg Vorbis
        if isinstance(audio, OggVorbis) and 'metadata_block_picture' in audio:
            import base64
            for b64 in audio['metadata_block_picture']:
                try:
                    data = base64.b64decode(b64)
                    pic = Picture(data)
                    return pic.data
                except Exception:
                    continue
    except Exception:
        pass
    return None


def extract_metadata(file_path: str, art_cache_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract comprehensive audio metadata for a file.
    Falls back gracefully if tags are missing or file is corrupted.
    """
    p = Path(file_path)
    title = p.stem.replace('_', ' ').strip()
    artist = "Unknown Artist"
    album = ""
    duration = 0.0
    track_number = None
    total_tracks = None
    disc_number = None
    year = None
    genre = "Unknown Genre"
    has_cover = False
    art_path = None

    if MUTAGEN_AVAILABLE and p.is_file():
        try:
            audio = mutagen.File(str(p), easy=True)
            if audio is not None:
                if audio.info and hasattr(audio.info, 'length'):
                    duration = float(audio.info.length)

                tags = audio.tags or {}
                if 'title' in tags:
                    raw_title = _first_str(tags.get('title'))
                    if raw_title:
                        title = raw_title
                if 'artist' in tags:
                    raw_artist = _first_str(tags.get('artist'))
                    if raw_artist:
                        artist = raw_artist
                if 'album' in tags:
                    album = _first_str(tags.get('album'))
                if 'tracknumber' in tags:
                    track_val = tags.get('tracknumber')
                    track_number = _clean_track_number(track_val)
                    total_tracks = _clean_total_tracks(track_val)
                if 'discnumber' in tags:
                    disc_number = _clean_track_number(tags.get('discnumber'))
                if 'date' in tags:
                    year = _clean_year(tags.get('date'))
                if 'genre' in tags:
                    raw_genre = _first_str(tags.get('genre'))
                    if raw_genre:
                        genre = raw_genre

            # Check cover art
            art_bytes = extract_cover_art_bytes(str(p))
            if art_bytes:
                has_cover = True
                if art_cache_dir:
                    os.makedirs(art_cache_dir, exist_ok=True)
                    art_hash = hashlib.md5(f"{artist}_{album}".encode('utf-8', errors='ignore')).hexdigest()
                    target_file = os.path.join(art_cache_dir, f"{art_hash}.jpg")
                    if not os.path.exists(target_file):
                        with open(target_file, "wb") as f:
                            f.write(art_bytes)
                    art_path = target_file
        except Exception as e:
            # Fallback to defaults on corrupt tags
            pass

    return {
        "file_path": str(p.resolve()),
        "file_name": p.name,
        "extension": p.suffix.lower(),
        "file_size": p.stat().st_size if p.exists() else 0,
        "title": title,
        "artist": artist,
        "album": album,
        "duration": round(duration, 2),
        "track_number": track_number,
        "total_tracks": total_tracks,
        "disc_number": disc_number,
        "year": year,
        "genre": genre,
        "has_cover": has_cover,
        "art_path": art_path
    }


def scan_directory(directory_path: str, art_cache_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """Recursively scan a directory for supported audio files and extract metadata."""
    results = []
    root_path = Path(directory_path)
    if not root_path.exists() or not root_path.is_dir():
        return results

    for root, _, files in os.walk(root_path):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in SUPPORTED_EXTENSIONS:
                full_path = os.path.join(root, file)
                meta = extract_metadata(full_path, art_cache_dir=art_cache_dir)
                results.append(meta)

    return results
