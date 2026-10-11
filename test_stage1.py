import os
import sys
import wave
import struct
import math
import shutil
from pathlib import Path

# Configure utf-8 encoding for console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from scanner import scan_directory, extract_metadata
from library import MusicLibrary, Track, Album
from player_engine import (
    PlayerEngine,
    DummyAudioBackend,
    build_multi_artist_singles_queue,
    build_album_shuffle_queue,
    PlaybackMode,
    RepeatMode
)


def create_sample_wav(file_path: str, duration_sec: float = 1.0, freq: float = 440.0) -> None:
    """Generate a valid, playable PCM WAV file for local audio testing."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    sample_rate = 22050
    num_samples = int(duration_sec * sample_rate)

    with wave.open(file_path, "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        for i in range(num_samples):
            val = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
            data = struct.pack("<h", val)
            wav_file.writeframesraw(data)


def test_stage1():
    print("=" * 60)
    print("[TEST] RUNNING STAGE 1 ENGINE & LIBRARY VERIFICATION SUITE")
    print("=" * 60)

    test_dir = os.path.join(os.path.dirname(__file__), "test_audio_samples")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir, exist_ok=True)

    # 1. Create simulated audio files
    # Album 1: Daft Punk - Discovery (3 tracks)
    create_sample_wav(os.path.join(test_dir, "Daft_Punk_One_More_Time.wav"), 0.5, 440)
    create_sample_wav(os.path.join(test_dir, "Daft_Punk_Aerodynamic.wav"), 0.5, 554)
    create_sample_wav(os.path.join(test_dir, "Daft_Punk_Digital_Love.wav"), 0.5, 659)

    # Album 2: Pink Floyd - The Dark Side of the Moon (2 tracks)
    create_sample_wav(os.path.join(test_dir, "Pink_Floyd_Time.wav"), 0.5, 330)
    create_sample_wav(os.path.join(test_dir, "Pink_Floyd_Money.wav"), 0.5, 392)

    # Singles:
    create_sample_wav(os.path.join(test_dir, "Adele_Skyfall.wav"), 0.5, 523)
    create_sample_wav(os.path.join(test_dir, "Coldplay_Midnight.wav"), 0.5, 587)
    create_sample_wav(os.path.join(test_dir, "Adele_Hello.wav"), 0.5, 659)
    create_sample_wav(os.path.join(test_dir, "Queen_Bohemian_Rhapsody.wav"), 0.5, 440)

    print("\n[1/5] Testing Audio File Scanner...")
    scanned_raw = scan_directory(test_dir)
    assert len(scanned_raw) == 9, f"Expected 9 audio files scanned, got {len(scanned_raw)}"
    print(f"  [OK] Successfully scanned {len(scanned_raw)} audio files with metadata.")

    # 2. Test Library Classification
    print("\n[2/5] Testing Library Classification (Albums vs. Singles)...")
    # Simulate metadata tags for classification test
    tagged_data = [
        # Album: Discovery
        {"file_path": os.path.join(test_dir, "Daft_Punk_One_More_Time.wav"), "file_name": "Daft_Punk_One_More_Time.wav", "extension": ".wav", "file_size": 22050, "title": "One More Time", "artist": "Daft Punk", "album": "Discovery", "duration": 320.0, "track_number": 1, "total_tracks": 14},
        {"file_path": os.path.join(test_dir, "Daft_Punk_Aerodynamic.wav"), "file_name": "Daft_Punk_Aerodynamic.wav", "extension": ".wav", "file_size": 22050, "title": "Aerodynamic", "artist": "Daft Punk", "album": "Discovery", "duration": 212.0, "track_number": 2, "total_tracks": 14},
        {"file_path": os.path.join(test_dir, "Daft_Punk_Digital_Love.wav"), "file_name": "Daft_Punk_Digital_Love.wav", "extension": ".wav", "file_size": 22050, "title": "Digital Love", "artist": "Daft Punk", "album": "Discovery", "duration": 298.0, "track_number": 3, "total_tracks": 14},

        # Album: The Dark Side of the Moon
        {"file_path": os.path.join(test_dir, "Pink_Floyd_Time.wav"), "file_name": "Pink_Floyd_Time.wav", "extension": ".wav", "file_size": 22050, "title": "Time", "artist": "Pink Floyd", "album": "The Dark Side of the Moon", "duration": 413.0, "track_number": 4, "total_tracks": 10},
        {"file_path": os.path.join(test_dir, "Pink_Floyd_Money.wav"), "file_name": "Pink_Floyd_Money.wav", "extension": ".wav", "file_size": 22050, "title": "Money", "artist": "Pink Floyd", "album": "The Dark Side of the Moon", "duration": 382.0, "track_number": 6, "total_tracks": 10},

        # Standalone Singles
        {"file_path": os.path.join(test_dir, "Adele_Skyfall.wav"), "file_name": "Adele_Skyfall.wav", "extension": ".wav", "file_size": 22050, "title": "Skyfall", "artist": "Adele", "album": "Skyfall - Single", "duration": 286.0, "track_number": 1, "total_tracks": 1},
        {"file_path": os.path.join(test_dir, "Coldplay_Midnight.wav"), "file_name": "Coldplay_Midnight.wav", "extension": ".wav", "file_size": 22050, "title": "Midnight", "artist": "Coldplay", "album": "Midnight", "duration": 254.0, "track_number": 1, "total_tracks": 1},
        {"file_path": os.path.join(test_dir, "Adele_Hello.wav"), "file_name": "Adele_Hello.wav", "extension": ".wav", "file_size": 22050, "title": "Hello", "artist": "Adele", "album": "", "duration": 295.0, "track_number": None, "total_tracks": None},
        {"file_path": os.path.join(test_dir, "Queen_Bohemian_Rhapsody.wav"), "file_name": "Queen_Bohemian_Rhapsody.wav", "extension": ".wav", "file_size": 22050, "title": "Bohemian Rhapsody", "artist": "Queen", "album": "Single", "duration": 354.0, "track_number": 1, "total_tracks": 1},
    ]

    lib = MusicLibrary(min_album_tracks=2)
    lib.load_from_metadata_list(tagged_data)

    print(f"  Summary: {lib.summary()}")
    assert len(lib.albums) == 2, f"Expected 2 albums, got {len(lib.albums)}"
    assert len(lib.singles) == 4, f"Expected 4 singles, got {len(lib.singles)}"
    assert len(lib.artists) == 5, f"Expected 5 artists, got {len(lib.artists)}"
    print("  [OK] Albums identified:")
    for alb in lib.albums:
        print(f"    - '{alb.title}' by {alb.artist} ({alb.track_count} tracks, {alb.formatted_duration})")
        track_nums = [t.track_number for t in alb.tracks]
        assert track_nums == sorted(track_nums), f"Album tracks not sorted: {track_nums}"

    print("  [OK] Standalone Singles isolated:")
    for s in lib.singles:
        print(f"    - '{s.title}' by {s.artist}")
        assert s.is_single is True

    # 3. Test Search Functionality
    print("\n[3/5] Testing Real-Time Search...")
    search_res = lib.search("Daft")
    assert len(search_res["albums"]) == 1
    assert len(search_res["tracks"]) == 3
    print(f"  [OK] Search query 'Daft' returned {len(search_res['tracks'])} tracks and {len(search_res['albums'])} album.")

    search_res2 = lib.search("Skyfall")
    assert len(search_res2["tracks"]) == 1
    assert search_res2["tracks"][0].title == "Skyfall"
    print(f"  [OK] Search query 'Skyfall' returned track: '{search_res2['tracks'][0].title}'.")

    # 4. Test Custom Playback & Shuffle Algorithms
    print("\n[4/5] Testing Custom Shuffle Algorithms...")
    multi_artist_queue = build_multi_artist_singles_queue(lib.singles)
    print("  [OK] Multi-Artist Singles Queue:")
    for idx, t in enumerate(multi_artist_queue):
        print(f"    {idx+1}. {t.title} - {t.artist}")
    # Verify no two consecutive tracks by Adele if another artist is available
    for i in range(len(multi_artist_queue) - 1):
        if multi_artist_queue[i].artist == multi_artist_queue[i+1].artist:
            remaining_artists = {t.artist for t in multi_artist_queue[i+1:]}
            assert len(remaining_artists) == 1, "Consecutive tracks from same artist when alternatives existed!"

    album_queue = build_album_shuffle_queue(lib.albums)
    print(f"  [OK] Shuffle Albums Queue generated with {len(album_queue)} tracks.")
    album_names = [t.album for t in album_queue]
    assert album_names[:3] == ["Discovery"] * 3 or album_names[:2] == ["The Dark Side of the Moon"] * 2

    # 5. Test Player Engine Lifecycle & Queue Navigation
    print("\n[5/5] Testing Player Engine Playback Lifecycle...")
    backend = DummyAudioBackend()
    player = PlayerEngine(backend=backend)

    # Play Album Mode
    discovery_album = lib.albums[0] if lib.albums[0].title == "Discovery" else lib.albums[1]
    player.play_album(discovery_album)
    assert player.playback_mode == PlaybackMode.PLAY_ALBUM
    assert player.current_track.title == "One More Time"
    assert player.is_playing is True
    print(f"  [OK] Playing Album: Now Playing '{player.current_track.title}'")

    player.next()
    assert player.current_track.title == "Aerodynamic"
    print(f"  [OK] Next: Now Playing '{player.current_track.title}'")

    player.pause()
    assert player.is_paused is True
    assert player.is_playing is False
    print("  [OK] Playback Paused.")

    player.play()
    assert player.is_paused is False
    print("  [OK] Playback Resumed.")

    player.shuffle_singles_only(lib.singles)
    assert player.playback_mode == PlaybackMode.SHUFFLE_SINGLES_ONLY
    assert len(player.queue) == 4
    for t in player.queue:
        assert t.is_single is True
    print(f"  [OK] Shuffle Singles Only: Queue has {len(player.queue)} tracks, verified zero album tracks.")

    player.set_repeat_mode(RepeatMode.ONE)
    curr_t = player.current_track
    player.next()
    assert player.current_track == curr_t
    print(f"  [OK] Repeat ONE verified: Replayed '{curr_t.title}'.")

    # Test Cache Saving and Loading
    cache_path = os.path.join(os.path.dirname(__file__), ".test_cache.json")
    lib.save_cache(cache_path)
    lib_cached = MusicLibrary()
    loaded = lib_cached.load_cache(cache_path)
    assert loaded is True
    assert len(lib_cached.tracks) == len(lib.tracks)
    assert len(lib_cached.albums) == len(lib.albums)
    assert len(lib_cached.singles) == len(lib.singles)
    if os.path.exists(cache_path):
        os.remove(cache_path)
    print("  [OK] Library JSON Cache save & load verified.")

    player.close()
    shutil.rmtree(test_dir)
    print("\n" + "=" * 60)
    print("[SUCCESS] ALL STAGE 1 CHECKS AND ALGORITHMS PASSED PERFECTLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_stage1()
