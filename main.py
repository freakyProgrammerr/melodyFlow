"""
🎵 MelodyFlow - Custom Android Local Music Player
Stage 2: OpenGL-rendered Touch-friendly Mobile UI with Customizable Theming.
"""

import os
import sys
from typing import Optional

# Set up desktop window size to simulate mobile aspect ratio (portrait)
from kivy.config import Config
Config.set('graphics', 'width', '390')
Config.set('graphics', 'height', '800')
Config.set('graphics', 'resizable', '1')

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.metrics import dp

import ui_theme
from library import MusicLibrary, Track, Album
from player_engine import PlayerEngine, PygameAudioBackend, DummyAudioBackend
from android_backend import create_audio_backend
from android_permissions import request_android_audio_permissions, get_android_default_music_dir
from ui_components import (
    TrackCard,
    AlbumCard,
    ActionPillButton,
    MiniPlayer,
    NowPlayingModal,
    AlbumDetailModal,
    StyledCard
)
from sample_library_builder import build_default_library


class MainRootLayout(BoxLayout):
    """Root layout containing Header, Tab Navigation, Screen Area, and Persistent MiniPlayer."""
    def __init__(self, app_instance, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.app = app_instance
        self.engine = app_instance.engine
        self.library = app_instance.library

        # Background canvas
        with self.canvas.before:
            self.bg_col = Color(*ui_theme.current_theme.bg_primary)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        # 1. Header Bar
        self._build_header()

        # 2. Tab Navigation
        self._build_tab_bar()

        # 3. Main Content Screen Area
        self.screen_manager = ScreenManager(transition=FadeTransition(duration=0.15))
        self._build_screens()
        self.add_widget(self.screen_manager)

        # 4. Persistent Bottom Mini Player
        self.mini_player = MiniPlayer(engine=self.engine, on_expand=self.open_now_playing)
        self.add_widget(self.mini_player)

        # Fullscreen Now Playing Modal instance
        self.now_playing_modal = NowPlayingModal(engine=self.engine)

        # Hook engine callbacks to update UI safely on Kivy main loop
        self.engine.on_track_change = self._on_engine_track_change
        self.engine.on_state_change = self._on_engine_state_change

        # Set default tab
        self.switch_tab("tracks")

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _build_header(self):
        header = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(54),
                           padding=[dp(16), dp(8)], spacing=dp(10))

        # Title + Library Stats
        title_box = BoxLayout(orientation="vertical", spacing=dp(1), size_hint=(0.7, 1))
        app_title = Label(text="MelodyFlow", font_size=dp(20), bold=True,
                          color=ui_theme.current_theme.text_primary, halign="left", valign="middle")
        title_box.bind(width=lambda _, w: setattr(app_title, 'text_size', (w, None)))

        stats_text = f"{self.library.total_tracks} tracks  •  {len(self.library.albums)} albums  •  {len(self.library.singles)} singles"
        self.stats_lbl = Label(text=stats_text, font_size=dp(11),
                               color=ui_theme.current_theme.text_secondary, halign="left", valign="middle")
        title_box.bind(width=lambda _, w: setattr(self.stats_lbl, 'text_size', (w, None)))

        title_box.add_widget(app_title)
        title_box.add_widget(self.stats_lbl)
        header.add_widget(title_box)

        # Theme Cycle Button (Demonstrates 100% dynamic theme customizability)
        btn_theme = Button(text="🎨", font_size=dp(18), size_hint=(None, 1), width=dp(42),
                           background_color=(0, 0, 0, 0), color=ui_theme.current_theme.accent_secondary)
        btn_theme.bind(on_release=self._cycle_theme)
        header.add_widget(btn_theme)

        # Rescan Folder Button
        btn_scan = Button(text="📁", font_size=dp(18), size_hint=(None, 1), width=dp(42),
                          background_color=(0, 0, 0, 0), color=ui_theme.current_theme.text_primary)
        btn_scan.bind(on_release=self._rescan_library)
        header.add_widget(btn_scan)

        self.add_widget(header)

    def _build_tab_bar(self):
        tab_bar = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(42),
                            padding=[dp(12), dp(4)], spacing=dp(8))

        self.tabs = {}
        tab_defs = [
            ("tracks", "Tracks"),
            ("albums", "Albums"),
            ("singles", "Singles"),
            ("search", "Search")
        ]

        for tab_id, label in tab_defs:
            btn = Button(text=label, font_size=dp(13), bold=True,
                         background_color=(0, 0, 0, 0), color=ui_theme.current_theme.text_secondary)
            btn.bind(on_release=lambda _, t=tab_id: self.switch_tab(t))
            tab_bar.add_widget(btn)
            self.tabs[tab_id] = btn

        self.add_widget(tab_bar)

    def _build_screens(self):
        # 1. Tracks Screen
        self.screen_tracks = Screen(name="tracks")
        self._populate_tracks_screen()
        self.screen_manager.add_widget(self.screen_tracks)

        # 2. Albums Screen
        self.screen_albums = Screen(name="albums")
        self._populate_albums_screen()
        self.screen_manager.add_widget(self.screen_albums)

        # 3. Singles Screen
        self.screen_singles = Screen(name="singles")
        self._populate_singles_screen()
        self.screen_manager.add_widget(self.screen_singles)

        # 4. Search Screen
        self.screen_search = Screen(name="search")
        self._populate_search_screen()
        self.screen_manager.add_widget(self.screen_search)

    def _populate_tracks_screen(self):
        self.screen_tracks.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=[dp(14), dp(8)], spacing=dp(10))

        # Action bar
        act_row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(38), spacing=dp(10))
        btn_shuffle = ActionPillButton(text="Shuffle All", icon_symbol="🔀", size_hint=(0.5, 1), is_accent=True)
        btn_shuffle.bind(on_release=lambda *_: self._shuffle_all_tracks())
        btn_play_all = ActionPillButton(text="Play All", icon_symbol="▶", size_hint=(0.5, 1), is_accent=False)
        btn_play_all.bind(on_release=lambda *_: self._play_all_tracks())
        act_row.add_widget(btn_shuffle)
        act_row.add_widget(btn_play_all)
        layout.add_widget(act_row)

        # Scrollable track list
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        tracks_grid = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        tracks_grid.bind(minimum_height=tracks_grid.setter('height'))

        for track in self.library.all_tracks:
            card = TrackCard(track=track, on_play=self._play_track)
            tracks_grid.add_widget(card)

        scroll.add_widget(tracks_grid)
        layout.add_widget(scroll)
        self.screen_tracks.add_widget(layout)

    def _populate_albums_screen(self):
        self.screen_albums.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=[dp(14), dp(8)], spacing=dp(10))

        # Action bar
        act_row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(38))
        btn_shuffle_albums = ActionPillButton(text="Shuffle Albums", icon_symbol="🔀", size_hint=(1, 1), is_accent=True)
        btn_shuffle_albums.bind(on_release=lambda *_: self._shuffle_albums())
        act_row.add_widget(btn_shuffle_albums)
        layout.add_widget(act_row)

        # 2-column album grid
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        albums_grid = GridLayout(cols=2, spacing=dp(12), size_hint_y=None)
        albums_grid.bind(minimum_height=albums_grid.setter('height'))

        for album in self.library.albums:
            card = AlbumCard(album=album, on_select=self._open_album_detail)
            albums_grid.add_widget(card)

        scroll.add_widget(albums_grid)
        layout.add_widget(scroll)
        self.screen_albums.add_widget(layout)

    def _populate_singles_screen(self):
        self.screen_singles.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=[dp(14), dp(8)], spacing=dp(10))

        # Actions: Shuffle Singles + Auto-Play Multi-Artist
        act_row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(38), spacing=dp(10))
        btn_shuffle_singles = ActionPillButton(text="Shuffle Singles", icon_symbol="🔀", size_hint=(0.5, 1), is_accent=True)
        btn_shuffle_singles.bind(on_release=lambda *_: self._shuffle_singles())

        btn_multi_artist = ActionPillButton(text="Multi-Artist Flow", icon_symbol="✨", size_hint=(0.5, 1), is_accent=False)
        btn_multi_artist.bind(on_release=lambda *_: self._auto_play_singles_multi_artist())

        act_row.add_widget(btn_shuffle_singles)
        act_row.add_widget(btn_multi_artist)
        layout.add_widget(act_row)

        # Singles list
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        singles_grid = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        singles_grid.bind(minimum_height=singles_grid.setter('height'))

        for single in self.library.singles:
            card = TrackCard(track=single, on_play=self._play_track)
            singles_grid.add_widget(card)

        scroll.add_widget(singles_grid)
        layout.add_widget(scroll)
        self.screen_singles.add_widget(layout)

    def _populate_search_screen(self):
        self.screen_search.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=[dp(14), dp(8)], spacing=dp(12))

        # Search Input Field
        input_box = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(46))
        self.search_input = TextInput(
            hint_text="Search tracks, artists, albums...",
            multiline=False,
            font_size=dp(14),
            background_color=ui_theme.current_theme.bg_card,
            foreground_color=ui_theme.current_theme.text_primary,
            cursor_color=ui_theme.current_theme.accent_secondary,
            padding=[dp(14), dp(12)]
        )
        self.search_input.bind(text=self._on_search_query)
        input_box.add_widget(self.search_input)
        layout.add_widget(input_box)

        # Scroll results container
        self.search_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.search_results_grid = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        self.search_results_grid.bind(minimum_height=self.search_results_grid.setter('height'))
        self.search_scroll.add_widget(self.search_results_grid)
        layout.add_widget(self.search_scroll)

        self.screen_search.add_widget(layout)

    def switch_tab(self, tab_id: str):
        self.screen_manager.current = tab_id
        for t_id, btn in self.tabs.items():
            if t_id == tab_id:
                btn.color = ui_theme.current_theme.accent_secondary
            else:
                btn.color = ui_theme.current_theme.text_secondary

    def _on_search_query(self, instance, query: str):
        self.search_results_grid.clear_widgets()
        query = query.strip()
        if not query:
            return

        res = self.library.search(query)
        # Show matching tracks
        for track in res["tracks"]:
            card = TrackCard(track=track, on_play=self._play_track)
            self.search_results_grid.add_widget(card)

    def _play_track(self, track: Track):
        self.engine.play_track_directly(track)
        self.mini_player.update_state()

    def _play_all_tracks(self):
        self.engine.set_queue(self.library.all_tracks, start_index=0, auto_play=True)
        self.mini_player.update_state()

    def _shuffle_all_tracks(self):
        self.engine.shuffle_all()
        self.mini_player.update_state()

    def _shuffle_albums(self):
        self.engine.shuffle_albums()
        self.mini_player.update_state()

    def _shuffle_singles(self):
        self.engine.shuffle_singles_only()
        self.mini_player.update_state()

    def _auto_play_singles_multi_artist(self):
        self.engine.auto_play_singles_multi_artist(self.library.singles)
        self.mini_player.update_state()

    def _open_album_detail(self, album: Album):
        modal = AlbumDetailModal(album=album, engine=self.engine, on_play_track=self._play_track)
        modal.open()

    def open_now_playing(self):
        self.now_playing_modal.open()

    def _on_engine_track_change(self, track: Optional[Track]):
        Clock.schedule_once(lambda dt: self.mini_player.update_state(), 0)
        Clock.schedule_once(lambda dt: self.now_playing_modal.refresh(), 0)

    def _on_engine_state_change(self, is_playing: bool):
        Clock.schedule_once(lambda dt: self.mini_player.update_state(), 0)
        Clock.schedule_once(lambda dt: self.now_playing_modal.refresh(), 0)

    def _cycle_theme(self, *args):
        # Dynamically switch between predefined themes
        themes = ["neon_dark", "amoled_pure", "sunset_glow"]
        idx = themes.index(ui_theme.current_theme_name)
        next_theme = themes[(idx + 1) % len(themes)]
        ui_theme.set_theme(next_theme)
        self.bg_col.rgba = ui_theme.current_theme.bg_primary
        self.switch_tab(self.screen_manager.current)

    def _rescan_library(self, *args):
        # Refresh sample or local directory
        self.library = build_default_library()
        self.engine.library = self.library
        self._populate_tracks_screen()
        self._populate_albums_screen()
        self._populate_singles_screen()
        self.stats_lbl.text = f"{self.library.total_tracks} tracks  •  {len(self.library.albums)} albums  •  {len(self.library.singles)} singles"


class MelodyFlowApp(App):
    """Main Kivy Application Class."""
    title = "MelodyFlow Music Player"

    def build(self):
        Window.clearcolor = ui_theme.current_theme.bg_primary

        # Request Android runtime audio permissions if running on device
        request_android_audio_permissions()

        # Load or generate library
        cache_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "library_cache.json"))
        self.library = MusicLibrary()
        if os.path.exists(cache_path):
            self.library.load_cache(cache_path)
        else:
            self.library = build_default_library()

        # Initialize platform-appropriate audio engine (Android MediaPlayer or Desktop Pygame)
        backend = create_audio_backend()

        self.engine = PlayerEngine(backend=backend)
        self.engine.library = self.library

        return MainRootLayout(app_instance=self)

    def on_stop(self):
        """Clean shutdown of playback threads and audio device."""
        if hasattr(self, 'engine'):
            self.engine.close()


if __name__ == "__main__":
    MelodyFlowApp().run()
