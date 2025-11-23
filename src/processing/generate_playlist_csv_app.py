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

    # --- KEYWORD SANITIZATION (CLASSROOM SAFE MODE) ---
    unsafe_map = {
        'romance': 'love', 'romantic': 'love',
        'sexy': 'warm', 'sensual': 'tender',
        'seductive': 'mysterious', 'passionate': 'emotional',
        'steamy': 'intense', 'erotic': 'dark', 'intimate': 'close'
    }
    
    sanitized_keywords = []
    for k in mood_keywords:
        word = str(k).lower().strip()
        replaced = False
        for unsafe, safe in unsafe_map.items():
            if unsafe in word:
                clean_word = word.replace(unsafe, safe)
                sanitized_keywords.append(clean_word)
                replaced = True
                break
        if not replaced:
            sanitized_keywords.append(word)

    mood_keywords_string = " ".join(sanitized_keywords)
    score_query = params.get('score_query', '')
    
    return {'mood_keywords_string': mood_keywords_string, 'score_query': str(score_query).strip()}

def _build_query(primary_keywords: str, query_type: str) -> str:
    ANTI_VOCAL_KEYWORDS = "instrumental"
    if query_type == "full":
        genre = PRIMARY_GENRE_BASE
        keywords = f"{genre} {primary_keywords}"
    elif query_type == "mood_only":
        keywords = f"{PRIMARY_GENRE_BASE} {primary_keywords}"
    elif query_type == "mood_fallback":
        keywords = FALLBACK_GENRE
    elif query_type == "score":
        keywords = primary_keywords
    else:
        keywords = "" 
    return f"{ANTI_VOCAL_KEYWORDS} {keywords}".strip()

# --- CACHED SEARCH FUNCTION ---
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

            # --- STAGE 2: STRICT CONTENT FILTERING ---
            clean_batch = []
            for track in tracks_batch:
                if track.get('explicit', False): continue 
                
                title = track['name'].lower()
                album = track['album']['name'].lower()
                risky_words = ['sex', 'explicit', 'uncensored', 'clean version', 'dirty', 'fuck', 'shit', 'bitch', 'sensual']
                if any(bad in title for bad in risky_words) or any(bad in album for bad in risky_words):
                    continue
                clean_batch.append(track)

            all_tracks.extend(clean_batch)
            tracks_to_fetch -= len(clean_batch) 
            offset += len(tracks_batch)

            if tracks_to_fetch > 0:
                time.sleep(WAIT_TIME_SECONDS)
                
        except Exception as e:
            if 'sp' in globals() and sp: pass 
            return [], str(e)

    return all_tracks, None

# --- NEW DEBUG STORAGE FUNCTION ---
def _store_spotify_debug(count: int, query: str, attempt_type: str):
    """
    Appends a new search event to the session state log.
    """
    if 'debug_info' not in st.session_state:
        st.session_state['debug_info'] = {}
        
    if 'search_log' not in st.session_state['debug_info']:
        st.session_state['debug_info']['search_log'] = []
        
    st.session_state['debug_info']['search_log'].append({
        "Source": attempt_type,
        "Query": query,
        "Tracks Added": count
    })

# -----------------------------------------------------------------------------------
# 🔥 IMPROVED MOOD SEARCH (DOUBLE DIP STRATEGY) 🔥
# -----------------------------------------------------------------------------------
def fetch_mood_tracks(mood_keywords_string: str, tracks_needed: int, existing_tracks: list):
    all_found_tracks = []
    existing_fingerprints = set(create_track_fingerprint(t) for t in existing_tracks)
    
    raw_list = mood_keywords_string.replace(',', ' ').split()
    mood_list = [k.strip() for k in raw_list if k.strip()]
    
    if not mood_list: return [], ""

    # --- PASS 1: BALANCED FAIRNESS ---
    limit_per_keyword = math.ceil(tracks_needed / len(mood_list))
    limit_per_keyword = max(limit_per_keyword, 3) 
    
    current_query = ""

    for keyword in mood_list:
        if tracks_needed <= 0: break
        
        current_query = _build_query(keyword, "mood_only")
        fetch_limit = limit_per_keyword * 2 
        
        tracks, error = _run_batched_search(current_query, fetch_limit, randomize_start=False)
        tracks_added_this_key = 0
        
        if tracks:
            for track in tracks:
                fp = create_track_fingerprint(track)
                if fp not in existing_fingerprints:
                    all_found_tracks.append(track)
                    existing_fingerprints.add(fp)
                    tracks_needed -= 1
                    tracks_added_this_key += 1
                    if tracks_needed <= 0: break
                    if tracks_added_this_key >= limit_per_keyword: break
            
            # LOGGING
            if tracks_added_this_key > 0:
                _store_spotify_debug(tracks_added_this_key, current_query, f"Balanced: {keyword}")

    # --- PASS 2: GREEDY CLEANUP ---
    if tracks_needed > 0:
        random.shuffle(mood_list)
        for keyword in mood_list:
            if tracks_needed <= 0: break
            
            current_query = _build_query(keyword, "mood_only")
            fetch_limit = tracks_needed * 2 
            
            tracks, error = _run_batched_search(current_query, fetch_limit, randomize_start=True) 
            tracks_added_this_key = 0
            
            if tracks:
                for track in tracks:
                    fp = create_track_fingerprint(track)
                    if fp not in existing_fingerprints:
                        all_found_tracks.append(track)
                        existing_fingerprints.add(fp)
                        tracks_needed -= 1
                        tracks_added_this_key += 1
                        if tracks_needed <= 0: break
                
                if tracks_added_this_key > 0:
                    _store_spotify_debug(tracks_added_this_key, current_query, f"Greedy Fill: {keyword}")

    # --- PASS 3: PURE AMBIENT ---
    if tracks_needed > 0:
        ambient_query = _build_query("", "mood_only") 
        limit = int(tracks_needed * 2) 
        amb_tracks, error = _run_batched_search(ambient_query, limit, randomize_start=True)
        tracks_added_this_key = 0
        
        if amb_tracks:
            for track in amb_tracks:
                fp = create_track_fingerprint(track)
                if fp not in existing_fingerprints:
                    all_found_tracks.append(track)
                    existing_fingerprints.add(fp)
                    tracks_needed -= 1
                    tracks_added_this_key += 1
                    if tracks_needed <= 0: break
            
            if tracks_added_this_key > 0:
                _store_spotify_debug(tracks_added_this_key, ambient_query, "Pure Ambient Fill")

    return all_found_tracks, current_query

def fetch_score_tracks(score_query: str, num_tracks: int):
    """
    Strict Strategy:
    1. Caps the result at MAX 4 tracks to prevent deep-diving into vocal/filler songs.
    2. Prioritizes tracks with "Theme", "Suite", or "Overture" in the title.
    3. Strictly avoids explicit content.
    """
    
    # 1. HARD CAP: Never return more than 4 score tracks, regardless of budget.
    # This keeps us in the "Main Theme" territory and out of "End Credits Pop Song" territory.
    SAFE_MAX_SCORE = 6
    num_to_fetch = min(num_tracks, SAFE_MAX_SCORE)
    
    search_terms = f"{score_query} soundtrack instrumental"
    print(f"🎬 Score Search (Capped at {num_to_fetch}): '{search_terms}'")

    try:
        # Fetch a batch to filter from
        limit = 20 
        results = sp.search(q=search_terms, type="track", limit=limit)
        raw_tracks = results.get('tracks', {}).get('items', [])
        
        filtered_tracks = []
        priority_tracks = [] # For tracks that explicitly look instrumental
        
        for track in raw_tracks:
            t_name = track['name'].lower()
            
            # A. SAFETY: Explicit Check
            if track.get('explicit', False): continue

            # B. SAFETY: Keyword Exclusion
            bad_keywords = ['remix', 'radio edit', 'club mix', 'interview', 'live', 'commentary', 'vocal', 'performed by']
            if any(bad in t_name for bad in bad_keywords): continue
            
            # C. QUALITY: Identify "Gold Standard" Instrumental Tracks
            good_keywords = ['theme', 'suite', 'overture', 'main title', 'opening', 'ending', 'credits', 'instrumental']
            
            if any(good in t_name for good in good_keywords):
                priority_tracks.append(track)
            else:
                filtered_tracks.append(track)

            # Optimization: Stop if we have enough "Gold" tracks
            if len(priority_tracks) >= num_to_fetch:
                break
        
        # Combine: Priority tracks first, then fillers
        final_selection = (priority_tracks + filtered_tracks)[:num_to_fetch]
        
        # LOGGING
        if final_selection:
            _store_spotify_debug(len(final_selection), search_terms, "Score Search (Strict Cap)")
            
        return final_selection, search_terms

    except Exception as e:
        print(f"  ❌ Score search failed: {e}")
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
        
        raw_list = mood_keywords_string.replace(',', ' ').split()
        keywords = [k.strip() for k in raw_list if k.strip()]
        
        if keywords:
            filler_keyword = random.choice(keywords)
            query = _build_query(filler_keyword, "mood_only")
            source_label = f"Duration Fill: {filler_keyword}"
        else:
            query = _build_query(FALLBACK_GENRE, "fallback")
            source_label = "Duration Fill: Generic"

        raw_new_tracks, _ = _run_batched_search(query, num_to_add * 2, randomize_start=True) 
        
        track_fingerprints = set(create_track_fingerprint(t) for t in safe_tracks)
        tracks_added = 0
        
        for track in raw_new_tracks:
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                safe_tracks.append(track)
                track_fingerprints.add(fingerprint)
                actual_time_ms += track['duration_ms']
                tracks_added += 1
                diff_min = (actual_time_ms - target_time_ms) / 60000
                if abs(diff_min) <= 5: break
        
        # LOGGING
        if tracks_added > 0:
            _store_spotify_debug(tracks_added, query, source_label)
                
    return safe_tracks

def get_final_tracks(book_title: str, author_name: str, total_pages: int):
    if not spotify_available:
        return generate_backup_playlist(total_pages=total_pages, genre_code='o')

    # INITIALIZE DEBUG LOG (Clear old data)
    if 'debug_info' not in st.session_state: st.session_state['debug_info'] = {}
    st.session_state['debug_info']['search_log'] = [] # <--- NEW: Reset log for fresh run

    try:
        data = generate_playlist_input(
            book=book_title, 
            author=author_name, 
            total_pages=total_pages,
            suppress_input=True
        )
    except Exception as e:
        return []

    current_page = 0 
    total_pages_used = data.get("total_pages", 0) 
    num_tracks_target, target_read_time_min = compute_playlist_length(current_page=current_page, total_pages=total_pages_used)
    
    st.session_state['debug_info']['target_metrics'] = {
        'target_read_time_min': f"{target_read_time_min:.1f}",
        'num_tracks_target': num_tracks_target,
    }

    validated_data = None
    gemini_response_str = data.get("response", "{}")
    
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
        st.session_state['debug_info']['gemini_status'] = "Failed validation, prompting user genre selection."
        return {"status": "GEMINI_FAILED_NEED_GENRE"}
    
    mood_keywords_string = validated_data['mood_keywords_string']
    score_query = validated_data['score_query']
    
    score_budget = min(math.ceil(num_tracks_target * MAX_SCORE_PERCENTAGE), num_tracks_target)
    final_tracks = []
    track_fingerprints = set()

    # PHASE 1 (SCORE)
    if score_query and score_budget > 0:
        raw_score_tracks, query = fetch_score_tracks(score_query, score_budget)
        for track in raw_score_tracks:
            if len(final_tracks) >= score_budget: break
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                final_tracks.append(track)
                track_fingerprints.add(fingerprint)

    # PHASE 2 (MOOD)
    tracks_needed_for_mood = num_tracks_target - len(final_tracks)
    if tracks_needed_for_mood > 0:
        raw_mood_tracks, query = fetch_mood_tracks(
            mood_keywords_string,       
            tracks_needed_for_mood,     
            final_tracks                
        )
        for track in raw_mood_tracks:
            if len(final_tracks) >= num_tracks_target: break
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                final_tracks.append(track)
                track_fingerprints.add(fingerprint)

    st.session_state['debug_info']['pre_adjustment_length'] = len(final_tracks)

    # DURATION ADJUSTMENT
    final_tracks = adjust_playlist_duration(final_tracks, target_read_time_min, mood_keywords_string)
    
    st.session_state['debug_info']['post_adjustment_length'] = len(final_tracks)

    if not final_tracks: 
         return generate_backup_playlist(total_pages=total_pages, genre_code='o')

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