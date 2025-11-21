"""
backup_playlist_generator.py
Creates a playlist from backup CSVs if Spotify API fails or credentials are missing.
"""

import os
import random
import math
import pandas as pd

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Fallback genre
DEFAULT_GENRE = "instrumental"

# Mapping between user input and CSV filenames
GENRE_MAP = {
    "b": "biography_backup.csv",
    "c": "classics_backup.csv",
    "cf": "contemporary_fiction_backup.csv",
    "d": "dystopian_backup.csv",
    "f": "fantasy_backup.csv",
    "g": "graphic_novels_backup.csv",
    "hf": "historical_fiction_backup.csv",
    "h": "horror_backup.csv",
    "i": "instrumental_backup.csv",
    "lf": "literary_fiction_backup.csv",
    "m": "mystery_backup.csv",
    "r": "romance_backup.csv",
    "s": "science_fiction_backup.csv",
    "t": "textbook_backup.csv",
    "th": "thriller_backup.csv",
    "ya": "young_adult_backup.csv",
    "o": DEFAULT_GENRE,  # 'other' falls back to instrumental
}

def compute_playlist_length(total_pages: int = 100, current_page: int = 0):
    """Same logic as main generator: reading time = pages_left * 2 minutes, ~5 min/song."""
    AVG_SONG_LENGTH_MIN = 5
    AVG_PAGE_SPEED_MIN = 2

    if total_pages == 0:
        return 20

    pages_left = max(0, total_pages - current_page)
    readtime = pages_left * AVG_PAGE_SPEED_MIN

    return max(1, math.ceil(readtime / AVG_SONG_LENGTH_MIN))


def _safe_load_csv(filename: str) -> pd.DataFrame | None:
    """Loads a CSV, returns None if missing."""

    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"⚠️ CSV not found: {path}")
        return None

    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"⚠️ Error reading CSV {filename}: {e}")
        return None


def _pick_tracks(df: pd.DataFrame, num: int):
    """Randomly picks N tracks from the backup CSV."""
    if df is None or df.empty:
        return []

    df = df.sample(frac=1).reset_index(drop=True)  # shuffle
    return df.head(num).to_dict(orient="records")


def generate_backup_playlist(total_pages: int = 250):
    """
    Main backup playlist generator.
    Used when Spotify API credentials are missing OR Spotify errors occur.
    """

    print("\n⚠️ Spotify unavailable — switching to BACKUP playlist generator.\n")

    print("Select your book's genre:")
    print("  b = biography")
    print("  c = classics")
    print("  cf = contemporary fiction")
    print("  d = dystopian")
    print("  f = fantasy")
    print("  g = graphic novels")
    print("  hf = historical fiction")
    print("  h = horror")
    print("  lf = literary fiction")
    print("  m = mystery")
    print("  r = romance")
    print("  s = science fiction")
    print("  t = textbook")
    print("  th = thriller")
    print("  ya = young adult")
    print("  o = other / unknown (defaults to instrumental)")
    
    user_choice = input("\nEnter a genre code: ").strip().lower()

    filename = GENRE_MAP.get(user_choice, GENRE_MAP["o"])
    df = _safe_load_csv(filename)

    # Compute length
    num_tracks = compute_playlist_length(total_pages=total_pages)

    # Try picking from selected CSV
    tracks = _pick_tracks(df, num_tracks)

    if not tracks:
        # Fallback to DEFAULT_GENRE
        print("\n⚠️ Selected genre has no viable tracks. Falling back to instrumental...\n")
        df2 = _safe_load_csv(f"{DEFAULT_GENRE}_backup.csv")
        tracks = _pick_tracks(df2, num_tracks)

    print("\n🎶 BACKUP PLAYLIST GENERATED 🎶")
    print(f"Using CSV: {filename}")
    print(f"Tracks: {len(tracks)} ≈ (target {num_tracks})\n")

    for i, t in enumerate(tracks, start=1):
        title = t.get("track_name", "Unknown Title")
        artist = t.get("artist_name", "Unknown Artist")
        duration = t.get("duration", "unknown")  # optional: you may have a duration column or leave unknown
        print(f"{i}. {title} — {artist} ({duration})")

    return tracks
