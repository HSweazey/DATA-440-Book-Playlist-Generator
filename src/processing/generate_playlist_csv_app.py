import math
import ast
import time
import pandas as pd
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
    from clients.keys.spotify_client_info import CLIENT_ID, CLIENT_SECRET
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
MAX_SCORE_PERCENTAGE = 0.15 
DURATION_THRESHOLD_MS = 5 * 60 * 1000 

# --- HELPER FUNCTIONS ---
def create_track_fingerprint(track: dict) -> str:
    title = track.get('name', 'Unknown').lower()
    # Handle simplified track objects (from album_tracks) vs full track objects
    if 'artists' in track:
        artist_name = track['artists'][0]['name'].lower()
    else:
        artist_name = track.get('artist_name', 'Unknown').lower()
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

    # Safety Check
    SAFETY_TRIGGER_KEYWORDS = ['romantic', 'romance', 'sexy', 'erotic', 'intimate', 'passion', 'love', 'passionate']
    safety_override = False 
    all_keywords_string = " ".join([str(k).lower().strip() for k in mood_keywords])
    if any(trigger in all_keywords_string for trigger in SAFETY_TRIGGER_KEYWORDS):
        safety_override = True

    score_query = params.get('score_query', '')
    composer_name = params.get('composer_name', '')
    
    # Terminal Debug
    if score_query:
        print(f"DEBUG: Extracted Score: '{score_query}' | Composer: '{composer_name}'")
    
    return {
        'mood_keywords_string': all_keywords_string, 
        'score_query': str(score_query).strip(),
        'composer_name': str(composer_name).strip(),
        'safety_override': safety_override 
    }

def _build_query(primary_keywords: str, query_type: str, composer_name: str = '') -> str:
    if query_type == "score":
        # For Album/Score search, less is often more.
        if composer_name:
            return f'{primary_keywords} {composer_name}'.strip()
        return primary_keywords.strip()
        
    elif query_type == "ambient_split":
        return f"ambient {primary_keywords} instrumental".strip()
    elif query_type == "instrumental_split":
        return f"instrumental {primary_keywords}".strip()
    elif query_type == "mood_fallback":
        return FALLBACK_GENRE
    return f"instrumental {primary_keywords}".strip()

@st.cache_data(show_spinner="Searching Spotify...", persist=True, hash_funcs={spotipy.Spotify: lambda _: None})
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
        try:
            results = sp.search(q=query, type="track", limit=limit, offset=offset)
            tracks_batch = results.get('tracks', {}).get('items', [])
            if not tracks_batch: break 

            all_tracks.extend(tracks_batch)
            
            tracks_to_fetch -= len(tracks_batch) 
            offset += len(tracks_batch)
            if tracks_to_fetch > 0: time.sleep(WAIT_TIME_SECONDS)
        except Exception as e:
            if 'sp' in globals() and sp: pass 
            return [], str(e)
    return all_tracks, None

def _store_spotify_debug(count: int, query: str, attempt_type: str):
    if 'debug_info' not in st.session_state: st.session_state['debug_info'] = {}
    if 'search_log' not in st.session_state['debug_info']: st.session_state['debug_info']['search_log'] = []
    st.session_state['debug_info']['search_log'].append({ "Source": attempt_type, "Query": query, "Tracks Added": count })
    print(f"DEBUG LOG: {attempt_type} | Query: '{query}' | Tracks: {count}")

def fetch_mood_tracks(mood_keywords_string: str, tracks_needed: int, existing_tracks: list):
    all_found_tracks = []
    existing_fingerprints = set(create_track_fingerprint(t) for t in existing_tracks)
    raw_list = mood_keywords_string.replace(',', ' ').split()
    mood_list = [k.strip() for k in raw_list if k.strip()]
    if not mood_list: return [], ""

    limit_per_search = math.ceil(tracks_needed / (len(mood_list) * 2))
    limit_per_search = max(limit_per_search, 2) 

    for keyword in mood_list:
        if tracks_needed <= 0: break
        # 1. Ambient
        query_a = _build_query(keyword, "ambient_split")
        tracks_a, _ = _run_batched_search(query_a, limit_per_search * 2, randomize_start=False)
        added_a = 0
        if tracks_a:
            for track in tracks_a:
                fp = create_track_fingerprint(track)
                if fp not in existing_fingerprints:
                    all_found_tracks.append(track)
                    existing_fingerprints.add(fp)
                    tracks_needed -= 1
                    added_a += 1
                    if tracks_needed <= 0 or added_a >= limit_per_search: break
            if added_a > 0:
                _store_spotify_debug(added_a, query_a, f"Ambient: {keyword}")

        if tracks_needed <= 0: break
        # 2. Instrumental
        query_b = _build_query(keyword, "instrumental_split")
        tracks_b, _ = _run_batched_search(query_b, limit_per_search * 2, randomize_start=False)
        added_b = 0
        if tracks_b:
            for track in tracks_b:
                fp = create_track_fingerprint(track)
                if fp not in existing_fingerprints:
                    all_found_tracks.append(track)
                    existing_fingerprints.add(fp)
                    tracks_needed -= 1
                    added_b += 1
                    if tracks_needed <= 0 or added_b >= limit_per_search: break
            if added_b > 0:
                _store_spotify_debug(added_b, query_b, f"Instrumental: {keyword}")

    if tracks_needed > 0:
        ambient_query = "ambient instrumental"
        limit = int(tracks_needed * 2) 
        amb_tracks, error = _run_batched_search(ambient_query, limit, randomize_start=True)
        added_amb = 0
        if amb_tracks:
            for track in amb_tracks:
                fp = create_track_fingerprint(track)
                if fp not in existing_fingerprints:
                    all_found_tracks.append(track)
                    existing_fingerprints.add(fp)
                    tracks_needed -= 1
                    added_amb += 1
                    if tracks_needed <= 0: break
            if added_amb > 0:
                _store_spotify_debug(added_amb, ambient_query, "Final Ambient Fill")
    return all_found_tracks, "Double Dip Completed"

def fetch_score_tracks(score_query: str, num_tracks: int, composer_name: str = ''):
    """
    ALBUM-FIRST STRATEGY:
    1. Check if an Album exists for this score/composer.
    2. If YES: Pull tracks from that Album.
    3. If NO: Return empty (so we default to Mood Search).
    """
    # Build a search query optimized for ALBUMS
    search_terms = _build_query(score_query, "score", composer_name)
    print(f"DEBUG: Checking for Album with query: '{search_terms}'")

    try:
        # 1. THE CHECK: Search for an Album
        album_results = sp.search(q=search_terms, type='album', limit=1)
        
        if album_results and album_results['albums']['items']:
            # ALBUM FOUND!
            best_album = album_results['albums']['items'][0]
            album_id = best_album['id']
            album_name = best_album['name']
            print(f"DEBUG: ✅ Score Found! Using Album: {album_name} ({album_id})")
            
            # 2. PULL FROM SCORE
            # Get tracks directly from this album
            # limit=50 ensures we get most tracks from a standard score
            album_tracks_resp = sp.album_tracks(album_id, limit=50)
            raw_tracks = album_tracks_resp.get('items', [])
            
            # Filter/Limit to the budget
            valid_tracks = []
            for track in raw_tracks:
                # SKIP TRACKS WITH "feat." IN TITLE
                t_name = track.get('name', '').lower()
                if "feat." in t_name or "(feat" in t_name:
                    continue

                valid_tracks.append(track)
                if len(valid_tracks) >= num_tracks: break
            
            if valid_tracks:
                _store_spotify_debug(len(valid_tracks), f"Album: {album_name}", "Score (Album Match)")
                return valid_tracks, f"Album: {album_name}"
        
        else:
            # NO ALBUM FOUND
            print(f"DEBUG: ❌ No Album found for '{search_terms}'. Skipping score search.")
            # Return empty list -> logic will go right to Mood Search
            return [], search_terms

    except Exception as e:
        print(f"DEBUG: Score search error: {e}")
        return [], search_terms
    
    return [], search_terms

def adjust_playlist_duration(tracks: list, target_time_min: float, mood_keywords_string: str) -> list:
    safe_tracks = [t for t in tracks if 'duration_ms' in t]
    if len(safe_tracks) < len(tracks): return tracks 
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
        query = "ambient instrumental"
        raw_new_tracks, _ = _run_batched_search(query, num_to_add * 2, randomize_start=True) 
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

def get_final_tracks(book_title: str, author_name: str, total_pages: int):
    # 1. SPOTIFY CHECK
    if not spotify_available:
        return {"status": "FAIL_NEED_GENRE", "reason": "Spotify API Keys Missing or Invalid"}

    if 'debug_info' not in st.session_state: st.session_state['debug_info'] = {}
    st.session_state['debug_info']['search_log'] = [] 

    # 2. GEMINI CALL
    try:
        data = generate_playlist_input(
            book=book_title, 
            author=author_name, 
            total_pages=total_pages,
            suppress_input=True
        )
    except Exception as e:
        return {"status": "FAIL_NEED_GENRE", "reason": f"Gemini connection failed: {e}"}

    current_page = 0 
    total_pages_used = data.get("total_pages", 0) 
    num_tracks_target, target_read_time_min = compute_playlist_length(current_page=current_page, total_pages=total_pages_used)
    
    st.session_state['debug_info']['target_metrics'] = {
        'target_read_time_min': f"{target_read_time_min:.1f}",
        'num_tracks_target': num_tracks_target,
    }

    validated_data = None
    gemini_response_str = data.get("response", "{}")
    
    # 3. GEMINI PARSING
    for attempt in range(1, 3):
        if attempt == 2:
            try:
                data = generate_playlist_input(book=book_title, author=author_name, total_pages=total_pages, suppress_input=True) 
                gemini_response_str = data.get("response", "{}")
            except Exception: break
        validated_data = validate_and_extract_parameters(gemini_response_str)
        if validated_data: break
        elif attempt == 1: time.sleep(1) 

    if not validated_data: 
        return {"status": "FAIL_NEED_GENRE", "reason": "AI could not determine mood"}
    
    if validated_data['safety_override']:
        st.error("🚨 Safety Override Triggered! Keywords suggested sensitive themes. Using Instrumental Backup.")
        return generate_backup_playlist(total_pages=total_pages, genre_code='o')

    mood_keywords_string = validated_data['mood_keywords_string']
    score_query = validated_data['score_query']
    composer_name = validated_data['composer_name']

    # 4. SPOTIFY SEARCH
    score_budget = min(math.ceil(num_tracks_target * MAX_SCORE_PERCENTAGE), num_tracks_target)
    final_tracks = []
    track_fingerprints = set()

    if score_query and score_budget > 0:
        # Runs the Album-First check strategy
        raw_score_tracks, query = fetch_score_tracks(score_query, score_budget, composer_name) 
        for track in raw_score_tracks:
            if len(final_tracks) >= score_budget: break
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                final_tracks.append(track)
                track_fingerprints.add(fingerprint)

    # 5. MOOD SEARCH (Fills the rest)
    # If Score Search returned 0 tracks, this budget automatically expands to cover the full target.
    tracks_needed_for_mood = num_tracks_target - len(final_tracks)
    
    if tracks_needed_for_mood > 0:
        raw_mood_tracks, query = fetch_mood_tracks(mood_keywords_string, tracks_needed_for_mood, final_tracks)
        for track in raw_mood_tracks:
            if len(final_tracks) >= num_tracks_target: break
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                final_tracks.append(track)
                track_fingerprints.add(fingerprint)

    st.session_state['debug_info']['pre_adjustment_length'] = len(final_tracks)

    final_tracks = adjust_playlist_duration(final_tracks, target_read_time_min, mood_keywords_string)
    
    st.session_state['debug_info']['post_adjustment_length'] = len(final_tracks)

    if not final_tracks: 
         return {"status": "FAIL_NEED_GENRE", "reason": "No matching tracks found on Spotify"}

    ui_ready_tracks = []
    for track in final_tracks:
        if 'external_urls' in track and 'spotify' in track['external_urls']:
            url = track['external_urls']['spotify']
        elif 'spotify_url' in track:
            url = track['spotify_url']
        else:
            url = None
        if url:
            t_name = track.get('name', track.get('track_name', 'Unknown Title'))
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