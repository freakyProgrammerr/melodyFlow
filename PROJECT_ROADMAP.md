# 🎵 Project Roadmap: Custom Android Local Music Player

## 📌 Project Overview
A personalized music player app built with **Python**, designed specifically for an **Android device**, to play local music files with advanced organization and custom playback/shuffle modes.

---

## 🎧 Core Features & Requirements

### 1. Library Organization
* **Albums**: Groups tracks belonging to full albums (sorted by track number).
* **Singles**: Identifies and isolates standalone single tracks.
* **Artists**: Displays songs and albums grouped by artist.
* **Search**: Real-time search across song titles, artists, and albums.

### 2. Custom Playback & Shuffle Modes
* **Play Album**: Plays the selected album sequentially from track 1 to end.
* **Play Singles**: Continuous playback queue of single tracks.
* **Auto-Play Singles (Multi-Artist)**: Auto-chains singles from varying artists to keep variety high.
* **Shuffle All**: Full randomized playback across the entire local music library.
* **Shuffle Singles Only**: Shuffles only standalone singles without mixing in full album tracks.
* **Shuffle Albums**: Randomizes the order of albums or shuffles tracks selected across albums.

---

## 🛠️ Technology Stack

* **Language**: Python 3.10
* **Metadata Extraction**: `mutagen` (extracts Title, Artist, Album, Duration, Track Number, Artwork from MP3/FLAC/M4A)
* **Audio Engine & Logic**: Custom Python Queue Engine + audio backend
* **Mobile Framework**: Kivy / Flet (Python-powered mobile UI)
* **Android Packaging**: Buildozer / Briefcase (compiles Python code into an installable `.apk`)

---

## 📋 Implementation Plan

### Stage 1: The Brain (Library & Shuffle Logic)
- [x] Initialize Python environment and dependencies (`mutagen`).
- [x] Create `scanner.py` to scan local audio files and extract metadata tags.
- [x] Implement `library.py` to classify tracks into Albums vs. Singles.
- [x] Implement `player_engine.py` with custom shuffle algorithms (Shuffle All, Singles Only, Album Shuffle).
- [x] Test the engine on PC with real/sample music files.

### Stage 2: The Mobile UI (Visual Interface)
- [x] Create modern, touch-friendly UI screens (Library, Albums, Singles, Search) in `main.py`.
- [x] Implement centralized, 100% customizable theme tokens in `ui_theme.py`.
- [x] Persistent bottom Mini Player (Play/Pause, Next, Track Info, progress line) in `ui_components.py`.
- [x] Fullscreen Now Playing modal with album art, scrubber, repeat toggle, and shuffle mode controls.
- [x] Full integration and verification suite in `test_stage2_ui.py`.

### Stage 3: Android Integration & APK Build
- [x] Configure native Android audio backend (`android_backend.py`) for hardware-accelerated playback with screen off.
- [x] Configure runtime Android permissions (`READ_MEDIA_AUDIO`, `READ_EXTERNAL_STORAGE`, `WAKE_LOCK`) in `android_permissions.py`.
- [x] Generate production Android Buildozer specification (`buildozer.spec`).
- [x] Run Buildozer APK compilation (`buildozer android debug` via automated GitHub Actions CI).
- [ ] Transfer and install `.apk` on Android phone.

