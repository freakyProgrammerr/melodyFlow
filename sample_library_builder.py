"""
Generates initial playable sample audio files and populates library cache.
Ensures the music player has full audio playback and albums ready out-of-the-box.
"""

import os
import wave
import struct
import math
from pathlib import Path
from library import MusicLibrary, Track, Album


def create_pcm_wav(file_path: str, duration_sec: float = 3.0, freq: float = 440.0) -> None:
    """Generate a valid, playable PCM WAV file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    sample_rate = 22050
    num_samples = int(duration_sec * sample_rate)

    with wave.open(file_path, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        for i in range(num_samples):
            # Gentle fade in / fade out to avoid clicks
            envelope = min(1.0, i / (sample_rate * 0.1), (num_samples - i) / (sample_rate * 0.1))
            val = int(32767.0 * 0.4 * envelope * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
            data = struct.pack("<h", val)
            wav_file.writeframesraw(data)


def build_default_library(target_dir: str = "music_library") -> MusicLibrary:
    """Creates sample files and writes library_cache.json."""
    os.makedirs(target_dir, exist_ok=True)

    tracks_data = [
        # Album 1: Discovery (Daft Punk)
        {"file": "Daft_Punk_One_More_Time.wav", "title": "One More Time", "artist": "Daft Punk",
         "album": "Discovery", "duration": 320.0, "track_num": 1, "freq": 440.0},
        {"file": "Daft_Punk_Aerodynamic.wav", "title": "Aerodynamic", "artist": "Daft Punk",
         "album": "Discovery", "duration": 212.0, "track_num": 2, "freq": 554.0},
        {"file": "Daft_Punk_Digital_Love.wav", "title": "Digital Love", "artist": "Daft Punk",
         "album": "Discovery", "duration": 298.0, "track_num": 3, "freq": 659.0},

        # Album 2: The Dark Side of the Moon (Pink Floyd)
        {"file": "Pink_Floyd_Time.wav", "title": "Time", "artist": "Pink Floyd",
         "album": "The Dark Side of the Moon", "duration": 413.0, "track_num": 4, "freq": 330.0},
        {"file": "Pink_Floyd_Money.wav", "title": "Money", "artist": "Pink Floyd",
         "album": "The Dark Side of the Moon", "duration": 382.0, "track_num": 6, "freq": 392.0},

        # Standalone Singles
        {"file": "Adele_Skyfall.wav", "title": "Skyfall", "artist": "Adele",
         "album": "Skyfall - Single", "duration": 286.0, "track_num": 1, "freq": 523.0},
        {"file": "Coldplay_Midnight.wav", "title": "Midnight", "artist": "Coldplay",
         "album": "Midnight", "duration": 254.0, "track_num": 1, "freq": 587.0},
        {"file": "Adele_Hello.wav", "title": "Hello", "artist": "Adele",
         "album": "", "duration": 295.0, "track_num": None, "freq": 659.0},
        {"file": "Queen_Bohemian_Rhapsody.wav", "title": "Bohemian Rhapsody", "artist": "Queen",
         "album": "Single", "duration": 354.0, "track_num": 1, "freq": 440.0},
    ]

    raw_metadata = []
    for item in tracks_data:
        path = os.path.abspath(os.path.join(target_dir, item["file"]))
        create_pcm_wav(path, duration_sec=5.0, freq=item["freq"])
        raw_metadata.append({
            "file_path": path,
            "file_name": item["file"],
            "extension": ".wav",
            "file_size": os.path.getsize(path),
            "title": item["title"],
            "artist": item["artist"],
            "album": item["album"],
            "duration": item["duration"],
            "track_number": item["track_num"],
            "total_tracks": 10 if item["album"] in ["Discovery", "The Dark Side of the Moon"] else 1
        })

    lib = MusicLibrary(min_album_tracks=2)
    lib.load_from_metadata_list(raw_metadata)
    cache_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "library_cache.json"))
    lib.save_cache(cache_path)
    return lib


if __name__ == "__main__":
    lib = build_default_library()
    print("Default music library generated and cached successfully:", lib.summary())
