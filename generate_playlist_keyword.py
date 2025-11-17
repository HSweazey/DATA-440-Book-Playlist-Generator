import math
import ast
import time
from generate_playlist_inputv1 import generate_playlist_input
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

# Constants for Batching
BATCH_SIZE = 20 # Number of tracks to request per API call
WAIT_TIME_SECONDS = 0.5 # Wait time between batches to prevent overwhelming the API

def compute_playlist_length(total_pages: int = 100) -> int:
    """
    Compute number of songs based on pages left and average song length.
    """

    readtime = total_pages * AVG_PAGE_SPEED_MIN

    print(max(1, math.ceil(readtime / AVG_SONG_LENGTH_MIN)))
    return (max(1, math.ceil(readtime / AVG_SONG_LENGTH_MIN)))

def search_spotify_in_batches(sp, keywords_input: str, num_tracks: int) -> list:
    """
    Searches Spotify for the required number of tracks in batches,
    with a small delay between each call.
    """
    all_tracks = []
    tracks_to_fetch = num_tracks
    offset = 0

    while tracks_to_fetch > 0:
        limit = min(BATCH_SIZE, tracks_to_fetch)
        print(f"Searching Spotify for {limit} tracks with offset {offset}...")

        try:
            results = sp.search(q=keywords_input, type="track", limit=limit, offset=offset)
            tracks_batch = results.get('tracks', {}).get('items', [])
            all_tracks.extend(tracks_batch)

            if not tracks_batch:
                print("No more tracks found in this batch.")
                break # Stop if no tracks are returned

            tracks_to_fetch -= len(tracks_batch)
            offset += len(tracks_batch)

            # Wait time before the next request
            if tracks_to_fetch > 0:
                print(f"Waiting for {WAIT_TIME_SECONDS} seconds...")
                time.sleep(WAIT_TIME_SECONDS)

        except Exception as e:
            print(f"Error searching Spotify in batch: {e}")
            break

    return all_tracks


def generate_playlist():
    """
    Generate a Spotify playlist based on book keywords from Gemini.
    """

    # Step 1: Get Gemini keywords and page info
    data = generate_playlist_input()

    print(data)

    total_pages = data.get("total_pages", 0)

    # Step 2: Compute number of tracks
    num_tracks = int(compute_playlist_length(total_pages=total_pages))

    # Step 3: Parse Gemini response safely into a list
    gemini_response = data.get("response", [])
    keywords_list = []

    if isinstance(gemini_response, str):
        try:
            keywords_list = ast.literal_eval(gemini_response)
        except Exception as e:
            print(f"Warning: failed to parse Gemini response string: {e}")
            return
    elif isinstance(gemini_response, list):
        keywords_list = gemini_response
    else:
        print(f"Unexpected Gemini response type: {type(gemini_response)}")
        return

    # Strip whitespace and ensure non-empty keywords
    keywords_list = [str(k).strip() for k in keywords_list if str(k).strip()]

    if not keywords_list:
        print(f"No keywords generated from Gemini response: {gemini_response}")
        return

    keywords_input = ",".join(keywords_list)

    # Step 4: Search Spotify for initial playlist in batches
    tracks = search_spotify_in_batches(sp, keywords_input, num_tracks)

    if not tracks:
        print(f"No tracks found for keywords: {keywords_input}")
        return

    # Step 5: Check total playlist duration (Simplified: no extra songs added here
    # to keep the logic focused on the batched search, as the original logic was
    # flawed/incomplete for adding extra songs by searching with the same query)
    total_duration_ms = sum(track['duration_ms'] for track in tracks)
    total_duration_min = total_duration_ms / 60000  # convert ms to minutes

    # Step 6: Print track info interactively
    print(f"\n🎶 Generated playlist ({len(tracks)} tracks, approx. {total_duration_min:.1f} minutes) for keywords: {keywords_input}\n")
    for i, track in enumerate(tracks, start=1):
        duration_ms = track['duration_ms']
        minutes, seconds = divmod(duration_ms // 1000, 60)
        formatted_duration = f"{minutes}:{seconds:02d}"

        print(f"{i}. {track['name']} – {track['artists'][0]['name']}")
        print(f"   Duration: {formatted_duration}")
        print(f"   Spotify URL: {track['external_urls']['spotify']}\n")


if __name__ == "__main__":
    generate_playlist()