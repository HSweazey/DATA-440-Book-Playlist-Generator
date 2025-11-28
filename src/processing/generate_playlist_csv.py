#python3.12 -m src.processing.WIP_generate_playlist_csv 

import math
import ast
import time
import re 
import json 
import pandas as pd
import random # <--- NEW IMPORT

from src.processing.generate_playlist_input import generate_playlist_input
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


from clients.keys.spotify_client_info import CLIENT_ID, CLIENT_SECRET 

# -------------------------------------------------------
# SPOTIFY SETUP
# -------------------------------------------------------
spotify_available = True
try:
    # Ensure all necessary imports are available if keys are found
    from clients.keys.spotify_client_info import CLIENT_ID, CLIENT_SECRET
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials

    try:
        auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        sp.search(q="test", type="track", limit=1)
    except Exception as e:
        print(f"⚠️ Spotify connection failed. Using backup playlist only. Error: {e}")
        spotify_available = False

except ImportError as e:
    print(f"⚠️ Spotify keys not found. Using backup playlist only. Error: {e}")
    spotify_available = False

if not spotify_available:
    from src.processing.csv_backup_generation import generate_backup_playlist


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


def generate_playlist():
    """
    Generate a Spotify playlist based on book parameters from Gemini.
    """

    if not spotify_available:
        # Skip all Gemini / Spotify logic and go straight to backup
        total_pages = int(input("Enter total number of pages (optional, press enter if unknown): ") or 250)
        tracks = generate_backup_playlist(total_pages=total_pages)
        return

    # Step 1: Get Gemini keywords and page info (initial fetch)
    data = generate_playlist_input()

    # Step 2: Compute target and book title
    current_page = 0 
    total_pages = data.get("total_pages", 0)
    num_tracks_target, target_read_time_min = compute_playlist_length(current_page=current_page, total_pages=total_pages)
    book_title = data.get("book", "Untitled Book")

    # --- Step 3 & 4: RETRY LOOP for Gemini Response and Validation ---
    validated_data = None
    gemini_response_str = data.get("response", "{}")
    
    # We allow up to 2 attempts (initial try + 1 retry)
    for attempt in range(1, 3):
        print(f"\n--- Attempt {attempt} to Parse Gemini Response ---")
        
        # 3a. Re-fetch the Gemini output only if this is the retry attempt
        if attempt == 2:
            print("Retrying Gemini call to fetch fresh response...")
            try:
                # The generate_playlist_input() function must be capable of retrying without re-prompting the user.
                data = generate_playlist_input(suppress_input=True) 
                gemini_response_str = data.get("response", "{}")
            except Exception as e:
                print(f"Error during Gemini retry fetch: {e}")
                break

        # 3b. Validate the response string
        validated_data = validate_and_extract_parameters(gemini_response_str)
        
        if validated_data:
            print("Successfully validated Gemini parameters.")
            break
        elif attempt == 1:
            print("Validation failed on first attempt. Retrying...")
            time.sleep(1) # Small pause before retrying
        else:
            print("Validation failed again. Aborting further attempts.")
            break

    if not validated_data:
        print("\nFailed to generate valid Spotify parameters after all retries. Aborting playlist creation.")
        return
    
    # Assign validated data
    mood_keywords_string = validated_data['mood_keywords_string']
    score_query = validated_data['score_query']
    
    # --- Step 5: Budget Calculation ---
    score_budget = min(math.ceil(num_tracks_target * MAX_SCORE_PERCENTAGE), num_tracks_target)
    
    print(f"\n--- Playlist Budget ---")
    print(f"Total Target Tracks: {num_tracks_target}")
    print(f"Score Budget (Max {MAX_SCORE_PERCENTAGE*100:.0f}%): {score_budget}")
    print(f"Mood Budget: {num_tracks_target - score_budget}")
    print("-----------------------\n")
    
    
    # --- Step 6: Sequential Search and Assembly ---
    
    final_tracks = []
    track_fingerprints = set()
    successful_query = ""
    raw_score_tracks_ids = set() 
    
    # 6a. PHASE 1: SCORE SEARCH (HIGH PRIORITY)
    if score_query and score_budget > 0:
        raw_score_tracks, query = fetch_score_tracks(score_query, score_budget)
        
        for track in raw_score_tracks:
            if len(final_tracks) >= score_budget:
                break
                
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                final_tracks.append(track)
                track_fingerprints.add(fingerprint)
                raw_score_tracks_ids.add(track['id']) 
        
        successful_query = query 
        print(f"Score search complete. Added {len(raw_score_tracks_ids)} unique score tracks.")
        
    
    # 6b. PHASE 2: MOOD SEARCH (FILLS REMAINDER)
    tracks_needed_for_mood = num_tracks_target - len(final_tracks)
    
    if tracks_needed_for_mood > 0:
        raw_mood_tracks, query = fetch_mood_tracks(mood_keywords_string, tracks_needed_for_mood)
        
        for track in raw_mood_tracks:
            if len(final_tracks) >= num_tracks_target:
                break
            
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                final_tracks.append(track)
                track_fingerprints.add(fingerprint)
        
        print(f"Mood search complete. Total unique tracks now at {len(final_tracks)}.")
        if not successful_query:
             successful_query = query 
    
    # --- Step 7: Duration Adjustment ---
    final_tracks = adjust_playlist_duration(final_tracks, target_read_time_min, mood_keywords_string)
    
    # --- Step 8: Final Check ---

    if not final_tracks:
        print(f"\nFailed to find any unique tracks after all searches.")
        return


    # Prepare parameters for clean printing
    print("\n--- Final Search Query Summary ---")
    print(f"Fixed Genre Base: {PRIMARY_GENRE_BASE}")
    print(f"Mood Keywords (Gemini Output): {mood_keywords_string}")
    print(f"Final Successful Query: {successful_query}")
    print(f"Total Unique Tracks Found: {len(final_tracks)} (Target: {num_tracks_target})")
    print("----------------------------------\n")

    # Step 9: Print and Export
    print(f"\n🎶 Generated Playlist Summary 🎶")
    print(f"Targeting: {book_title}")
    
    score_tracks_included = len([t for t in final_tracks if t['id'] in raw_score_tracks_ids])
    mood_tracks_included = len(final_tracks) - score_tracks_included
    
    print(f"Score Tracks Included: {score_tracks_included} (Budget: {score_budget})")
    print(f"Mood Tracks Included: {mood_tracks_included} (Budget: {num_tracks_target - score_budget})")
    total_duration_ms = sum(track['duration_ms'] for track in final_tracks)
    total_duration_min = total_duration_ms / 60000
    print(f"Total Duration: {total_duration_min:.1f} minutes\n")
    
    for i, track in enumerate(final_tracks, start=1):
        duration_ms = track['duration_ms']
        minutes, seconds = divmod(duration_ms // 1000, 60)
        formatted_duration = f"{minutes}:{seconds:02d}"

        artists = ", ".join([a['name'] for a in track['artists']])
        print(f"{i}. {track['name']} – {artists}")
        print(f"   Duration: {formatted_duration}")
        print(f"   Spotify URL: {track['external_urls']['spotify']}\n")

    # --- EXPORT PROMPT ---
    export_choice = input("Export playlist? (c = CSV, j = JSON, n = No): ").lower().strip()
    
    if not export_choice:
        export_choice = 'n'
        
    if export_choice == 'c':
        export_playlist(final_tracks, 'csv', book_title)
    elif export_choice == 'j':
        export_playlist(final_tracks, 'json', book_title)
    elif export_choice == 'n':
        print("\nExport skipped.")
    else:
        print(f"\nInvalid choice ('{export_choice}'). Export skipped.")


if __name__ == "__main__":
    generate_playlist()