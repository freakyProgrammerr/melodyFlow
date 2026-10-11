import random
import time
import threading
from enum import Enum
from typing import List, Optional, Callable, Dict
from library import Track, Album, MusicLibrary


class RepeatMode(Enum):
    OFF = "off"
    ALL = "all"
    ONE = "one"


class PlaybackMode(Enum):
    NORMAL = "normal"
    PLAY_ALBUM = "play_album"
    PLAY_SINGLES = "play_singles"
    AUTO_PLAY_SINGLES_MULTI_ARTIST = "auto_play_singles_multi_artist"
    SHUFFLE_ALL = "shuffle_all"
    SHUFFLE_SINGLES_ONLY = "shuffle_singles_only"
    SHUFFLE_ALBUMS = "shuffle_albums"


class AudioBackend:
    """Abstract base audio backend."""
    def load(self, file_path: str) -> bool:
        raise NotImplementedError
    def play(self) -> None:
        raise NotImplementedError
    def pause(self) -> None:
        raise NotImplementedError
    def unpause(self) -> None:
        raise NotImplementedError
    def stop(self) -> None:
        raise NotImplementedError
    def seek(self, position_seconds: float) -> None:
        raise NotImplementedError
    def get_position(self) -> float:
        raise NotImplementedError
    def set_volume(self, volume: float) -> None:
        raise NotImplementedError
    def is_playing(self) -> bool:
        raise NotImplementedError


class PygameAudioBackend(AudioBackend):
    """Local PC Audio backend using pygame.mixer.music."""
    def __init__(self):
        import pygame
        pygame.mixer.init()
        self._pygame = pygame
        self._is_paused = False
        self._is_loaded = False
        self._current_file = ""
        self._start_time = 0.0
        self._pause_offset = 0.0

    def load(self, file_path: str) -> bool:
        try:
            self._pygame.mixer.music.load(file_path)
            self._current_file = file_path
            self._is_loaded = True
            self._is_paused = False
            self._pause_offset = 0.0
            return True
        except Exception as e:
            print(f"[PygameBackend] Error loading {file_path}: {e}")
            return False

    def play(self) -> None:
        if self._is_loaded:
            self._pygame.mixer.music.play()
            self._start_time = time.time()
            self._pause_offset = 0.0
            self._is_paused = False

    def pause(self) -> None:
        if self._is_loaded and not self._is_paused:
            self._pygame.mixer.music.pause()
            self._pause_offset += time.time() - self._start_time
            self._is_paused = True

    def unpause(self) -> None:
        if self._is_loaded and self._is_paused:
            self._pygame.mixer.music.unpause()
            self._start_time = time.time()
            self._is_paused = False

    def stop(self) -> None:
        if self._is_loaded:
            self._pygame.mixer.music.stop()
            self._is_paused = False
            self._pause_offset = 0.0

    def seek(self, position_seconds: float) -> None:
        try:
            self._pygame.mixer.music.set_pos(position_seconds)
            self._start_time = time.time()
            self._pause_offset = position_seconds
        except Exception:
            pass

    def get_position(self) -> float:
        if not self._is_loaded:
            return 0.0
        pos = self._pygame.mixer.music.get_pos()
        if pos == -1:
            return 0.0
        return pos / 1000.0

    def set_volume(self, volume: float) -> None:
        vol = max(0.0, min(1.0, volume))
        self._pygame.mixer.music.set_volume(vol)

    def is_playing(self) -> bool:
        return self._pygame.mixer.music.get_busy() and not self._is_paused


class DummyAudioBackend(AudioBackend):
    """Headless dummy backend for mock tests."""
    def __init__(self):
        self._playing = False
        self._paused = False
        self._position = 0.0
        self._last_update = 0.0
        self._volume = 1.0

    def load(self, file_path: str) -> bool:
        self._playing = False
        self._paused = False
        self._position = 0.0
        return True

    def play(self) -> None:
        self._playing = True
        self._paused = False
        self._last_update = time.time()

    def pause(self) -> None:
        if self._playing:
            self._position += time.time() - self._last_update
            self._paused = True
            self._playing = False

    def unpause(self) -> None:
        if self._paused:
            self._paused = False
            self._playing = True
            self._last_update = time.time()

    def stop(self) -> None:
        self._playing = False
        self._paused = False
        self._position = 0.0

    def seek(self, position_seconds: float) -> None:
        self._position = position_seconds
        self._last_update = time.time()

    def get_position(self) -> float:
        if self._playing:
            return self._position + (time.time() - self._last_update)
        return self._position

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))

    def is_playing(self) -> bool:
        return self._playing


def build_multi_artist_singles_queue(singles: List[Track]) -> List[Track]:
    """
    Auto-Play Singles (Multi-Artist) Algorithm:
    Interleaves single tracks from different artists so consecutive songs
    are from different artists as much as possible, maximizing variety.
    """
    if not singles:
        return []

    # Group singles by artist
    artist_buckets: Dict[str, List[Track]] = {}
    for s in singles:
        artist_buckets.setdefault(s.artist.lower().strip(), []).append(s)

    # Shuffle each bucket's tracks internally
    for tracks in artist_buckets.values():
        random.shuffle(tracks)

    queue: List[Track] = []
    last_artist = None

    # Greedy largest-bucket interleave
    while artist_buckets:
        # Sort artists by remaining track count descending
        sorted_artists = sorted(
            artist_buckets.keys(),
            key=lambda a: len(artist_buckets[a]),
            reverse=True
        )

        chosen_artist = None
        # Pick the artist with the most songs that isn't the same as the last artist
        for artist_key in sorted_artists:
            if artist_key != last_artist:
                chosen_artist = artist_key
                break

        # Fallback if only the last artist remains
        if not chosen_artist:
            chosen_artist = sorted_artists[0]

        track = artist_buckets[chosen_artist].pop(0)
        queue.append(track)
        last_artist = chosen_artist

        if not artist_buckets[chosen_artist]:
            del artist_buckets[chosen_artist]

    return queue


def build_album_shuffle_queue(albums: List[Album]) -> List[Track]:
    """
    Shuffle Albums Algorithm:
    Randomizes the order of full albums, playing each album sequentially
    from track 1 to end before moving to the next randomized album.
    """
    if not albums:
        return []
    shuffled_albums = list(albums)
    random.shuffle(shuffled_albums)

    queue: List[Track] = []
    for album in shuffled_albums:
        album.sort_tracks()
        queue.extend(album.tracks)
    return queue


class PlayerEngine:
    """
    Central Audio Playback and Queue Manager.
    Handles queue building, playback state, custom shuffle modes, and events.
    """

    def __init__(self, backend: Optional[AudioBackend] = None):
        if backend is not None:
            self.backend = backend
        else:
            try:
                self.backend = PygameAudioBackend()
            except Exception:
                self.backend = DummyAudioBackend()

        self.queue: List[Track] = []
        self.history: List[Track] = []
        self.current_index: int = -1
        self.repeat_mode: RepeatMode = RepeatMode.OFF
        self.playback_mode: PlaybackMode = PlaybackMode.NORMAL
        self.is_paused: bool = False

        # Event callbacks
        self.on_track_change: Optional[Callable[[Optional[Track]], None]] = None
        self.on_state_change: Optional[Callable[[bool], None]] = None
        self.on_queue_update: Optional[Callable[[List[Track]], None]] = None

        # Auto-advance watchdog
        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._playback_monitor_loop, daemon=True)
        self._monitor_thread.start()

    @property
    def current_track(self) -> Optional[Track]:
        if 0 <= self.current_index < len(self.queue):
            return self.queue[self.current_index]
        return None

    @property
    def is_playing(self) -> bool:
        return self.backend.is_playing()

    def set_queue(self, tracks: List[Track], start_index: int = 0, auto_play: bool = True) -> None:
        """Set a new playback queue and optionally start playing."""
        self.queue = list(tracks)
        self.current_index = start_index
        if self.on_queue_update:
            self.on_queue_update(self.queue)

        if 0 <= self.current_index < len(self.queue):
            if auto_play:
                self.play_track_at_index(self.current_index)
        else:
            self.backend.stop()
            if self.on_track_change:
                self.on_track_change(None)

    def play_album(self, album: Album, start_track_index: int = 0) -> None:
        """Play an entire album sequentially from track 1 to end."""
        self.playback_mode = PlaybackMode.PLAY_ALBUM
        album.sort_tracks()
        self.set_queue(album.tracks, start_index=start_track_index, auto_play=True)

    def play_singles(self, singles: List[Track], start_index: int = 0) -> None:
        """Play singles in current list order."""
        self.playback_mode = PlaybackMode.PLAY_SINGLES
        self.set_queue(singles, start_index=start_index, auto_play=True)

    def auto_play_singles_multi_artist(self, singles: List[Track]) -> None:
        """Auto-chains singles from varying artists to maximize variety."""
        self.playback_mode = PlaybackMode.AUTO_PLAY_SINGLES_MULTI_ARTIST
        interleaved = build_multi_artist_singles_queue(singles)
        self.set_queue(interleaved, start_index=0, auto_play=True)

    def shuffle_all(self, all_tracks: List[Track]) -> None:
        """Full randomized playback across the entire local music library."""
        self.playback_mode = PlaybackMode.SHUFFLE_ALL
        shuffled = list(all_tracks)
        random.shuffle(shuffled)
        self.set_queue(shuffled, start_index=0, auto_play=True)

    def shuffle_singles_only(self, singles: List[Track]) -> None:
        """Shuffles only standalone singles without mixing in full album tracks."""
        self.playback_mode = PlaybackMode.SHUFFLE_SINGLES_ONLY
        shuffled = list(singles)
        random.shuffle(shuffled)
        self.set_queue(shuffled, start_index=0, auto_play=True)

    def shuffle_albums(self, albums: List[Album]) -> None:
        """Randomizes the order of albums (sequential per album)."""
        self.playback_mode = PlaybackMode.SHUFFLE_ALBUMS
        album_queue = build_album_shuffle_queue(albums)
        self.set_queue(album_queue, start_index=0, auto_play=True)

    def play_track_at_index(self, index: int) -> bool:
        """Play track at given queue index."""
        if not (0 <= index < len(self.queue)):
            return False

        self.current_index = index
        track = self.queue[self.current_index]

        loaded = self.backend.load(track.file_path)
        if loaded:
            self.backend.play()
            self.is_paused = False
            if self.on_track_change:
                self.on_track_change(track)
            if self.on_state_change:
                self.on_state_change(True)
            return True
        return False

    def play(self) -> None:
        """Resume playback or start playing current track."""
        if self.is_paused:
            self.backend.unpause()
            self.is_paused = False
            if self.on_state_change:
                self.on_state_change(True)
        elif self.current_track:
            self.backend.play()
            self.is_paused = False
            if self.on_state_change:
                self.on_state_change(True)
        elif self.queue:
            self.play_track_at_index(0)

    def pause(self) -> None:
        """Pause playback."""
        if not self.is_paused and self.backend.is_playing():
            self.backend.pause()
            self.is_paused = True
            if self.on_state_change:
                self.on_state_change(False)

    def toggle_play_pause(self) -> None:
        """Toggle play/pause state."""
        if self.is_paused or not self.backend.is_playing():
            self.play()
        else:
            self.pause()

    def next(self) -> bool:
        """Advance to next track in queue or handle repeat mode."""
        if not self.queue:
            return False

        if self.current_track:
            self.history.append(self.current_track)

        if self.repeat_mode == RepeatMode.ONE:
            return self.play_track_at_index(self.current_index)

        next_idx = self.current_index + 1
        if next_idx < len(self.queue):
            return self.play_track_at_index(next_idx)
        elif self.repeat_mode == RepeatMode.ALL:
            return self.play_track_at_index(0)
        else:
            # End of queue
            self.backend.stop()
            self.current_index = -1
            if self.on_track_change:
                self.on_track_change(None)
            if self.on_state_change:
                self.on_state_change(False)
            return False

    def previous(self) -> bool:
        """Return to previous track or restart current track if > 3s played."""
        if not self.queue:
            return False

        # If current track has been playing for > 3 seconds, replay from start
        if self.get_position() > 3.0:
            self.seek(0.0)
            return True

        prev_idx = self.current_index - 1
        if prev_idx >= 0:
            return self.play_track_at_index(prev_idx)
        elif self.repeat_mode == RepeatMode.ALL:
            return self.play_track_at_index(len(self.queue) - 1)
        return False

    def seek(self, position_seconds: float) -> None:
        self.backend.seek(position_seconds)

    def get_position(self) -> float:
        return self.backend.get_position()

    def set_volume(self, volume: float) -> None:
        self.backend.set_volume(volume)

    def set_repeat_mode(self, mode: RepeatMode) -> None:
        self.repeat_mode = mode

    def cycle_repeat_mode(self) -> RepeatMode:
        """Cycle repeat mode: OFF -> ALL -> ONE -> OFF."""
        if self.repeat_mode == RepeatMode.OFF:
            self.repeat_mode = RepeatMode.ALL
        elif self.repeat_mode == RepeatMode.ALL:
            self.repeat_mode = RepeatMode.ONE
        else:
            self.repeat_mode = RepeatMode.OFF
        return self.repeat_mode

    def _playback_monitor_loop(self) -> None:
        """Watches for track completion and auto-advances to next track."""
        while self._monitor_running:
            time.sleep(0.5)
            if self.current_track and not self.is_paused:
                # Check if backend finished playing current track
                # Notice: with dummy backend or when busy goes false while not paused
                if not self.backend.is_playing() and not self.is_paused and self.current_index != -1:
                    # Double check if it genuinely reached the end
                    dur = self.current_track.duration
                    pos = self.backend.get_position()
                    if dur > 0 and pos >= (dur - 1.0):
                        self.next()

    def close(self) -> None:
        self._monitor_running = False
        self.backend.stop()
