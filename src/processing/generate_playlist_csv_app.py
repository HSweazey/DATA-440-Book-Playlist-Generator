import math
import ast
import time
import re 
import json 
import pandas as pd
import sys 
import random 
import streamlit as st

from src.processing.generate_playlist_input_app import generate_playlist_input

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# -------------------------------------------------------
# SPOTIFY SETUP
# -------------------------------------------------------
spotify_available = True
try:
    from src.utils.KEYS import CLIENT_ID, CLIENT_SECRET
    try:
        auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        sp.search(q="test", type="track", limit=1)
    except Exception as e:
        print(f"⚠️ Spotify connection failed. Error: {e}")
        spotify_available = False
except ImportError as e:
    print(f"⚠️ Spotify keys not found. Error: {e}")
    spotify_available = False

# Import backup generator
from src.processing.csv_backup_generation_app import generate_backup_playlist

# Constants
AVG_SONG_LENGTH_MIN = 5
AVG_PAGE_SPEED_MIN = 2
AVG_BOOK_LENGTH = 300
BATCH_SIZE = 20
WAIT_TIME_SECONDS = 0.5
MAX_SEARCH_LIMIT = 50 
PRIMARY_GENRE_BASE = 'ambient' 
FALLBACK_GENRE = 'classical' 
MAX_SCORE_PERCENTAGE = 0.25 
DURATION_THRESHOLD_MS = 5 * 60 * 1000 

# --- HELPER FUNCTIONS ---
def create_track_fingerprint(track: dict) -> str:
    title = track.get('name', 'Unknown').lower()
    artist_name = track['artists'][0]['name'].lower() if 'artists' in track else track.get('artist_name', 'Unknown').lower()
    return f"{title} | {artist_name}"

def compute_playlist_length(current_page: int = 0, total_pages: int = 100) -> tuple[int, float]:
    if total_pages == 0 or total_pages == None:
        readtime = AVG_BOOK_LENGTH * AVG_PAGE_SPEED_MIN
        num_tracks = max(1, math.ceil(readtime / AVG_SONG_LENGTH_MIN))
        return num_tracks, readtime
    pages_left = max(0, total_pages - current_page)
    readtime = pages_left * AVG_PAGE_SPEED_MIN
    num_tracks = max(1, math.ceil(readtime / AVG_SONG_LENGTH_MIN))
    return num_tracks, readtime

def validate_and_extract_parameters(gemini_response_str: str) -> dict | None:
    processed_str = gemini_response_str.strip()
    if processed_str.strip().startswith('```'):
        processed_str = processed_str.replace('```python', '').replace('```', '').strip()
    try:
        params = ast.literal_eval(processed_str)
        if isinstance(params, list):
            if not params: return None
            params = params[0] 
        if not isinstance(params, dict): return None
        mood_keywords = params.get('mood_keywords')
        if not isinstance(mood_keywords, list) or len(mood_keywords) < 3:
            return None
    except Exception:
        return None
    mood_keywords_string = " ".join([str(k).lower().strip() for k in mood_keywords])
    score_query = params.get('score_query', '')
    return {'mood_keywords_string': mood_keywords_string, 'score_query': str(score_query).strip()}

def _build_query(primary_keywords: str, query_type: str) -> str:
    """
    Constructs the Spotify search query string using aggressive anti-vocal keywords.
    """
    
    ANTI_VOCAL_KEYWORDS = "instrumental"
    
    if query_type == "full":
        # Current: 'instrumental ambient heroic epic grand'
        genre = PRIMARY_GENRE_BASE
        keywords = f"{genre} {primary_keywords}"
    
    elif query_type == "mood_only":
        # --- MODIFIED LINE ---
        # WAS: keywords = primary_keywords
        # NOW: keywords = f"{PRIMARY_GENRE_BASE} {primary_keywords}"
        keywords = f"{PRIMARY_GENRE_BASE} {primary_keywords}"
        # This enforces 'ambient' even on the second attempt.
        # Example Query: 'instrumental ambient heroic epic grand' 
        
    elif query_type == "mood_fallback":
        # This already uses the fallback genre (e.g., 'classical'), which should remain as a last resort.
        keywords = FALLBACK_GENRE
    
    elif query_type == "score":
        keywords = primary_keywords
    else:
        keywords = "" 
    
    return f"{ANTI_VOCAL_KEYWORDS} {keywords}".strip()

def _run_batched_search(query: str, num_tracks: int, randomize_start: bool = False):
    all_tracks = []
    tracks_to_fetch = num_tracks
    initial_offset = 0
    if randomize_start:
        initial_offset = random.randint(0, 500)
    offset = initial_offset
    limit_per_call = min(BATCH_SIZE, MAX_SEARCH_LIMIT) 

    while tracks_to_fetch > 0:
        limit = min(limit_per_call, tracks_to_fetch)
        # ... try block starts ...
        try:
            results = sp.search(
                q=query, 
                type="track", 
                limit=limit,
                offset=offset
            )
            tracks_batch = results.get('tracks', {}).get('items', [])
            
            # --- CRITICAL FIX 1: Break the loop if Spotify finds nothing ---
            if not tracks_batch:
                break # <--- This prevents an infinite loop if search is exhausted

            all_tracks.extend(tracks_batch)
            
            # --- CRITICAL FIX 2: Update variables for the next iteration ---
            tracks_to_fetch -= len(tracks_batch)
            offset += len(tracks_batch)

            if tracks_to_fetch > 0:
                # Add a small Streamlit-friendly sleep if you need it, though optional
                time.sleep(WAIT_TIME_SECONDS)
                
        except Exception as e:
            # ... (Keep existing error handling and return) ...
            if 'sp' in globals() and sp:
                st.error(f"❌ Spotify Search Error: Search query failed. Details: {e}")
            else:
                 st.error(f"❌ Spotify Search Error: Client not initialized. Details: {e}")
            return [], str(e)

    return all_tracks, None

def _store_spotify_debug(tracks: list, query: str, query_type: str):
    st.session_state['debug_info']['spotify_query'] = query
    st.session_state['debug_info']['tracks_returned'] = len(tracks)
    st.session_state['debug_info']['successful_attempt'] = query_type

def fetch_mood_tracks(mood_keywords_string: str, num_tracks: int):
    attempts = [
        (mood_keywords_string, "full", "Most Specific", False), 
        (mood_keywords_string, "mood_only", "Intermediate", False),
        (FALLBACK_GENRE, "mood_fallback", "Safe Fallback", True) 
    ]
    for current_moods, query_type, attempt_name, randomize in attempts:
        current_query = _build_query(current_moods, query_type)
        tracks, error = _run_batched_search(current_query, int(num_tracks * 1.5), randomize_start=randomize)
        
        if tracks: 
            _store_spotify_debug(tracks, current_query, attempt_name) # <-- ADDED
            return tracks, current_query
    
    # If all fail, store the last attempt's failure
    _store_spotify_debug([], current_query, "All Failed") # <-- ADDED
    return [], current_query

def fetch_score_tracks(score_query: str, num_tracks: int):
    current_query = _build_query(score_query, "score") 
    tracks, error = _run_batched_search(current_query, int(num_tracks * 1.5), randomize_start=False)
    
    # Store success or failure
    if tracks:
        _store_spotify_debug(tracks, current_query, "Score Search") # <-- ADDED
    else:
        _store_spotify_debug([], current_query, "Score Search Failed") # <-- ADDED

    return tracks, current_query

def adjust_playlist_duration(tracks: list, target_time_min: float, mood_keywords_string: str) -> list:
    # Handle backup tracks that might lack 'duration_ms'
    safe_tracks = [t for t in tracks if 'duration_ms' in t]
    if len(safe_tracks) < len(tracks): return tracks # Skip logic if data is missing
    
    target_time_ms = target_time_min * 60 * 1000
    actual_time_ms = sum(track['duration_ms'] for track in safe_tracks)
    diff_min = (actual_time_ms - target_time_ms) / 60000
    
    if abs(diff_min) <= 5: return safe_tracks
    
    if diff_min > 5:
        safe_tracks.sort(key=lambda t: t['duration_ms'], reverse=True)
        while diff_min > 5 and len(safe_tracks) > 1:
            removed_track = safe_tracks.pop(0)
            actual_time_ms -= removed_track['duration_ms']
            diff_min = (actual_time_ms - target_time_ms) / 60000
        return safe_tracks
    elif diff_min < -5 and spotify_available:
        time_to_add_min = abs(diff_min)
        num_to_add = max(1, math.ceil(time_to_add_min / AVG_SONG_LENGTH_MIN))
        raw_new_tracks, _ = _run_batched_search(_build_query(FALLBACK_GENRE, "fallback"), num_to_add * 2, randomize_start=True) 
        track_fingerprints = set(create_track_fingerprint(t) for t in safe_tracks)
        for track in raw_new_tracks:
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                safe_tracks.append(track)
                track_fingerprints.add(fingerprint)
                actual_time_ms += track['duration_ms']
                diff_min = (actual_time_ms - target_time_ms) / 60000
                if abs(diff_min) <= 5: break
        return safe_tracks
    return safe_tracks

# -----------------------------------------------------------------------------------
# 🔥 UI-FRIENDLY FUNCTION 🔥
# -----------------------------------------------------------------------------------
def get_final_tracks(book_title: str, author_name: str, total_pages: int):
    """
    Generate a Spotify playlist based on UI parameters. 
    """
    # 1. Fallback to Backup if Spotify is dead
    if not spotify_available:
        print("\nSpotify unavailable. Generating backup playlist...")
        # Default to 'instrumental' (genre code 'i') or 'o' (other) for UI
        return generate_backup_playlist(total_pages=total_pages, genre_code='o')

    # 2. Run Gemini
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

    current_page = 0 
    total_pages_used = data.get("total_pages", 0) 
    num_tracks_target, target_read_time_min = compute_playlist_length(current_page=current_page, total_pages=total_pages_used)
    
    # --- NEW DEBUG CAPTURE: Target Metrics ---
    st.session_state['debug_info']['target_metrics'] = {
        'target_read_time_min': f"{target_read_time_min:.1f}",
        'num_tracks_target': num_tracks_target,
    }

    validated_data = None
    gemini_response_str = data.get("response", "{}")
    
    # 3. Parse Gemini Result
    for attempt in range(1, 3):
        if attempt == 2:
            try:
                data = generate_playlist_input(
                    book=book_title, 
                    author=author_name, 
                    total_pages=total_pages,
                    suppress_input=True
                ) 
                gemini_response_str = data.get("response", "{}")
            except Exception:
                break
        validated_data = validate_and_extract_parameters(gemini_response_str)
        if validated_data: break
        elif attempt == 1: time.sleep(1) 

    # If Gemini fails entirely, use fallback logic? Or return empty?
    # For now, if keywords fail, we can't search Spotify effectively.
    if not validated_data: 
        print("Gemini failed. Returning backup.")
        return generate_backup_playlist(total_pages=total_pages, genre_code='o')
    
    mood_keywords_string = validated_data['mood_keywords_string']
    score_query = validated_data['score_query']
    
    score_budget = min(math.ceil(num_tracks_target * MAX_SCORE_PERCENTAGE), num_tracks_target)
    final_tracks = []
    track_fingerprints = set()

    # 4. Spotify Search
    if score_query and score_budget > 0:
        raw_score_tracks, query = fetch_score_tracks(score_query, score_budget)
        for track in raw_score_tracks:
            if len(final_tracks) >= score_budget: break
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                final_tracks.append(track)
                track_fingerprints.add(fingerprint)

    tracks_needed_for_mood = num_tracks_target - len(final_tracks)
    if tracks_needed_for_mood > 0:
        raw_mood_tracks, query = fetch_mood_tracks(mood_keywords_string, tracks_needed_for_mood)
        for track in raw_mood_tracks:
            if len(final_tracks) >= num_tracks_target: break
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                final_tracks.append(track)
                track_fingerprints.add(fingerprint)

    final_tracks = adjust_playlist_duration(final_tracks, target_read_time_min, mood_keywords_string)
    if not final_tracks: 
         return generate_backup_playlist(total_pages=total_pages, genre_code='o')

    # --- NEW DEBUG CAPTURE: Pre-Adjustment Length ---
    st.session_state['debug_info']['pre_adjustment_length'] = len(final_tracks)
    # -----------------------------------------------

    # 5. Duration Adjustment
    final_tracks = adjust_playlist_duration(final_tracks, target_read_time_min, mood_keywords_string)
    
    # --- NEW DEBUG CAPTURE: Post-Adjustment Length ---
    st.session_state['debug_info']['post_adjustment_length'] = len(final_tracks)
    # ------------------------------------------------
    
    # 5. Standardize Output for UI
    ui_ready_tracks = []
    for track in final_tracks:
        # Handle Spotify API structure
        if 'external_urls' in track and 'spotify' in track['external_urls']:
            url = track['external_urls']['spotify']
        # Handle Backup CSV structure
        elif 'spotify_url' in track:
            url = track['spotify_url']
        else:
            url = None

        if url:
            # Robustly get names whether from API object or flat CSV dict
            t_name = track.get('name', track.get('track_name', 'Unknown Title'))
            
            # Handle Artist: API returns list of dicts, CSV returns string
            if 'artists' in track and isinstance(track['artists'], list):
                a_name = track['artists'][0]['name']
            else:
                a_name = track.get('artist_name', 'Unknown Artist')

            ui_ready_tracks.append({
                'track_name': t_name,
                'artist_name': a_name,
                'spotify_url': url 
            })
            
    return ui_ready_tracks

if __name__ == "__main__":
    pass