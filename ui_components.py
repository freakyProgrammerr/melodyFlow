"""
OpenGL-rendered Custom Kivy UI Components for Mobile Music Player.
Built with clean canvas instructions for 100% themeability and silky-smooth rendering.
"""

import os
from typing import Callable, Optional, List
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.image import Image, AsyncImage
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle, Ellipse
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.metrics import dp

import ui_theme
from library import Track, Album


class StyledCard(Button):
    """
    Base touch-responsive card rendered via OpenGL RoundedRectangle.
    Provides hover/press state changes and smooth transitions.
    """
    def __init__(self, bg_color=None, radius=None, border_color=None, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self._bg_color = bg_color or ui_theme.current_theme.bg_card
        self._hover_color = ui_theme.current_theme.bg_card_hover
        self._radius = radius or ui_theme.current_metrics.radius_md
        self._border_color = border_color

        with self.canvas.before:
            self.col_inst = Color(*self._bg_color)
            self.rect_inst = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
            if self._border_color:
                self.border_col = Color(*self._border_color)
                self.border_inst = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self._radius), width=1.1)

        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect_inst.pos = self.pos
        self.rect_inst.size = self.size
        if hasattr(self, 'border_inst') and self._border_color:
            self.border_inst.rounded_rectangle = (self.x, self.y, self.width, self.height, self._radius)

    def on_press(self):
        self.col_inst.rgba = self._hover_color

    def on_release(self):
        self.col_inst.rgba = self._bg_color


class ArtworkThumbnail(Widget):
    """
    Renders album cover artwork or an elegant geometric placeholder with music glyphs.
    """
    def __init__(self, art_path: Optional[str] = None, corner_radius: float = 10.0, **kwargs):
        super().__init__(**kwargs)
        self.art_path = art_path
        self.corner_radius = corner_radius

        with self.canvas:
            self.bg_color = Color(*ui_theme.current_theme.bg_secondary)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.corner_radius])
            
            # Placeholder icon or real texture
            self.accent_col = Color(*ui_theme.current_theme.accent_primary)
            self.icon_circle = Ellipse(pos=(self.x + self.width * 0.25, self.y + self.height * 0.25),
                                       size=(self.width * 0.5, self.height * 0.5))

        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        cw, ch = self.width * 0.5, self.height * 0.5
        self.icon_circle.pos = (self.x + (self.width - cw) / 2, self.y + (self.height - ch) / 2)
        self.icon_circle.size = (cw, ch)


class TrackCard(StyledCard):
    """
    Interactive track row showing title, artist, duration, and metadata.
    """
    def __init__(self, track: Track, on_play: Callable[[Track], None], **kwargs):
        self.track = track
        self.on_play_callback = on_play
        super().__init__(size_hint=(1, None), height=dp(64), **kwargs)

        # Layout content inside
        layout = BoxLayout(orientation="horizontal", padding=[dp(12), dp(6)], spacing=dp(12), pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(layout, 'pos', self.pos),
                  size=lambda *_: setattr(layout, 'size', self.size))

        # Icon / Art badge
        badge = ArtworkThumbnail(art_path=track.art_path, size_hint=(None, None), size=(dp(48), dp(48)))
        layout.add_widget(badge)

        # Title + Artist stack
        info_box = BoxLayout(orientation="vertical", spacing=dp(2), size_hint=(0.7, 1))
        title_label = Label(text=track.title, font_size=dp(15), bold=True,
                            color=ui_theme.current_theme.text_primary, halign="left", valign="middle",
                            size_hint=(1, 0.6), text_size=(dp(200), None), shorten=True, shorten_from="right")
        info_box.bind(width=lambda w, val: setattr(title_label, 'text_size', (val, None)))

        artist_text = f"{track.artist}  •  {track.album if not track.is_single else 'Single'}"
        sub_label = Label(text=artist_text, font_size=dp(12),
                          color=ui_theme.current_theme.text_secondary, halign="left", valign="middle",
                          size_hint=(1, 0.4), text_size=(dp(200), None), shorten=True, shorten_from="right")
        info_box.bind(width=lambda w, val: setattr(sub_label, 'text_size', (val, None)))

        info_box.add_widget(title_label)
        info_box.add_widget(sub_label)
        layout.add_widget(info_box)

        # Duration label
        dur_label = Label(text=track.formatted_duration, font_size=dp(13),
                          color=ui_theme.current_theme.text_muted, size_hint=(0.2, 1),
                          halign="right", valign="middle")
        layout.add_widget(dur_label)

        self.add_widget(layout)

    def on_release(self):
        super().on_release()
        if self.on_play_callback:
            self.on_play_callback(self.track)


class AlbumCard(StyledCard):
    """
    Grid card for full albums. Displays artwork, title, artist, and track count.
    """
    def __init__(self, album: Album, on_select: Callable[[Album], None], **kwargs):
        self.album = album
        self.on_select_callback = on_select
        super().__init__(size_hint=(1, None), height=dp(185), **kwargs)

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8), pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(layout, 'pos', self.pos),
                  size=lambda *_: setattr(layout, 'size', self.size))

        # Album Art
        art = ArtworkThumbnail(art_path=album.art_path, corner_radius=12.0, size_hint=(1, 0.65))
        layout.add_widget(art)

        # Album Title
        title_lbl = Label(text=album.title, font_size=dp(14), bold=True,
                          color=ui_theme.current_theme.text_primary, halign="left", valign="middle",
                          size_hint=(1, 0.18), text_size=(dp(160), None), shorten=True)
        layout.bind(width=lambda _, val: setattr(title_lbl, 'text_size', (val - dp(20), None)))
        layout.add_widget(title_lbl)

        # Artist & Count
        desc = f"{album.artist}  •  {album.track_count} tracks"
        desc_lbl = Label(text=desc, font_size=dp(11),
                         color=ui_theme.current_theme.text_secondary, halign="left", valign="middle",
                         size_hint=(1, 0.17), text_size=(dp(160), None), shorten=True)
        layout.bind(width=lambda _, val: setattr(desc_lbl, 'text_size', (val - dp(20), None)))
        layout.add_widget(desc_lbl)

        self.add_widget(layout)

    def on_release(self):
        super().on_release()
        if self.on_select_callback:
            self.on_select_callback(self.album)


class ActionPillButton(Button):
    """Modern pill button for primary actions (e.g. 'Play Album', 'Shuffle All')."""
    def __init__(self, text: str, icon_symbol: str = "▶", is_accent: bool = True, **kwargs):
        super().__init__(text=f"{icon_symbol}  {text}", font_size=dp(13), bold=True, **kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = ui_theme.current_theme.text_primary
        self._is_accent = is_accent
        self._bg_col = ui_theme.current_theme.accent_primary if is_accent else ui_theme.current_theme.bg_card

        with self.canvas.before:
            self.col_inst = Color(*self._bg_col)
            self.rect_inst = RoundedRectangle(pos=self.pos, size=self.size, radius=[ui_theme.current_metrics.radius_pill])

        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect_inst.pos = self.pos
        self.rect_inst.size = self.size

    def on_press(self):
        self.col_inst.rgba = ui_theme.current_theme.accent_secondary if self._is_accent else ui_theme.current_theme.bg_card_hover

    def on_release(self):
        self.col_inst.rgba = self._bg_col


class MiniPlayer(BoxLayout):
    """
    Persistent bottom bar pinned above navigation.
    Displays current track, Play/Pause, Next, and opens NowPlayingModal on tap.
    """
    def __init__(self, engine, on_expand: Callable[[], None], **kwargs):
        super().__init__(orientation="horizontal", size_hint=(1, None),
                         height=dp(ui_theme.current_metrics.mini_player_height),
                         padding=[dp(12), dp(8)], spacing=dp(12), **kwargs)
        self.engine = engine
        self.on_expand_callback = on_expand

        with self.canvas.before:
            Color(*ui_theme.current_theme.bg_secondary)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16), dp(16), 0, 0])
            # Mini top progress line
            self.prog_col = Color(*ui_theme.current_theme.progress_bar_fill)
            self.prog_line = Line(points=[self.x, self.top, self.x, self.top], width=2.0)

        self.bind(pos=self._update_canvas, size=self._update_canvas)

        # Thumbnail art
        self.thumb = ArtworkThumbnail(size_hint=(None, None), size=(dp(50), dp(50)), corner_radius=10.0)
        self.add_widget(self.thumb)

        # Info Box (Title + Artist)
        self.info_btn = Button(background_color=(0, 0, 0, 0), size_hint=(0.6, 1))
        info_layout = BoxLayout(orientation="vertical", spacing=dp(2), pos=self.info_btn.pos, size=self.info_btn.size)
        self.info_btn.bind(pos=lambda *_: setattr(info_layout, 'pos', self.info_btn.pos),
                           size=lambda *_: setattr(info_layout, 'size', self.info_btn.size))

        self.title_label = Label(text="No track playing", font_size=dp(14), bold=True,
                                 color=ui_theme.current_theme.text_primary, halign="left", valign="middle",
                                 size_hint=(1, 0.55), shorten=True)
        self.artist_label = Label(text="Select music to start", font_size=dp(12),
                                  color=ui_theme.current_theme.text_secondary, halign="left", valign="middle",
                                  size_hint=(1, 0.45), shorten=True)
        info_layout.bind(width=lambda _, w: setattr(self.title_label, 'text_size', (w, None)))
        info_layout.bind(width=lambda _, w: setattr(self.artist_label, 'text_size', (w, None)))

        info_layout.add_widget(self.title_label)
        info_layout.add_widget(self.artist_label)
        self.info_btn.add_widget(info_layout)
        self.info_btn.bind(on_release=lambda *_: self.on_expand_callback())
        self.add_widget(self.info_btn)

        # Control Buttons (Play/Pause, Next)
        ctrl_box = BoxLayout(orientation="horizontal", size_hint=(0.28, 1), spacing=dp(8))
        
        self.btn_play = Button(text="▶", font_size=dp(20), bold=True,
                               background_color=(0, 0, 0, 0), color=ui_theme.current_theme.accent_secondary,
                               size_hint=(0.5, 1))
        self.btn_play.bind(on_release=self._toggle_play)

        self.btn_next = Button(text="⏭", font_size=dp(18), bold=True,
                               background_color=(0, 0, 0, 0), color=ui_theme.current_theme.text_primary,
                               size_hint=(0.5, 1))
        self.btn_next.bind(on_release=self._next_track)

        ctrl_box.add_widget(self.btn_play)
        ctrl_box.add_widget(self.btn_next)
        self.add_widget(ctrl_box)

    def _update_canvas(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        # Update progress line
        pos_frac = 0.0
        if self.engine.current_track and self.engine.current_track.duration > 0:
            pos_frac = min(1.0, max(0.0, self.engine.get_position() / self.engine.current_track.duration))
        prog_w = self.width * pos_frac
        self.prog_line.points = [self.x, self.top, self.x + prog_w, self.top]

    def _toggle_play(self, *args):
        self.engine.toggle_play_pause()
        self.update_state()

    def _next_track(self, *args):
        self.engine.next_track()
        self.update_state()

    def update_state(self):
        track = self.engine.current_track
        if track:
            self.title_label.text = track.title
            self.artist_label.text = f"{track.artist}  •  {track.album if not track.is_single else 'Single'}"
            self.btn_play.text = "⏸" if self.engine.is_playing else "▶"
        else:
            self.title_label.text = "No track playing"
            self.artist_label.text = "Select a song or album to play"
            self.btn_play.text = "▶"
        self._update_canvas()


class NowPlayingModal(ModalView):
    """
    Fullscreen immersive Now Playing screen with album art, scrubber slider,
    mode selectors, and responsive controls.
    """
    def __init__(self, engine, **kwargs):
        super().__init__(size_hint=(1, 1), auto_dismiss=True, background_color=(0, 0, 0, 0), **kwargs)
        self.engine = engine
        self._user_is_scrubbing = False

        # Main background
        with self.canvas.before:
            Color(*ui_theme.current_theme.bg_modal)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self.bg_rect, 'pos', self.pos),
                  size=lambda *_: setattr(self.bg_rect, 'size', self.size))

        # Root content layout
        root = BoxLayout(orientation="vertical", padding=[dp(20), dp(16)], spacing=dp(14))

        # Header bar: Down chevron to dismiss + Title
        header = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(48))
        btn_dismiss = Button(text="⌄", font_size=dp(32), bold=True, size_hint=(None, 1), width=dp(48),
                             background_color=(0, 0, 0, 0), color=ui_theme.current_theme.text_secondary)
        btn_dismiss.bind(on_release=lambda *_: self.dismiss())
        header.add_widget(btn_dismiss)

        header_lbl = Label(text="NOW PLAYING", font_size=dp(13), bold=True,
                           color=ui_theme.current_theme.text_muted, size_hint=(1, 1))
        header.add_widget(header_lbl)

        # Mode Badge Indicator
        self.mode_badge = Label(text="NORMAL", font_size=dp(11), bold=True,
                                color=ui_theme.current_theme.accent_secondary, size_hint=(None, 1), width=dp(90))
        header.add_widget(self.mode_badge)
        root.add_widget(header)

        # Large Artwork
        art_container = AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, 0.45))
        self.large_art = ArtworkThumbnail(corner_radius=20.0, size_hint=(None, None), size=(dp(240), dp(240)))
        art_container.add_widget(self.large_art)
        root.add_widget(art_container)

        # Song Info
        info_stack = BoxLayout(orientation="vertical", spacing=dp(4), size_hint=(1, None), height=dp(64))
        self.title_lbl = Label(text="Track Title", font_size=dp(20), bold=True,
                               color=ui_theme.current_theme.text_primary, halign="center", shorten=True)
        self.artist_lbl = Label(text="Artist Name", font_size=dp(14),
                                color=ui_theme.current_theme.text_secondary, halign="center", shorten=True)
        info_stack.bind(width=lambda _, w: setattr(self.title_lbl, 'text_size', (w, None)))
        info_stack.bind(width=lambda _, w: setattr(self.artist_lbl, 'text_size', (w, None)))
        info_stack.add_widget(self.title_lbl)
        info_stack.add_widget(self.artist_lbl)
        root.add_widget(info_stack)

        # Scrubber / Slider Box
        scrubber_box = BoxLayout(orientation="vertical", size_hint=(1, None), height=dp(52), spacing=dp(2))
        self.seek_slider = Slider(min=0, max=100, value=0, size_hint=(1, None), height=dp(30))
        self.seek_slider.cursor_size = (dp(16), dp(16))
        self.seek_slider.bind(on_touch_down=self._on_seek_start, on_touch_up=self._on_seek_end)
        scrubber_box.add_widget(self.seek_slider)

        time_row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(18))
        self.lbl_time_cur = Label(text="0:00", font_size=dp(12), color=ui_theme.current_theme.text_muted,
                                  size_hint=(0.5, 1), halign="left")
        self.lbl_time_tot = Label(text="0:00", font_size=dp(12), color=ui_theme.current_theme.text_muted,
                                  size_hint=(0.5, 1), halign="right")
        time_row.bind(width=lambda _, w: setattr(self.lbl_time_cur, 'text_size', (w / 2, None)))
        time_row.bind(width=lambda _, w: setattr(self.lbl_time_tot, 'text_size', (w / 2, None)))
        time_row.add_widget(self.lbl_time_cur)
        time_row.add_widget(self.lbl_time_tot)
        scrubber_box.add_widget(time_row)
        root.add_widget(scrubber_box)

        # Primary Controls Row: Prev, Play/Pause, Next
        ctrls_row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(68), spacing=dp(24))
        ctrls_row.add_widget(Widget(size_hint=(0.1, 1)))

        self.btn_prev = Button(text="⏮", font_size=dp(28), bold=True, size_hint=(0.25, 1),
                               background_color=(0, 0, 0, 0), color=ui_theme.current_theme.text_primary)
        self.btn_prev.bind(on_release=lambda *_: self._prev())

        self.btn_play_pause = ActionPillButton(text="", icon_symbol="▶", size_hint=(0.3, 1), is_accent=True)
        self.btn_play_pause.bind(on_release=lambda *_: self._toggle_play())

        self.btn_next = Button(text="⏭", font_size=dp(28), bold=True, size_hint=(0.25, 1),
                               background_color=(0, 0, 0, 0), color=ui_theme.current_theme.text_primary)
        self.btn_next.bind(on_release=lambda *_: self._next())

        ctrls_row.add_widget(self.btn_prev)
        ctrls_row.add_widget(self.btn_play_pause)
        ctrls_row.add_widget(self.btn_next)
        ctrls_row.add_widget(Widget(size_hint=(0.1, 1)))
        root.add_widget(ctrls_row)

        # Secondary Controls Row: Repeat Mode & Shuffle Mode Indicator
        sec_row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(42), spacing=dp(12))
        self.btn_repeat = Button(text="🔁 ALL", font_size=dp(12), bold=True, size_hint=(0.5, 1),
                                 background_color=(0, 0, 0, 0), color=ui_theme.current_theme.text_secondary)
        self.btn_repeat.bind(on_release=self._cycle_repeat)
        sec_row.add_widget(self.btn_repeat)

        self.btn_shuffle_mode = Button(text="🔀 SHUFFLE ALL", font_size=dp(12), bold=True, size_hint=(0.5, 1),
                                       background_color=(0, 0, 0, 0), color=ui_theme.current_theme.accent_secondary)
        self.btn_shuffle_mode.bind(on_release=self._cycle_shuffle)
        sec_row.add_widget(self.btn_shuffle_mode)
        root.add_widget(sec_row)

        self.add_widget(root)

        # Schedule regular progress tick
        Clock.schedule_interval(self._tick_progress, 0.5)

    def on_open(self):
        self.refresh()

    def refresh(self):
        track = self.engine.current_track
        if track:
            self.title_lbl.text = track.title
            self.artist_lbl.text = f"{track.artist}  •  {track.album if not track.is_single else 'Single'}"
            self.seek_slider.max = track.duration if track.duration > 0 else 100
            self.lbl_time_tot.text = track.formatted_duration
            self.btn_play_pause.text = "⏸" if self.engine.is_playing else "▶"
            self.mode_badge.text = self.engine.playback_mode.value.replace("_", " ").upper()
            self._update_repeat_label()
        else:
            self.title_lbl.text = "Select a track to play"
            self.artist_lbl.text = ""
            self.btn_play_pause.text = "▶"

    def _update_repeat_label(self):
        rep = self.engine.repeat_mode.value.upper()
        self.btn_repeat.text = f"🔁 REPEAT: {rep}"

    def _cycle_repeat(self, *args):
        from player_engine import RepeatMode
        modes = [RepeatMode.ALL, RepeatMode.ONE, RepeatMode.OFF]
        idx = modes.index(self.engine.repeat_mode)
        next_mode = modes[(idx + 1) % len(modes)]
        self.engine.set_repeat_mode(next_mode)
        self._update_repeat_label()

    def _cycle_shuffle(self, *args):
        # Quick action: Shuffle Singles Only if available, else Shuffle All
        if self.engine.library and self.engine.library.singles:
            self.engine.shuffle_singles_only()
        else:
            self.engine.shuffle_all()
        self.refresh()

    def _toggle_play(self):
        self.engine.toggle_play_pause()
        self.refresh()

    def _next(self):
        self.engine.next_track()
        self.refresh()

    def _prev(self):
        self.engine.previous_track()
        self.refresh()

    def _on_seek_start(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self._user_is_scrubbing = True

    def _on_seek_end(self, instance, touch):
        if self._user_is_scrubbing:
            self._user_is_scrubbing = False
            self.engine.seek(self.seek_slider.value)

    def _tick_progress(self, dt):
        if self.engine.is_playing and not self._user_is_scrubbing:
            pos = self.engine.get_position()
            self.seek_slider.value = pos
            mins = int(pos // 60)
            secs = int(pos % 60)
            self.lbl_time_cur.text = f"{mins}:{secs:02d}"


class AlbumDetailModal(ModalView):
    """
    Modal displaying album overview and sequential track list with Play/Shuffle buttons.
    """
    def __init__(self, album: Album, engine, on_play_track: Callable[[Track], None], **kwargs):
        super().__init__(size_hint=(1, 1), auto_dismiss=True, background_color=(0, 0, 0, 0), **kwargs)
        self.album = album
        self.engine = engine
        self.on_play_track = on_play_track

        with self.canvas.before:
            Color(*ui_theme.current_theme.bg_modal)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self.bg_rect, 'pos', self.pos),
                  size=lambda *_: setattr(self.bg_rect, 'size', self.size))

        root = BoxLayout(orientation="vertical", padding=[dp(16), dp(16)], spacing=dp(12))

        # Header back button
        header = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(44))
        btn_back = Button(text="← Back", font_size=dp(16), bold=True, size_hint=(None, 1), width=dp(80),
                          background_color=(0, 0, 0, 0), color=ui_theme.current_theme.text_secondary)
        btn_back.bind(on_release=lambda *_: self.dismiss())
        header.add_widget(btn_back)
        root.add_widget(header)

        # Album Overview Header
        album_header = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(100), spacing=dp(14))
        art = ArtworkThumbnail(corner_radius=14.0, size_hint=(None, 1), width=dp(100))
        album_header.add_widget(art)

        info_box = BoxLayout(orientation="vertical", spacing=dp(4), size_hint=(1, 1))
        title = Label(text=album.title, font_size=dp(18), bold=True, color=ui_theme.current_theme.text_primary,
                      halign="left", valign="middle", size_hint=(1, 0.4), shorten=True)
        artist = Label(text=f"By {album.artist}", font_size=dp(13), color=ui_theme.current_theme.text_secondary,
                       halign="left", valign="middle", size_hint=(1, 0.3), shorten=True)
        meta = Label(text=f"{album.track_count} tracks  •  {album.formatted_duration}", font_size=dp(12),
                     color=ui_theme.current_theme.text_muted, halign="left", valign="middle", size_hint=(1, 0.3))
        info_box.bind(width=lambda _, w: setattr(title, 'text_size', (w, None)))
        info_box.bind(width=lambda _, w: setattr(artist, 'text_size', (w, None)))
        info_box.bind(width=lambda _, w: setattr(meta, 'text_size', (w, None)))
        info_box.add_widget(title)
        info_box.add_widget(artist)
        info_box.add_widget(meta)
        album_header.add_widget(info_box)
        root.add_widget(album_header)

        # Action Buttons Row
        actions_row = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(44), spacing=dp(12))
        btn_play_album = ActionPillButton(text="Play Album", icon_symbol="▶", size_hint=(0.5, 1), is_accent=True)
        btn_play_album.bind(on_release=lambda *_: self._play_album())
        btn_shuffle_album = ActionPillButton(text="Shuffle", icon_symbol="🔀", size_hint=(0.5, 1), is_accent=False)
        btn_shuffle_album.bind(on_release=lambda *_: self._shuffle_album())
        actions_row.add_widget(btn_play_album)
        actions_row.add_widget(btn_shuffle_album)
        root.add_widget(actions_row)

        # Track List ScrollView
        scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        track_layout = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        track_layout.bind(minimum_height=track_layout.setter('height'))

        for track in album.tracks:
            card = TrackCard(track=track, on_play=self._play_track)
            track_layout.add_widget(card)

        scroll.add_widget(track_layout)
        root.add_widget(scroll)

        self.add_widget(root)

    def _play_album(self):
        self.engine.play_album(self.album)
        self.dismiss()

    def _shuffle_album(self):
        self.engine.shuffle_albums()
        self.dismiss()

    def _play_track(self, track: Track):
        self.engine.play_track_directly(track)
        self.dismiss()
