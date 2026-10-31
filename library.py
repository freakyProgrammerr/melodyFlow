from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Set
from pathlib import Path


@dataclass
class Track:
    file_path: str
    file_name: str
    extension: str
    file_size: int
    title: str
    artist: str
    album: str
    duration: float
    track_number: Optional[int] = None
    total_tracks: Optional[int] = None
    disc_number: Optional[int] = None
    year: Optional[int] = None
    genre: str = "Unknown Genre"
    has_cover: bool = False
    art_path: Optional[str] = None
    is_single: bool = False

    @property
    def id(self) -> str:
        return self.file_path

    @property
    def formatted_duration(self) -> str:
        mins = int(self.duration // 60)
        secs = int(self.duration % 60)
        return f"{mins}:{secs:02d}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Track:
        return cls(**data)


@dataclass
class Album:
    title: str
    artist: str
    year: Optional[int] = None
    genre: str = "Unknown Genre"
    tracks: List[Track] = field(default_factory=list)
    art_path: Optional[str] = None

    @property
    def key(self) -> str:
        return f"{self.artist.lower().strip()}::{self.title.lower().strip()}"

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def total_duration(self) -> float:
        return sum(t.duration for t in self.tracks)

    @property
    def formatted_duration(self) -> str:
        total = int(self.total_duration)
        mins = total // 60
        secs = total % 60
        if mins >= 60:
            hrs = mins // 60
            mins = mins % 60
            return f"{hrs} hr {mins} min"
        return f"{mins}:{secs:02d}"

    def sort_tracks(self) -> None:
        """Sort tracks by disc number, then track number, then title."""
        self.tracks.sort(key=lambda t: (
            t.disc_number or 1,
            t.track_number if t.track_number is not None else 999,
            t.title.lower()
        ))

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "artist": self.artist,
            "year": self.year,
            "genre": self.genre,
            "art_path": self.art_path,
            "tracks": [t.to_dict() for t in self.tracks]
        }

    @classmethod
    def from_dict(cls, data: dict) -> Album:
        tracks = [Track.from_dict(t) for t in data.get("tracks", [])]
        return cls(
            title=data["title"],
            artist=data["artist"],
            year=data.get("year"),
            genre=data.get("genre", "Unknown Genre"),
            tracks=tracks,
            art_path=data.get("art_path")
        )


@dataclass
class Artist:
    name: str
    albums: List[Album] = field(default_factory=list)
    singles: List[Track] = field(default_factory=list)

    @property
    def all_tracks(self) -> List[Track]:
        tracks = list(self.singles)
        for album in self.albums:
            tracks.extend(album.tracks)
        return tracks

    @property
    def track_count(self) -> int:
        return len(self.all_tracks)


class MusicLibrary:
    """
    Organizes the local audio collection into Albums, Singles, and Artists.
    Provides fast indexing, search, and categorization.
    """

    def __init__(self, min_album_tracks: int = 2):
        self.min_album_tracks = min_album_tracks
        self.tracks: List[Track] = []
        self.albums: List[Album] = []
        self.singles: List[Track] = []
        self.artists: Dict[str, Artist] = {}

    @property
    def total_tracks(self) -> int:
        return len(self.tracks)

    @property
    def all_tracks(self) -> List[Track]:
        return self.tracks

    def load_from_metadata_list(self, raw_metadata_list: List[dict]) -> None:
        """Populate the library from raw scanner metadata dicts."""
        self.tracks = [Track.from_dict(meta) for meta in raw_metadata_list]
        self._organize_library()

    def _organize_library(self) -> None:
        """Classify tracks into Albums and Singles, and group by Artist."""
        self.albums.clear()
        self.singles.clear()
        self.artists.clear()

        # Step 1: Group potential album tracks by (artist, album_title)
        album_groups: Dict[str, List[Track]] = {}
        for track in self.tracks:
            album_name = track.album.strip()
            # If no album name, it is immediately a single
            if not album_name:
                continue

            # Check if tagged explicitly as a single
            lower_album = album_name.lower()
            if lower_album in {"single", "singles", f"{track.title.lower()} - single", f"{track.title.lower()} (single)"}:
                continue

            key = f"{track.artist.lower().strip()}::{album_name.lower()}"
            album_groups.setdefault(key, []).append(track)

        # Step 2: Separate true Albums from Singles
        album_track_ids: Set[str] = set()

        for key, group in album_groups.items():
            # A group qualifies as an Album if it has >= min_album_tracks
            # OR if total_tracks > 1 indicated in tags
            has_multi_tracks = len(group) >= self.min_album_tracks
            indicated_total_album = any(
                t.total_tracks is not None and t.total_tracks > 1 for t in group
            )

            if has_multi_tracks or indicated_total_album:
                rep_track = group[0]
                album_title = rep_track.album
                artist_name = rep_track.artist
                year = next((t.year for t in group if t.year is not None), None)
                genre = next((t.genre for t in group if t.genre != "Unknown Genre"), "Unknown Genre")
                art_path = next((t.art_path for t in group if t.art_path), None)

                album = Album(
                    title=album_title,
                    artist=artist_name,
                    year=year,
                    genre=genre,
                    tracks=group,
                    art_path=art_path
                )
                album.sort_tracks()
                self.albums.append(album)

                for t in group:
                    t.is_single = False
                    album_track_ids.add(t.id)

        # Sort albums alphabetically by artist then title
        self.albums.sort(key=lambda a: (a.artist.lower(), a.title.lower()))

        # Step 3: Any track not part of a recognized Album is a Single
        for track in self.tracks:
            if track.id not in album_track_ids:
                track.is_single = True
                self.singles.append(track)

        self.singles.sort(key=lambda t: (t.artist.lower(), t.title.lower()))

        # Step 4: Group into Artists
        for album in self.albums:
            artist_key = album.artist.strip() or "Unknown Artist"
            if artist_key not in self.artists:
                self.artists[artist_key] = Artist(name=artist_key)
            self.artists[artist_key].albums.append(album)

        for single in self.singles:
            artist_key = single.artist.strip() or "Unknown Artist"
            if artist_key not in self.artists:
                self.artists[artist_key] = Artist(name=artist_key)
            self.artists[artist_key].singles.append(single)

    def search(self, query: str) -> Dict[str, list]:
        """
        Real-time search across song titles, artists, and albums.
        Returns matching tracks, albums, and artists.
        """
        q = query.lower().strip()
        if not q:
            return {"tracks": [], "albums": [], "artists": []}

        matched_tracks = [
            t for t in self.tracks
            if q in t.title.lower() or q in t.artist.lower() or q in t.album.lower()
        ]

        matched_albums = [
            a for a in self.albums
            if q in a.title.lower() or q in a.artist.lower()
        ]

        matched_artists = [
            art for art in self.artists.values()
            if q in art.name.lower()
        ]

        return {
            "tracks": matched_tracks,
            "albums": matched_albums,
            "artists": matched_artists
        }

    def save_cache(self, cache_file_path: str) -> None:
        """Persist scanned library to a JSON cache file for instant loading."""
        os.makedirs(os.path.dirname(os.path.abspath(cache_file_path)), exist_ok=True)
        data = {
            "version": 1,
            "tracks": [t.to_dict() for t in self.tracks]
        }
        with open(cache_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_cache(self, cache_file_path: str) -> bool:
        """Load library from JSON cache file."""
        if not os.path.exists(cache_file_path):
            return False
        try:
            with open(cache_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw_tracks = data.get("tracks", [])
            self.tracks = [Track.from_dict(t) for t in raw_tracks]
            self._organize_library()
            return True
        except Exception:
            return False

    def summary(self) -> dict:
        """Return high-level library stats."""
        total_duration = sum(t.duration for t in self.tracks)
        mins = int(total_duration // 60)
        return {
            "total_tracks": len(self.tracks),
            "total_albums": len(self.albums),
            "total_singles": len(self.singles),
            "total_artists": len(self.artists),
            "total_duration_minutes": mins
        }
