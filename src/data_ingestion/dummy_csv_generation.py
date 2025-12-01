import ast
import time
import pandas as pd
from dummy_csv_prompting import generate_genre_keywords
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from src.processing.keys.spotify_client_info import CLIENT_ID, CLIENT_SECRET
import sys
import os 

# -------------------------------------------------------
# SPOTIFY SETUP (Using credentials from KEYS.py)
# -------------------------------------------------------
try:
    auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    sp.search(q="test", type="track", limit=1)
except Exception as e:
    print(f"Error: Failed to initialize Spotify API connection. Ensure CLIENT_ID/SECRET are correct and valid. Error: {e}")
    sys.exit(1)


# --- CONFIGURATION CONSTANTS ---
BATCH_SIZE = 20
WAIT_TIME_SECONDS = 0.5
MAX_SEARCH_LIMIT = 50 
TARGET_TRACKS_PER_CSV = 1000 # Fixed target as requested
FIXED_GENRE_BASE = 'ambient' # Fixed instrumental base
# -------------------------------

# --- Utility Functions ---

def validate_and_extract_keywords(gemini_response_str: str) -> str | None:
    """
    Safely parses the Gemini dictionary string, extracts the keyword list, and returns the combined string.
    """
    try:
        # Safely evaluate the string as a Python literal (dictionary or list wrapper)
        params = ast.literal_eval(gemini_response_str)
        
        # Robustly handle list wrapper (e.g., if output is [{'keywords': [...]}]
        if isinstance(params, list):
            if not params:
                print("Error: Gemini response is an empty list.")
                return None
            params = params[0] # Extract the dictionary from the list

        if not isinstance(params, dict):
            print(f"Error: Gemini response could not be extracted as a dictionary. Received type: {type(params)}")
            return None
        
        # --- NEW LOGIC: Extract the list from the 'keywords' key ---
        keywords_list = params.get('keywords')
        
        # Check for required keyword list structure
        if not isinstance(keywords_list, list) or len(keywords_list) < 3:
            print("Error: Missing or invalid 'keywords' list (needs 3 strings).")
            return None
            
    except Exception as e:
        print(f"Error: Failed to parse Gemini response string: {e}")
        return None

    # Combine the first three lowercase keywords into a single string
    mood_keywords_string = " ".join([str(k).lower().strip() for k in keywords_list[:3]])
    
    return mood_keywords_string

def _build_query(primary_genre: str, mood_keywords_string: str) -> str:
    """
    Constructs the Spotify search query string for the CSV backup.
    """
    ANTI_VOCAL_KEYWORDS = "instrumental"
    keywords = f"{primary_genre} {mood_keywords_string}"
    
    unsafe_map = {
        'romance': 'love', 'romantic': 'love',
        'sexy': 'emotional', 'sensual': 'emotional',
        'seductive': 'mysterious', 'passionate': 'emotional',
        'steamy': 'intense', 'erotic': 'dark', 'intimate': 'emotional'
    }
    
    sanitized_keywords = []
    for k in keywords:
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

    #return f"{ANTI_VOCAL_KEYWORDS} {mood_keywords_string}".strip() # <-- Put back in
    return f"instrumental ambient dreamy emotional love"  # <--- remove


def _run_batched_search(query: str, num_tracks: int, offset_start: int = 0):
    """
    Internal helper to execute the batched search for a given query.
    Returns (tracks, error)
    """
    all_tracks = []
    tracks_to_fetch = num_tracks
    offset = offset_start
    limit_per_call = min(BATCH_SIZE, MAX_SEARCH_LIMIT) 

    print(f"Starting batch search for query: '{query}'")

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
                print("--- Search ended: No more tracks found for this query. ---")
                break

            all_tracks.extend(tracks_batch)
            tracks_to_fetch -= len(tracks_batch)
            offset += len(tracks_batch)

            print(f"Fetched {len(all_tracks)} tracks so far (Target: {num_tracks}).")

            if tracks_to_fetch > 0:
                time.sleep(WAIT_TIME_SECONDS)
                
        except Exception as e:
            print(f"API Error during search batch: {e}")
            return [], str(e)

    return all_tracks, None 

def export_to_csv(tracks: list, target_genre: str, mood_keywords: str):
    """
    Converts track list into a DataFrame and exports it to a CSV file.
    It ensures the target directory exists before writing the file.
    """
    if not tracks:
        print("No tracks to export.")
        return

    # Extract relevant fields
    data = []
    for track in tracks:
        if 'artists' in track and track['artists'] and 'album' in track:
            track_data = {
                'track_name': track['name'],
                'artist_name': track['artists'][0]['name'],
                'album_name': track['album']['name'],
                'release_date': track['album']['release_date'],
                'track_id': track['id'],
                'spotify_url': track['external_urls']['spotify'],
                'mood_keywords': mood_keywords
            }
            data.append(track_data)

    df = pd.DataFrame(data)
    
    # Define the output directory and filename
    output_dir = "./data" 
    safe_genre = target_genre.lower().replace(' ', '_')
    filename = f"{output_dir}/{safe_genre}_backup.csv" # <-- put back in
    #filename = f"{output_dir}/instrumental_backup.csv"

    # --- Directory Check and Creation ---
    # The exist_ok=True argument prevents an error if the directory already exists.
    try:
        # os.makedirs works with relative paths and creates all necessary intermediate directories
        os.makedirs(output_dir, exist_ok=True)
        print(f"Ensured output directory exists: {os.path.abspath(output_dir)}")
    except OSError as e:
        print(f"Error creating directory {output_dir}. Check file system permissions: {e}")
        return
    # ---------------------------------------------
    
    df.to_csv(filename, index=False)
    
    print(f"\n✅ Successfully exported {len(df)} tracks to {filename}")


if __name__ == "__main__":
    
    # --- STEP 1: Define Target Genres ---
    TARGET_GENRES = ["Romance"]
    #["Fantasy", "Science Fiction", "Mystery","Thriller","Romance","Historical Fiction",
                    # "Horror","Young Adult","Contemporary Fiction","Literary Fiction","Dystopian",
                    # "Textbook","Classics","Graphic Novels","Biography"]
    print("\n--- Spotify Backup CSV Generator (Automated) ---")
    print(f"Processing {len(TARGET_GENRES)} genres, targeting {TARGET_TRACKS_PER_CSV} tracks each.")
    
    for genre in TARGET_GENRES:
        print("\n")
        print(f"STARTING GENRE: {genre}")
        
        # Step 2: Get mood keywords from Gemini
        gemini_response_str = generate_genre_keywords(genre)
        mood_keywords_string = validate_and_extract_keywords(gemini_response_str)

        if not mood_keywords_string:
            print(f"Skipping {genre} due to failed keyword generation.")
            continue
        
        # Step 3: Construct the search query
        search_query = _build_query(FIXED_GENRE_BASE, mood_keywords_string)
        
        # Step 4: Fetch the songs
        fetched_tracks, error = _run_batched_search(search_query, TARGET_TRACKS_PER_CSV)
        
        if error:
            print(f"Could not complete CSV generation for {genre} due to API error: {error}")
            continue
        
        # Step 5: Export to CSV
        export_to_csv(fetched_tracks, genre, mood_keywords_string)