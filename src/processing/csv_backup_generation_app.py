"""
backup_playlist_generator.py
Creates a playlist from backup CSVs if Spotify API fails or credentials are missing.
"""

import os
import math
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Fallback Genre
DEFAULT_GENRE = "instrumental"

# 1. User Input Mapping
GENRE_MAP = {
    "b": "biography_backup.csv",
    "c": "classics_backup.csv",
    "cf": "contemporary_fiction_backup.csv",
    "d": "dystopian_backup.csv",
    "f": "fantasy_backup.csv",
    "g": "graphic_novels_backup.csv",
    "hf": "historical_fiction_backup.csv",
    "h": "horror_backup.csv",
    "lf": "literary_fiction_backup.csv",
    "m": "mystery_backup.csv",
    "r": "romance_backup.csv",
    "s": "science_fiction_backup.csv",
    "t": "textbook_backup.csv",
    "th": "thriller_backup.csv",
    "ya": "young_adult_backup.csv",
    "o": "instrumental_backup.csv", 
}

# 2. UI Dropdown Menu
UI_GENRE_OPTIONS = {
    "Instrumental / Other": "o",
    "Biography": "b",
    "Classics": "c",
    "Contemporary Fiction": "cf",
    "Dystopian": "d",
    "Fantasy": "f",
    "Graphic Novels": "g",
    "Historical Fiction": "hf",
    "Horror": "h",
    "Literary Fiction": "lf",
    "Mystery": "m",
    "Romance": "r",
    "Science Fiction": "s",
    "Textbook / Non-Fiction": "t",
    "Thriller": "th",
    "Young Adult": "ya"
}

def compute_playlist_length(total_pages: int = 100, current_page: int = 0):
    AVG_SONG_LENGTH_MIN = 5
    AVG_PAGE_SPEED_MIN = 2
    if total_pages == 0: return 20
    pages_left = max(0, total_pages - current_page)
    readtime = pages_left * AVG_PAGE_SPEED_MIN
    return max(1, math.ceil(readtime / AVG_SONG_LENGTH_MIN))

def _safe_load_csv(filename: str) -> pd.DataFrame | None:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        if os.path.exists(filename): return pd.read_csv(filename)
        print(f"⚠️ CSV not found: {path}")
        return None
    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"⚠️ Error reading CSV {filename}: {e}")
        return None

def _pick_tracks(df: pd.DataFrame, num: int):
    if df is None or df.empty: return []
    try:
        df = df.sample(frac=1).reset_index(drop=True)
        return df.head(num).to_dict(orient="records")
    except Exception:
        return []

def generate_backup_playlist(total_pages: int = 250, genre_code: str = 'o'):
    """
    UI-Friendly Backup Generator
    """
    print(f"\n⚠️ Using BACKUP playlist generator for code: {genre_code}")
    
    filename = GENRE_MAP.get(genre_code, GENRE_MAP["o"])
    df = _safe_load_csv(filename)
    
    if df is None or df.empty:
        if filename != "instrumental_backup.csv": 
            print("⚠️ Selected genre CSV is empty. Falling back to instrumental.")
            df = _safe_load_csv("instrumental_backup.csv")
        else:
            pass 

    num_tracks = compute_playlist_length(total_pages=total_pages)
    tracks = _pick_tracks(df, num_tracks)

    return tracks