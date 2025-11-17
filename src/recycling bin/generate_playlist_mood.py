import math
import ast
import time
from generate_playlist_input_genre_mood import generate_playlist_input
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from KEYS import CLIENT_ID, CLIENT_SECRET

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
FALLBACK_GENRE = 'ambient' # Guaranteed safe instrumental fallback

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

def validate_and_extract_keywords(gemini_response_str: str): #-> dict | None: (weird error on Ella's computer)
    """
    Safely parses the Gemini keyword list string and extracts the primary genre and mood keywords.
    """
    try:
        # Safely evaluate the string as a Python literal (a list)
        keywords_list = ast.literal_eval(gemini_response_str)
        
        if not isinstance(keywords_list, list) or len(keywords_list) < 3:
            print(f"Error: Gemini response is not a list of 3 keywords. Received: {keywords_list}")
            return None
            
    except Exception as e:
        print(f"Error: Failed to parse Gemini response string: {e}")
        return None

    # Strip whitespace and ensure all are lowercase strings
    keywords_list = [str(k).lower().strip() for k in keywords_list]
    
    # --- Extraction (Assume first word is the primary genre, remaining are mood) ---
    primary_genre = keywords_list[0]
    mood_keywords = keywords_list[1:3] 
    
    if not primary_genre or not mood_keywords:
        print("Error: Could not extract necessary keywords from the list.")
        return None

    return {
        'primary_genre': primary_genre,
        'mood_keywords_string': " ".join(mood_keywords),
        'all_keywords': keywords_list
    }

def _build_query(genre: str, mood_keywords_string: str, query_type: str) -> str:
    """
    Constructs the Spotify search query string based on the genre and optional mood keywords.
    """
    if query_type == "full":
        # Attempt 1: All keywords (most specific)
        keywords = f"{genre} {mood_keywords_string}"
    elif query_type == "mood_only":
        # Attempt 2: Mood keywords only (intermediate step)
        keywords = mood_keywords_string
    elif query_type == "fallback":
        # Attempt 3: Guaranteed fallback genre
        keywords = FALLBACK_GENRE
    else:
        keywords = "" # Should not happen
    
    # Return instrumental + space-separated keywords
    return f"instrumental {keywords}".strip()


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

def fetch_search_tracks(genre: str, mood_keywords_string: str, num_tracks: int):
    """
    Fetches the requested number of tracks using a 3-step cascading search strategy.
    """
    
    # Define the three cascading attempts
    attempts = [
        # Attempt 1: Most Specific (All Keywords)
        (genre, mood_keywords_string, "full", "Most Specific (All Keywords)"), 
        
        # Attempt 2: Intermediate (Mood Keywords Only)
        (genre, mood_keywords_string, "mood_only", "Intermediate (Mood Only)"),
        
        # Attempt 3: Safe Fallback (Ambient Genre Only)
        (FALLBACK_GENRE, "", "fallback", "Safe Fallback (Ambient Only)")
    ]
    
    for i, (current_genre, current_moods, query_type, attempt_name) in enumerate(attempts):
        
        # Build the specific query for this attempt
        current_query = _build_query(current_genre, current_moods, query_type)
        
        # Display attempt and query
        print(f"\n--- Attempt {i+1}: {attempt_name} ---")
        print(f"Using Query: {current_query}")
        
        tracks, error = _run_batched_search(current_query, num_tracks)
        
        if tracks:
            # Success: Found tracks on this attempt
            print(f"Successfully found {len(tracks)} tracks.")
            return tracks, current_query

        if error:
            # API Failure: Invalid genre, routing issue, etc. Move to next attempt.
            print(f"API Error detected: {error}. Moving to next attempt.")
        else:
            # 0 Tracks Found: Specificity issue. Move to next attempt.
            print("Zero tracks found for this query. Moving to next attempt.")

    return [], current_query # Returns empty list if all attempts fail


def generate_playlist():
    """
    Generate a Spotify playlist based on book parameters from Gemini.
    """

    # Step 1: Get Gemini keywords and page info
    data = generate_playlist_input()

    current_page = data.get("current_page", 0)
    total_pages = data.get("total_pages", 0)

    # Step 2: Compute number of tracks
    num_tracks = int(compute_playlist_length(current_page=current_page, total_pages=total_pages))

    # Step 3: Parse and Validate Gemini keywords
    gemini_response_str = data.get("response", "[]")
    validated_data = validate_and_extract_keywords(gemini_response_str)

    if not validated_data:
        print("Failed to generate valid Spotify keywords. Aborting playlist creation.")
        return
    
    primary_genre = validated_data['primary_genre']
    mood_keywords_string = validated_data['mood_keywords_string']
    
    # Step 4: Fetch tracks in batches using Search API with retry logic
    tracks, final_query = fetch_search_tracks(primary_genre, mood_keywords_string, num_tracks)

    # Step 5: Handle failure/success
    if not tracks:
        print(f"No tracks found after all attempts. Last query used: {final_query}")
        return

    # Prepare parameters for clean printing
    print("\n--- Final Search Query Summary ---")
    print(f"Primary Genre (Gemini Output): {primary_genre}")
    print(f"Mood Keywords (Gemini Output): {mood_keywords_string}")
    print(f"Final Successful Query: {final_query}")
    print("----------------------------------\n")

    # Step 6: Calculate total duration
    total_duration_ms = sum(track['duration_ms'] for track in tracks)
    total_duration_min = total_duration_ms / 60000

    # Step 7: Print track info interactively
    print(f"\n🎶 Generated Playlist Summary 🎶")
    print(f"Targeting: {data.get('book')}")
    print(f"Tracks Found: {len(tracks)} (Targeted: {num_tracks})")
    print(f"Total Duration: {total_duration_min:.1f} minutes\n")
    
    for i, track in enumerate(tracks, start=1):
        duration_ms = track['duration_ms']
        minutes, seconds = divmod(duration_ms // 1000, 60)
        formatted_duration = f"{minutes}:{seconds:02d}"

        artists = ", ".join([a['name'] for a in track['artists']])
        print(f"{i}. {track['name']} – {artists}")
        print(f"   Duration: {formatted_duration}")
        print(f"   Spotify URL: {track['external_urls']['spotify']}\n")


if __name__ == "__main__":
    generate_playlist()