# generate_playlist_csv.py (MODIFIED)

import math
import ast
import time
import re 
import json 
import pandas as pd
import sys 
import random 

# IMPORTANT: Ensure the modified generate_playlist_input is imported
from src.processing.generate_playlist_csv_app import generate_playlist_input
# Assuming spotipy and key imports are correct
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
# from src.utils.KEYS import CLIENT_ID, CLIENT_SECRET # Placeholder

# -------------------------------------------------------
# SPOTIFY SETUP (Assumed placeholder for connection logic)
# -------------------------------------------------------
spotify_available = True 
# For UI integration, assume sp is initialized here if keys exist
try:
    auth_manager = SpotifyClientCredentials(client_id='PLACEHOLDER', client_secret='PLACEHOLDER')
    sp = spotipy.Spotify(auth_manager=auth_manager)
    sp.search(q="test", type="track", limit=1)
except Exception:
    spotify_available = False

if not spotify_available:
    from src.processing.csv_backup_generation import generate_backup_playlist

# ... (Keep all constants and helper functions here: AVG_SONG_LENGTH_MIN, create_track_fingerprint, 
#      compute_playlist_length, validate_and_extract_parameters, _build_query, 
#      _run_batched_search, fetch_mood_tracks, fetch_score_tracks, 
#      adjust_playlist_duration, export_playlist) ...
# NOTE: The body of these helper functions remains unchanged from your originals.

# Average song length in minutes
AVG_SONG_LENGTH_MIN = 5
AVG_PAGE_SPEED_MIN = 2
AVG_BOOK_LENGTH = 300

# Constants for Batching and Validation
BATCH_SIZE = 20
WAIT_TIME_SECONDS = 0.5
MAX_SEARCH_LIMIT = 50 
PRIMARY_GENRE_BASE = 'ambient' # Fixed instrumental base
FALLBACK_GENRE = 'classical' # Guaranteed safe fallback (Used if ambient search fails)
MAX_SCORE_PERCENTAGE = 0.25 # Max percentage of the playlist that can be score tracks
DURATION_THRESHOLD_MS = 5 * 60 * 1000 # 5 minutes in milliseconds

# --- HELPER FUNCTION: Create a unique fingerprint for each song ---
def create_track_fingerprint(track: dict) -> str:
    """
    Creates a standardized, lowercase identifier (fingerprint) using the main
    artist and a cleaned track title to catch duplicates across albums.
    """
    
    # 1. Clean Title: Remove common suffixes (remastered, live, deluxe, mix, etc.)
    title = track['name'].lower()
    title = re.sub(r'\s*\((remastered|live|deluxe|mix|edit|version|radio|explicit|single)\s*[^)]*\)', '', title).strip()
    title = re.sub(r'\s*\[[^\]]+\]', '', title).strip() # Remove bracketed text
    
    # 2. Get Primary Artist
    artist_name = track['artists'][0]['name'].lower()
    
    return f"{title} | {artist_name}"
# ----------------------------------------------------------------------


def compute_playlist_length(current_page: int = 0, total_pages: int = 100) -> tuple[int, float]:
    """
    Compute number of songs based on pages left and average song length.
    Returns: (num_tracks, estimated_read_time_min)
    """
    if total_pages == 0 or total_pages == None:
        readtime = AVG_BOOK_LENGTH * AVG_PAGE_SPEED_MIN
        num_tracks = max(1, math.ceil(readtime / AVG_SONG_LENGTH_MIN))
        print(f"Calculated reading time: {readtime} minutes. Target tracks: {num_tracks}")
        return num_tracks, readtime

    pages_left = max(0, total_pages - current_page)
    readtime = pages_left * AVG_PAGE_SPEED_MIN

    num_tracks = max(1, math.ceil(readtime / AVG_SONG_LENGTH_MIN))
    print(f"Calculated reading time: {readtime} minutes. Target tracks: {num_tracks}")
    # Return both number of tracks and target duration
    return num_tracks, readtime

def validate_and_extract_parameters(gemini_response_str: str) -> dict | None:
    """
    Safely parses the Gemini dictionary string and extracts required parameters.
    """
    
    # --- FIX: Clean Markdown code fences and language labels ---
    processed_str = gemini_response_str
    
    processed_str = processed_str.strip()
    if processed_str.strip().startswith('```'):
        processed_str = processed_str.replace('```python', '').replace('```', '')
        processed_str = processed_str.strip()
    # --- End Markdown Fix ---
    
    try:
        params = ast.literal_eval(processed_str)
        
        # Robustly handle list wrapper (e.g., if output is [{'k': 'v'}])
        if isinstance(params, list):
            if not params:
                return None
            params = params[0] 

        if not isinstance(params, dict):
            return None
        
        # Check for required mood keywords
        mood_keywords = params.get('mood_keywords')
        if not isinstance(mood_keywords, list) or len(mood_keywords) < 3:
            return None
            
    except Exception as e:
        return None

    # Extraction
    mood_keywords_string = " ".join([str(k).lower().strip() for k in mood_keywords])
    score_query = params.get('score_query', '')
    
    return {
        'mood_keywords_string': mood_keywords_string,
        'score_query': str(score_query).strip()
    }

def _build_query(primary_keywords: str, query_type: str) -> str:
    """
    Constructs the Spotify search query string using aggressive anti-vocal keywords.
    """
    
    ANTI_VOCAL_KEYWORDS = "instrumental"
    
    if query_type == "full":
        genre = PRIMARY_GENRE_BASE
        keywords = f"{genre} {primary_keywords}"
    elif query_type == "mood_only":
        keywords = primary_keywords
    elif query_type == "mood_fallback":
        keywords = FALLBACK_GENRE
    elif query_type == "score":
        keywords = primary_keywords
    else:
        keywords = "" 
    
    return f"{ANTI_VOCAL_KEYWORDS} {keywords}".strip()


def _run_batched_search(query: str, num_tracks: int, randomize_start: bool = False):
    """
    Internal helper to execute the batched search for a given query.
    If randomize_start is True, the search begins at a random offset to promote diversity.
    Returns (tracks, error)
    """
    all_tracks = []
    tracks_to_fetch = num_tracks
    
    # ------------------- MODIFIED LOGIC START -------------------
    initial_offset = 0
    if randomize_start:
        # Start search from a random page, up to a large buffer (e.g., 500 tracks deep)
        # This prevents constantly getting the same top-ranking tracks.
        max_random_offset = 500 
        initial_offset = random.randint(0, max_random_offset)
        print(f"Randomizing start offset to {initial_offset}.")
    
    offset = initial_offset
    # ------------------- MODIFIED LOGIC END ---------------------
    
    limit_per_call = min(BATCH_SIZE, MAX_SEARCH_LIMIT) 

    while tracks_to_fetch > 0:
        limit = min(limit_per_call, tracks_to_fetch)

        try:
            results = sp.search(
                q=query, 
                type="track", 
                limit=limit,
                offset=offset
            )
            tracks_batch = results.get('tracks', {}).get('items', [])
            
            if not tracks_batch:
                break 

            all_tracks.extend(tracks_batch)
            tracks_to_fetch -= len(tracks_batch)
            offset += len(tracks_batch)

            if tracks_to_fetch > 0:
                time.sleep(WAIT_TIME_SECONDS)
                
        except Exception as e:
            return [], str(e)

    return all_tracks, None 

def fetch_mood_tracks(mood_keywords_string: str, num_tracks: int):
    """
    Fetches the requested number of tracks using a 3-step cascading search strategy.
    """
    
    attempts = [
        # Attempt 1: Most Specific (No random offset)
        (mood_keywords_string, "full", "Most Specific (Fixed Base + Moods)", False), 
        
        # Attempt 2: Intermediate (No random offset)
        (mood_keywords_string, "mood_only", "Intermediate (Mood Only)", False),
        
        # Attempt 3: Safe Fallback (ACTIVATE RANDOM OFFSET)
        (FALLBACK_GENRE, "mood_fallback", "Safe Fallback (Ambient Only)", True) 
    ]
    
    for i, (current_moods, query_type, attempt_name, randomize) in enumerate(attempts):
        
        current_query = _build_query(current_moods, query_type)
        
        # We fetch tracks needed for the mood budget, fetching 50% extra to account for duplicates
        search_limit = int(num_tracks * 1.5)
        
        # Pass the randomization flag to the search runner
        tracks, error = _run_batched_search(current_query, search_limit, randomize_start=randomize)
        
        if tracks:
            return tracks, current_query

        if error:
            print(f"API Error detected in attempt {i+1}: {error}. Moving to next attempt.")
            continue

    return [], current_query # Returns empty list if all attempts fail


def fetch_score_tracks(score_query: str, num_tracks: int):
    """ Fetches tracks from a specific movie score. """
    current_query = _build_query(score_query, "score") 
    search_limit = int(num_tracks * 1.5)
    
    # We do NOT randomize the score search, as we want the *best* score tracks first.
    tracks, error = _run_batched_search(current_query, search_limit, randomize_start=False)
    
    if error:
        print(f"API Error detected during score search: {error}")
        return [], current_query
    
    return tracks, current_query

# --- Adjusts playlist duration against estimated read time ---
def adjust_playlist_duration(tracks: list, target_time_min: float, mood_keywords_string: str) -> list:
    
    target_time_ms = target_time_min * 60 * 1000
    actual_time_ms = sum(track['duration_ms'] for track in tracks)
    
    # Calculate the duration difference
    diff_ms = actual_time_ms - target_time_ms
    diff_min = diff_ms / 60000
    
    print(f"\n--- Duration Validation ---")
    print(f"Target Read Time: {target_time_min:.1f} min")
    print(f"Actual Playlist Time: {actual_time_ms / 60000:.1f} min")

    if abs(diff_min) <= 5:
        print("Playlist duration is within the 5-minute threshold. No adjustment needed.")
        return tracks
    
    # --- Case A: Playlist is Too Long (Remove Songs) ---
    if diff_min > 5:
        print(f"Playlist is too long by {diff_min:.1f} minutes. Removing tracks...")
        
        tracks.sort(key=lambda t: t['duration_ms'], reverse=True)
        
        while diff_min > 5 and len(tracks) > 1:
            removed_track = tracks.pop(0)
            actual_time_ms -= removed_track['duration_ms']
            diff_min = (actual_time_ms - target_time_ms) / 60000
        
        print(f"Removed tracks. New time difference: {diff_min:.1f} minutes. Total tracks: {len(tracks)}")
        return tracks

    # --- Case B: Playlist is Too Short (Add Songs) ---
    elif diff_min < -5:
        print(f"Playlist is too short by {abs(diff_min):.1f} minutes. Adding replacement tracks...")
        
        time_to_add_min = abs(diff_min)
        num_to_add = max(1, math.ceil(time_to_add_min / AVG_SONG_LENGTH_MIN))
        
        print(f"Requesting {num_to_add} replacement tracks.")
        
        # We must use the safest search (Fallback) and activate randomization for diversity
        raw_new_tracks, query = _run_batched_search(_build_query(FALLBACK_GENRE, "fallback"), num_to_add * 2, randomize_start=True) 

        track_fingerprints = set(create_track_fingerprint(t) for t in tracks)
        
        for track in raw_new_tracks:
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                tracks.append(track)
                track_fingerprints.add(fingerprint)
                actual_time_ms += track['duration_ms']
                diff_min = (actual_time_ms - target_time_ms) / 60000
                
                if abs(diff_min) <= 5:
                    break
        
        print(f"Added tracks. New time difference: {diff_min:.1f} minutes. Total tracks: {len(tracks)}")
        return tracks
    
    return tracks
# -----------------------------------------------------------------------------------


def export_playlist(tracks: list, export_format: str, book_title: str):
    """
    Exports the final list of unique tracks to a CSV or JSON file.
    """
    if not tracks:
        print("No tracks to export.")
        return

    data = []
    for track in tracks:
        track_data = {
            'track_name': track['name'],
            'artist_name': track['artists'][0]['name'],
            'album_name': track['album']['name'],
            'duration_minutes': f"{track['duration_ms'] // 60000}:{(track['duration_ms'] % 60000) // 1000:02d}",
            'spotify_url': track['external_urls']['spotify']
        }
        data.append(track_data)

    # Sanitize book title for filename
    safe_title = re.sub(r'[^\w\-_\. ]', '', book_title.lower().replace(' ', '_'))
    filename = f"{safe_title}_playlist.{export_format}"
    
    if export_format == 'csv':
        try:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"\n✅ Playlist successfully exported to {filename} (CSV).")
        except NameError:
            print("\nError: pandas library not found. Cannot export to CSV.")
    
    elif export_format == 'json':
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"\n✅ Playlist successfully exported to {filename} (JSON).")
    
    else:
        print("\nExport skipped.")
# -----------------------------------------------------------------------------------
# 🔥 UI-FRIENDLY FUNCTION (Replaces original generate_playlist) 🔥
def get_final_tracks(book_title: str, author_name: str, total_pages: int):
    """
    Generate a Spotify playlist based on UI parameters. 
    Returns a standardized list of tracks for Streamlit embedding.
    """

    if not spotify_available:
        print("\nFailed to connect to Spotify. Aborting playlist creation.")
        return []

    # Step 1: Get Gemini keywords and page info (Modified call)
    try:
        data = generate_playlist_input(
            book=book_title, 
            author=author_name, 
            total_pages=total_pages,
            suppress_input=True
        )
    except Exception as e:
        print(f"Error during Gemini keyword generation: {e}")
        return []

    # Step 2: Compute target
    current_page = 0 
    total_pages_used = data.get("total_pages", 0) 
    num_tracks_target, target_read_time_min = compute_playlist_length(current_page=current_page, total_pages=total_pages_used)
    
    # --- Steps 3-6: RETRY LOOP, VALIDATION, BUDGET, SEARCH ---
    validated_data = None
    gemini_response_str = data.get("response", "{}")
    
    for attempt in range(1, 3):
        # Removal of print statements
        
        if attempt == 2:
            try:
                # Use the modified function again for retry
                data = generate_playlist_input(
                    book=book_title, 
                    author=author_name, 
                    total_pages=total_pages,
                    suppress_input=True
                ) 
                gemini_response_str = data.get("response", "{}")
            except Exception as e:
                break

        validated_data = validate_and_extract_parameters(gemini_response_str)
        
        if validated_data:
            break
        elif attempt == 1:
            time.sleep(1) 
        else:
            break

    if not validated_data:
        return []
    
    mood_keywords_string = validated_data['mood_keywords_string']
    score_query = validated_data['score_query']
    
    # Budget Calculation (Keep as is)
    score_budget = min(math.ceil(num_tracks_target * 0.25), num_tracks_target)
    
    # Sequential Search and Assembly (Keep existing logic)
    final_tracks = []
    track_fingerprints = set()
    successful_query = ""
    raw_score_tracks_ids = set() 
    
    # ... (PHASE 1: SCORE SEARCH LOGIC HERE) ...
    # ... (PHASE 2: MOOD SEARCH LOGIC HERE) ...
    
    # --- Step 7: Duration Adjustment ---
    final_tracks = adjust_playlist_duration(final_tracks, target_read_time_min, mood_keywords_string)
    
    # --- Step 8: Final Check ---
    if not final_tracks:
        return []

    # ----------------------------------------------------------------------------
    # 🔥 Step 9: CRITICAL ADJUSTMENT - STANDARDIZE DATA FOR STREAMLIT UI 🔥
    # ----------------------------------------------------------------------------
    
    ui_ready_tracks = []
    for track in final_tracks:
        try:
            # Extract required keys and standardize the output format
            spotify_url = track['external_urls']['spotify']
            
            ui_ready_tracks.append({
                'track_name': track.get('name', 'Unknown Title'),
                'artist_name': track['artists'][0]['name'],
                'spotify_url': spotify_url # <-- The key Streamlit app.py looks for
            })
            
        except (KeyError, IndexError):
            continue 
            
    # Return the standardized list
    return ui_ready_tracks

# --- CLI entry point (Retained for terminal use) ---
def generate_playlist_cli():
    """ Runs the original CLI version of the playlist generator. """
    
    if not spotify_available:
        total_pages = int(input("Enter total number of pages (optional, press enter if unknown): ") or 250)
        tracks = generate_backup_playlist(total_pages=total_pages)
        return

    data = generate_playlist_input()
    tracks = get_final_tracks(data["book"], data["author"], data["total_pages"])

    if tracks:
        print("\n🎶 Generated Playlist Summary 🎶")
        
        for i, track in enumerate(tracks, start=1):
             print(f"{i}. {track['track_name']} – {track['artist_name']}")
             print(f"   Spotify URL: {track['spotify_url']}\n")
        
        export_choice = input("Export playlist? (c = CSV, j = JSON, n = No): ").lower().strip()
        
        if export_choice == 'j':
             with open(f"{data['book']}_playlist.json", 'w') as f:
                json.dump(tracks, f, indent=4)
             print(f"\n✅ Playlist successfully exported to {data['book']}_playlist.json (JSON).")
        else:
            print("\nExport skipped.")


if __name__ == "__main__":
    generate_playlist_cli()