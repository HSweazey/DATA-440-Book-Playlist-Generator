"""
config.py
----------
Central configuration file for DATA400 final project: book playlist generator. 

This module defines project-wide constants and paths that can be imported
throughout the codebase for consistency. It also provides lightweight
helpers for locating and verifying directories.
"""

from pathlib import Path

# === PROJECT ROOT ===

# Assumes this file is located at: <project_root>/src/utils/config.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]


# === DIRECTORIES ===

DATA_DIR = PROJECT_ROOT / "data"
BOOKS_DIR = DATA_DIR / "split_books"
PLAYLISTS_DIR = DATA_DIR / "playlists"
SRC_DIR = PROJECT_ROOT / "src"

# make sure expected directories exist (non-fatal)
for path in [DATA_DIR, BOOKS_DIR, PLAYLISTS_DIR]:
    path.mkdir(parents=True, exist_ok=True)


# === CONSTANTS ===

# assuming average adult reading speed ≈ 1 page per minute
AVG_READING_SPEED_PPM = 1.0