"""
Native Android Audio Backend using pyjnius and android.media.MediaPlayer.
Enables hardware-accelerated background audio playback with screen locked.
"""

from typing import Optional
from player_engine import AudioBackend


class AndroidMediaPlayerBackend(AudioBackend):
    """
    Interfaces directly with Android's native MediaPlayer class via PyJNIus.
    Provides battery-efficient playback and continues playing with screen locked.
    """
    def __init__(self):
        try:
            from jnius import autoclass  # type: ignore[import-not-found, import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "PyJNIus (jnius) is only available in the Android runtime environment. "
                "On desktop, MelodyFlow uses PygameAudioBackend."
            ) from exc

        self.MediaPlayer = autoclass('android.media.MediaPlayer')
        self.AudioManager = autoclass('android.media.AudioManager')
        self.player = self.MediaPlayer()
        self._current_path: str = ""
        self._is_paused: bool = False
        self._is_prepared: bool = False

    def load(self, file_path: str) -> bool:
        try:
            self.player.reset()
            self._is_prepared = False
            self._is_paused = False
            self.player.setDataSource(file_path)
            self.player.prepare()
            self._is_prepared = True
            self._current_path = file_path
            return True
        except Exception as e:
            print(f"[AndroidAudio] Error loading file '{file_path}': {e}")
            return False

    def play(self) -> None:
        if self._is_prepared:
            try:
                self.player.start()
                self._is_paused = False
            except Exception as e:
                print(f"[AndroidAudio] Play error: {e}")

    def pause(self) -> None:
        if self._is_prepared and self.player.isPlaying():
            try:
                self.player.pause()
                self._is_paused = True
            except Exception as e:
                print(f"[AndroidAudio] Pause error: {e}")

    def unpause(self) -> None:
        if self._is_prepared and self._is_paused:
            self.play()

    def stop(self) -> None:
        try:
            if self._is_prepared and self.player.isPlaying():
                self.player.stop()
            self._is_paused = False
        except Exception as e:
            print(f"[AndroidAudio] Stop error: {e}")

    def seek(self, position_seconds: float) -> None:
        if self._is_prepared:
            try:
                pos_ms = int(position_seconds * 1000)
                self.player.seekTo(pos_ms)
            except Exception as e:
                print(f"[AndroidAudio] Seek error: {e}")

    def get_position(self) -> float:
        if self._is_prepared:
            try:
                return float(self.player.getCurrentPosition()) / 1000.0
            except Exception:
                return 0.0
        return 0.0

    def set_volume(self, volume: float) -> None:
        if self._is_prepared:
            try:
                vol = max(0.0, min(1.0, volume))
                self.player.setVolume(vol, vol)
            except Exception:
                pass

    def is_playing(self) -> bool:
        if self._is_prepared and not self._is_paused:
            try:
                return self.player.isPlaying()
            except Exception:
                return False
        return False

    def release(self) -> None:
        """Release native media player resources."""
        try:
            self.player.release()
        except Exception:
            pass


def create_audio_backend() -> AudioBackend:
    """
    Factory function: returns Android native MediaPlayer when running on Android,
    or PygameAudioBackend when running on PC/Mac/Linux.
    """
    from kivy.utils import platform
    if platform == "android":
        try:
            return AndroidMediaPlayerBackend()
        except Exception as e:
            print(f"[AudioBackend] Android backend init failed: {e}. Falling back to default.")

    # Desktop fallback
    try:
        from player_engine import PygameAudioBackend
        return PygameAudioBackend()
    except Exception:
        from player_engine import DummyAudioBackend
        return DummyAudioBackend()
