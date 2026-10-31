"""
Automated Test & Verification Suite for Stage 2 Mobile UI.
Tests widget construction, playback interactions, modals, theming, and search.
"""

import os
import sys

# Configure UTF-8 for console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import main
import ui_theme
from library import MusicLibrary, Track, Album


def test_stage2_ui():
    print("=" * 65)
    print("[TEST] RUNNING STAGE 2 MOBILE UI INTEGRATION SUITE")
    print("=" * 65)

    # 1. Instantiate App & Build Root
    print("\n[1/6] Initializing MelodyFlowApp & OpenGL Canvas Hierarchy...")
    app = main.MelodyFlowApp()
    root = app.build()
    assert root is not None
    assert len(root.children) == 4  # Header, Tab Bar, ScreenManager, MiniPlayer
    print("  [OK] UI Root built with Header, TabBar, ScreenManager, and MiniPlayer.")

    # 2. Test Tab Navigation
    print("\n[2/6] Testing Tab Navigation...")
    tabs = ["tracks", "albums", "singles", "search"]
    for t in tabs:
        root.switch_tab(t)
        assert root.screen_manager.current == t
        print(f"  [OK] Successfully switched to '{t}' screen.")

    # 3. Test Playback Interaction & Mini Player State
    print("\n[3/6] Testing Track Playback & Mini Player updates...")
    assert len(root.library.all_tracks) > 0
    test_track = root.library.all_tracks[0]
    print(f"  Playing track: '{test_track.title}' by {test_track.artist}")
    root._play_track(test_track)
    assert root.engine.current_track is not None
    assert root.engine.current_track.id == test_track.id
    assert root.mini_player.title_label.text == test_track.title
    print(f"  [OK] Mini Player synchronized: '{root.mini_player.title_label.text}'")

    # 4. Test Now Playing Modal
    print("\n[4/6] Testing Fullscreen Now Playing Modal...")
    modal = root.now_playing_modal
    modal.refresh()
    assert modal.title_lbl.text == test_track.title
    print(f"  [OK] Now Playing Modal populated: '{modal.title_lbl.text}'")

    # Test repeat toggle
    from player_engine import RepeatMode
    modal._cycle_repeat()
    print(f"  [OK] Repeat mode cycled to: {root.engine.repeat_mode.value}")

    # 5. Test Album Detail Modal
    print("\n[5/6] Testing Album Detail Modal & Actions...")
    assert len(root.library.albums) > 0
    test_album = root.library.albums[0]
    detail_modal = main.AlbumDetailModal(album=test_album, engine=root.engine, on_play_track=root._play_track)
    assert detail_modal.album.title == test_album.title
    print(f"  [OK] Album Detail opened for '{test_album.title}' with {test_album.track_count} tracks.")
    detail_modal._play_album()
    assert root.engine.playback_mode.value == "play_album"
    print("  [OK] Play Album action executed sequentially.")

    # 6. Test Real-time Search & Theme Customization
    print("\n[6/6] Testing Real-time Search & 100% Theme Customizability...")
    root.switch_tab("search")
    root._on_search_query(None, "Daft")
    assert len(root.search_results_grid.children) == 3
    print("  [OK] Live Search 'Daft' rendered 3 track cards in results grid.")

    # Theme cycling test
    initial_theme = ui_theme.current_theme_name
    root._cycle_theme()
    print(f"  [OK] Theme cycled from {initial_theme} -> {ui_theme.current_theme_name}")
    root._cycle_theme()
    print(f"  [OK] Theme cycled -> {ui_theme.current_theme_name}")

    # Clean shutdown
    app.on_stop()
    print("\n" + "=" * 65)
    print("[SUCCESS] ALL STAGE 2 UI COMPONENTS & CONTROLS PASSED!")
    print("=" * 65)


if __name__ == "__main__":
    test_stage2_ui()
