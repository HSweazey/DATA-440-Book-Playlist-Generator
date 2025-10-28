import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import time
from typing import List, Dict, Any

# ==============================================================================
# 1. SETUP & CONFIGURATION
# ==============================================================================

# NOTE: REPLACE THESE WITH YOUR ACTUAL SPOTIFY DEVELOPER CREDENTIALS
CLIENT_ID = "b4e4a0fb88344c8d81d1419afa71d7a9"
CLIENT_SECRET = "574971712e62498e881e2af5416fc5ae"

# Initialize the Spotipy client
try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    ))
    print("✅ Spotify client initialized successfully.")
except Exception as e:
    print(f"❌ Error initializing Spotify client. Check your CLIENT_ID/SECRET. Error: {e}")
    sp = None

# --- Search and Filtering Parameters ---
SEARCH_QUERIES = [
    "instrumental", 
    "background music",
    "no vocals",
    "soundtrack",
    "score",
    "ambient",
    "lo-fi",
    "study music",
    "classical", 
    "piano solo",
    "jazz instrumental",
    "chillout"
]

# Filtering Cutoffs (Controls dataset quality and size)
POPULARITY_CUTOFF = 30                 # Minimum popularity (0-100)
INSTRUMENTALNESS_CUTOFF = 0.5          # Minimum instrumentalness (0.0-1.0)
SPEECHINESS_CUTOFF = 0.4               # Maximum speechiness (0.0-1.0)

# API parameters
MAX_TRACKS_PER_QUERY = 10             # Target max tracks to fetch per query (500 * 12 queries = ~6000 potential tracks)
PAGINATION_LIMIT = 50                  # The 'limit' parameter for a single API call (Spotify's maximum)
ALL_TRACK_IDS = set()                  # Tracks unique IDs to avoid duplicates across queries

# ==============================================================================
# 2. DATA EXTRACTION FUNCTION
# ==============================================================================

def extract_filtered_tracks(
    queries: List[str], 
    pop_cutoff: int, 
    inst_cutoff: float, 
    speech_cutoff: float, 
    max_limit: int
) -> pd.DataFrame:
    """Searches Spotify using pagination, filters tracks, and compiles data."""
    if sp is None:
        return pd.DataFrame()

    all_track_data = []
    
    for query in queries:
        print(f"\nSearching for: '{query}'...")
        tracks_fetched = 0
        
        # Initial search
        results = sp.search(q=query, limit=PAGINATION_LIMIT, type='track')
        
        # --- PAGINATION LOOP ---
        while results and tracks_fetched < max_limit:
            
            # 1. Identify unique, popular track IDs from the current page
            track_ids_to_process = []
            for track in results['tracks']['items']:
                if (track['popularity'] >= pop_cutoff) and (track['id'] not in ALL_TRACK_IDS):
                    track_ids_to_process.append(track['id'])
                    ALL_TRACK_IDS.add(track['id'])
            
            # 2. Get Audio Features for the filtered tracks

            if track_ids_to_process:
                time.sleep(1.0) # Increased delay (Step 1)
                
                try:
                    audio_features_list = sp.audio_features(track_ids_to_process)
                except spotipy.exceptions.SpotifyException as e:
                    print(f"  ⚠️ Rate Limit Hit (403 or similar). Waiting 10s and skipping this batch. Error: {e}")
                    time.sleep(10) # Wait a long time if an error occurs
                    continue # Skip to the next iteration (next page/query)
                
                # ... rest of the filtering code
                for features in audio_features_list:
                    if features: 
                        # Filtering logic
                        is_instrumental = features.get('instrumentalness', 0.0) >= inst_cutoff
                        is_low_speech = features.get('speechiness', 1.0) <= speech_cutoff
                        
                        if is_instrumental and is_low_speech:
                            # Find the corresponding track info
                            track_info = next((t for t in results['tracks']['items'] if t['id'] == features['id']), None)
                            
                            if track_info:
                                # Prepare the data row, collecting all key features for the recommender
                                data = {
                                    'track_id': track_info['id'],
                                    'track_name': track_info['name'],
                                    'artist': track_info['artists'][0]['name'],
                                    'album': track_info['album']['name'],
                                    'popularity': track_info['popularity'],
                                    # Duration is key for the playlist length match
                                    'duration_ms': features['duration_ms'],
                                    # Core features for filtering and recommendation
                                    'instrumentalness': features['instrumentalness'],
                                    'speechiness': features['speechiness'],
                                    'danceability': features['danceability'],
                                    'energy': features['energy'],
                                    'valence': features['valence'],
                                    'tempo': features['tempo'],
                                    'acousticness': features['acousticness'],
                                    'liveness': features['liveness'],
                                    'loudness': features['loudness'],
                                }
                                all_track_data.append(data)

            tracks_fetched += PAGINATION_LIMIT
            
            # 4. Move to the next page
            if results['tracks']['next'] and tracks_fetched < max_limit:
                results = sp.next(results['tracks'])
                # Increase the delay significantly between large pagination steps
                time.sleep(2)
            else:
                results = None # End the loop for this query

        print(f"  Query '{query}' complete. Unique instrumental tracks found so far: {len(ALL_TRACK_IDS)}")

    # Final DataFrame conversion and cleanup
    df = pd.DataFrame(all_track_data)
    if not df.empty:
        df = df.drop_duplicates(subset=['track_id']).reset_index(drop=True)
    return df

# ==============================================================================
# 3. EXECUTION
# ==============================================================================

if sp is not None:
    print("\n--- Starting Data Extraction ---")
    df_instrumental = extract_filtered_tracks(
        SEARCH_QUERIES, 
        POPULARITY_CUTOFF, 
        INSTRUMENTALNESS_CUTOFF, 
        SPEECHINESS_CUTOFF, 
        MAX_TRACKS_PER_QUERY
    )

    # Save the final dataset
    if not df_instrumental.empty:
        FILE_NAME = 'instrumental_tracks_data_large.csv'
        df_instrumental.to_csv(FILE_NAME, index=False)
        print("\n" + "="*40)
        print(f"🎉 SUCCESS! Extracted **{len(df_instrumental)}** unique instrumental tracks.")
        print(f"💾 Data saved to '{FILE_NAME}'.")
        print(f"Sample Data:\n{df_instrumental[['track_name', 'artist', 'popularity', 'duration_ms', 'instrumentalness']].head()}")
        print("="*40)
    else:
        print("\n⚠️ Extraction complete, but no tracks were saved. Check API credentials, or try lowering the cutoffs.")