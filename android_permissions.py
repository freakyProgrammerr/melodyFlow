"""
Android Runtime Permissions Manager.
Handles Android 13+ (READ_MEDIA_AUDIO) and Android 12- (READ_EXTERNAL_STORAGE).
Gracefully falls back on desktop without errors.
"""

from kivy.utils import platform


def request_android_audio_permissions(on_complete=None) -> None:
    """
    Requests necessary Android storage and audio media permissions at runtime.
    Safe to call on any platform (no-op on Windows/macOS/Linux).
    """
    if platform != "android":
        if on_complete:
            on_complete(True)
        return

    try:
        from android.permissions import request_permissions, Permission
        from android import api_version

        # Android 13+ (API 33+) requires READ_MEDIA_AUDIO
        # Older versions require READ_EXTERNAL_STORAGE
        permissions_to_request = []
        if api_version >= 33:
            permissions_to_request.append(Permission.READ_MEDIA_AUDIO)
        else:
            permissions_to_request.append(Permission.READ_EXTERNAL_STORAGE)

        # Background audio permissions
        permissions_to_request.append(Permission.WAKE_LOCK)

        def callback(permissions, grant_results):
            all_granted = all(grant_results)
            if on_complete:
                on_complete(all_granted)

        request_permissions(permissions_to_request, callback)

    except Exception as e:
        print(f"[AndroidPermissions] Warning: Failed to request permissions: {e}")
        if on_complete:
            on_complete(False)


def get_android_default_music_dir() -> str:
    """
    Returns standard music directory path on Android,
    or local directory when running on desktop.
    """
    if platform == "android":
        # Standard public Music directory on Android devices
        return "/storage/emulated/0/Music"
    return "music_library"
