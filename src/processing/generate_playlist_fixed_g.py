#python3.12 -m src.processing.generate_playlist_fixed_g 

import math
import ast
import time
import re 

from src.processing.generate_playlist_input_v5 import generate_playlist_input
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from src.utils.KEYS import CLIENT_ID, CLIENT_SECRET  # <- ensure utils has __init__.py

# -------------------------------------------------------
# SPOTIFY SETUP
# -------------------------------------------------------
auth_manager = SpotifyClientCredentials(client_id = CLIENT_ID, client_secret = CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Average song length in minutes
AVG_SONG_LENGTH_MIN = 5
AVG_PAGE_SPEED_MIN = 2

# Constants for Batching and Validation
BATCH_SIZE = 20
WAIT_TIME_SECONDS = 0.5
MAX_SEARCH_LIMIT = 50 
PRIMARY_GENRE_BASE = 'ambient' # Fixed instrumental base
FALLBACK_GENRE = 'classical' # Guaranteed safe fallback (Used if ambient search fails)
MAX_SCORE_PERCENTAGE = 0.25 # Max percentage of the playlist that can be score tracks

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


def compute_playlist_length(current_page: int = 0, total_pages: int = 100) -> int:
    """
    Compute number of songs based on pages left and average song length.
    """
    if total_pages == 0:
        return 20 

    pages_left = max(0, total_pages - current_page)
    readtime = pages_left * AVG_PAGE_SPEED_MIN

    num_tracks = max(1, math.ceil(readtime / AVG_SONG_LENGTH_MIN))
    print(f"Calculated reading time: {readtime} minutes. Target tracks: {num_tracks}")
    return num_tracks

def validate_and_extract_parameters(gemini_response_str: str) -> dict | None:
    """
    Safely parses the Gemini dictionary string and extracts required parameters.
    """
    try:
        # Safely evaluate the string as a Python literal (a dictionary or list)
        params = ast.literal_eval(gemini_response_str)
        
        # --- FIX: Robustly handle list wrapper (e.g., if output is [{'k': 'v'}]) ---
        if isinstance(params, list):
            if not params:
                print("Error: Gemini response is an empty list.")
                return None
            params = params[0] # Extract the dictionary from the list
        # -------------------------------------------------------------------------

        if not isinstance(params, dict):
            print(f"Error: Gemini response could not be extracted as a dictionary. Received type: {type(params)}")
            return None
        
        # Check for required mood keywords
        mood_keywords = params.get('mood_keywords')
        if not isinstance(mood_keywords, list) or len(mood_keywords) < 3:
            print("Error: Missing or invalid 'mood_keywords' list (needs 3).")
            return None
            
    except Exception as e:
        print(f"Error: Failed to parse Gemini response string: {e}")
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
    
    # Aggressive Anti-Vocal Keywords (used in every search)
    ANTI_VOCAL_KEYWORDS = "instrumental no vocals score"
    
    if query_type == "full":
        # Mood Search Attempt 1: Full Query (Fixed Genre Base + All Mood Keywords)
        genre = PRIMARY_GENRE_BASE
        keywords = f"{genre} {primary_keywords}"
    elif query_type == "mood_only":
        # Mood Search Attempt 2: Mood keywords only (intermediate step)
        keywords = primary_keywords
    elif query_type == "mood_fallback":
        # Mood Search Attempt 3: Guaranteed Fallback genre
        keywords = FALLBACK_GENRE
    elif query_type == "score":
        # Score Search: Search for the specific score name
        keywords = primary_keywords
    else:
        keywords = "" # Should not happen
    
    # Combine anti-vocal keywords with the specific search terms
    return f"{ANTI_VOCAL_KEYWORDS} {keywords}".strip()


def _run_batched_search(query: str, num_tracks: int):
    """
    Internal helper to execute the batched search for a given query.
    Returns (tracks, error)
    """
    all_tracks = []
    tracks_to_fetch = num_tracks
    offset = 0
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
                break # No more tracks found in this batch

            all_tracks.extend(tracks_batch)
            tracks_to_fetch -= len(tracks_batch)
            offset += len(tracks_batch)

            if tracks_to_fetch > 0:
                time.sleep(WAIT_TIME_SECONDS)
                
        except Exception as e:
            # API error (400, 404, etc.) occurred.
            return [], str(e)

    return all_tracks, None # Success

def fetch_mood_tracks(mood_keywords_string: str, num_tracks: int):
    """
    Fetches the requested number of tracks using a 3-step cascading search strategy.
    """
    
    attempts = [
        ("full", "Most Specific (Fixed Base + Moods)"), 
        ("mood_only", "Intermediate (Mood Only)"),
        ("mood_fallback", "Safe Fallback (Ambient Only)")
    ]
    
    for i, (query_type, attempt_name) in enumerate(attempts):
        
        current_query = _build_query(mood_keywords_string, query_type)
        
        print(f"\n--- Mood Search Attempt {i+1}: {attempt_name} ---")
        print(f"Using Query: {current_query}")
        
        # We fetch tracks needed for the mood budget, fetching 50% extra to account for duplicates
        search_limit = int(num_tracks * 1.5)
        
        tracks, error = _run_batched_search(current_query, search_limit)
        
        if tracks:
            print(f"Successfully found {len(tracks)} raw mood tracks.")
            return tracks, current_query

        if error:
            print(f"API Error detected: {error}. Moving to next attempt.")
        else:
            print("Zero tracks found for this query. Moving to next attempt.")

    return [], current_query # Returns empty list if all attempts fail


def fetch_score_tracks(score_query: str, num_tracks: int):
    """
    Fetches tracks from a specific movie score.
    """
    # The score query is the primary keywords for this search type
    current_query = _build_query(score_query, "score") 
    print(f"\n--- Score Search: Dedicated Score Query ---")
    print(f"Using Query: {current_query}")
    
    # Fetch 50% more tracks than budget to allow for duplicate removal
    search_limit = int(num_tracks * 1.5)
    
    tracks, error = _run_batched_search(current_query, search_limit)
    
    if error:
        print(f"API Error detected during score search: {error}")
        return [], current_query
    
    print(f"Found {len(tracks)} raw score tracks.")
    return tracks, current_query

def generate_playlist():
    """
    Generate a Spotify playlist based on book parameters from Gemini.
    """

    # Step 1: Get Gemini keywords and page info
    data = generate_playlist_input()

    current_page = 0 
    total_pages = data.get("total_pages", 0)

    # Step 2: Compute total track target
    num_tracks_target = int(compute_playlist_length(current_page=current_page, total_pages=total_pages))

    # Step 3: Parse and Validate Gemini parameters
    gemini_response_str = data.get("response", "{}")
    validated_data = validate_and_extract_parameters(gemini_response_str)

    if not validated_data:
        print("Failed to generate valid Spotify parameters. Aborting playlist creation.")
        return
    
    mood_keywords_string = validated_data['mood_keywords_string']
    score_query = validated_data['score_query']
    
    # --- Step 4: Budget Calculation ---
    score_budget = min(math.ceil(num_tracks_target * MAX_SCORE_PERCENTAGE), num_tracks_target)
    mood_budget = num_tracks_target - score_budget
    
    print(f"\n--- Playlist Budget ---")
    print(f"Total Target Tracks: {num_tracks_target}")
    print(f"Score Budget (Max {MAX_SCORE_PERCENTAGE*100:.0f}%): {score_budget}")
    print(f"Mood Budget: {mood_budget}")
    print("-----------------------\n")
    
    
    # --- Step 5: Sequential Search and Assembly ---
    
    final_tracks = []
    track_fingerprints = set()
    successful_query = ""
    raw_score_tracks = [] # Tracks fetched in Phase 1
    
    # 5a. PHASE 1: SCORE SEARCH (HIGH PRIORITY)
    if score_query and score_budget > 0:
        raw_score_tracks, query = fetch_score_tracks(score_query, score_budget)
        
        for track in raw_score_tracks:
            # Stop once the score budget is reached
            if len(final_tracks) >= score_budget:
                break
                
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                final_tracks.append(track)
                track_fingerprints.add(fingerprint)
        
        print(f"Score search complete. Added {len(final_tracks)} unique score tracks.")
        successful_query = query # Save the score query
        
    
    # 5b. PHASE 2: MOOD SEARCH (FILLS REMAINDER)
    tracks_needed_for_mood = num_tracks_target - len(final_tracks)
    
    if tracks_needed_for_mood > 0:
        raw_mood_tracks, query = fetch_mood_tracks(mood_keywords_string, tracks_needed_for_mood)
        
        # Use the raw mood tracks list only to track which tracks came from the mood search
        # We need to iterate over the fetched tracks to check for duplicates against the set
        
        for track in raw_mood_tracks:
            # Stop once the total target is reached
            if len(final_tracks) >= num_tracks_target:
                break
            
            fingerprint = create_track_fingerprint(track)
            if fingerprint not in track_fingerprints:
                final_tracks.append(track)
                track_fingerprints.add(fingerprint)
        
        print(f"Mood search complete. Total unique tracks now at {len(final_tracks)}.")
        if not successful_query:
             successful_query = query # Save the mood query if score search was skipped
    
    # --- Step 6: Final Check ---

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

    # Step 7: Calculate total duration
    total_duration_ms = sum(track['duration_ms'] for track in final_tracks)
    total_duration_min = total_duration_ms / 60000

    # Step 8: Print track info interactively
    print(f"\n🎶 Generated Playlist Summary 🎶")
    print(f"Targeting: {data.get('book')}")
    # Calculate tracks included from each phase for summary
    score_tracks_included = len([t for t in final_tracks if t in raw_score_tracks])
    mood_tracks_included = len(final_tracks) - score_tracks_included
    
    print(f"Score Tracks Included: {score_tracks_included} (Budget: {score_budget})")
    print(f"Mood Tracks Included: {mood_tracks_included} (Budget: {mood_budget})")
    print(f"Total Duration: {total_duration_min:.1f} minutes\n")
    
    for i, track in enumerate(final_tracks, start=1):
        duration_ms = track['duration_ms']
        minutes, seconds = divmod(duration_ms // 1000, 60)
        formatted_duration = f"{minutes}:{seconds:02d}"

        artists = ", ".join([a['name'] for a in track['artists']])
        print(f"{i}. {track['name']} – {artists}")
        print(f"   Duration: {formatted_duration}")
        print(f"   Spotify URL: {track['external_urls']['spotify']}\n")


if __name__ == "__main__":
    generate_playlist()