[app]

# (str) Title of your application
title = MelodyFlow

# (str) Package name
package.name = melodyflow

# (str) Package domain (needed for android/ios packaging)
package.domain = org.music

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,wav,mp3

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,music_library/*

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, .venv, __pycache__, .git

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.3.1,mutagen,pillow,pyjnius

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen
fullscreen = 0

# (list) Permissions
android.permissions = READ_MEDIA_AUDIO, READ_EXTERNAL_STORAGE, WAKE_LOCK, FOREGROUND_SERVICE, FOREGROUND_SERVICE_MEDIA_PLAYBACK

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (list) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jars that you do not need, since extra jars can slow
# down the build process.
# android.add_jars = foo.jar

# (list) Android architectures to build for (arm64-v8a is modern standard)
android.archs = arm64-v8a

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (bool) Keep device awake while playing audio
android.wakelock = True

# (bool) Automatically accept Android SDK license agreements
android.accept_sdk_license = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug with command output)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
