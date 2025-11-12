import math
import ast
from generate_playlist_input import generate_playlist_input
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from KEYS import CLIENT_ID, CLIENT_SECRET

# -------------------------------------------------------
# SPOTIFY SETUP
# -------------------------------------------------------
auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Average song length in minutes
AVG_SONG_LENGTH_MIN = 3

def compute_playlist_length(current_page: int, total_pages: int) -> int:
    """Compute number of songs based on pages left and average song length."""
    pages_left = max(0, total_pages - current_page)
    return max(1, math.ceil(pages_left / AVG_SONG_LENGTH_MIN))

def generate_playlist():
    """Generate a Spotify playlist based on book keywords from Gemini."""
    # Step 1: Get Gemini keywords and page info
    data = generate_playlist_input()

    current_page = data.get("current_page", 0)
    total_pages = data.get("total_pages", 0)

    # Step 2: Compute number of tracks
    num_tracks = compute_playlist_length(current_page=current_page, total_pages=total_pages)

    # Step 3: Parse Gemini response safely into a list
    gemini_response_str = data.get("response", "[]")  # <-- MUST use "response"
    if not gemini_response_str:
        print("No response returned from Gemini.")
        return

    # Remove wrapping quotes if present
    gemini_response_str = gemini_response_str.strip()
    if gemini_response_str.startswith('"') and gemini_response_str.endswith('"'):
        gemini_response_str = gemini_response_str[1:-1]

    # Convert the string to a list of keywords
    keywords_list = []
    try:
        # Remove square brackets, then split by comma
        for k in gemini_response_str.strip("[]").split(","):
            clean_k = k.strip().strip("'\"")
            if clean_k:
                keywords_list.append(clean_k)
    except Exception as e:
        print(f"Warning: failed to parse Gemini response: {e}")
        return

    if not keywords_list:
        print(f"No keywords generated from Gemini response: {gemini_response_str}")
        return

    # Prepare keywords string for Spotify search
    keywords_input = ",".join(keywords_list)

    # Step 4: Search Spotify
    try:
        results = sp.search(q=keywords_input, type="track", limit=num_tracks)
        tracks = results.get('tracks', {}).get('items', [])
    except Exception as e:
        print(f"Error searching Spotify: {e}")
        return

    if not tracks:
        print(f"No tracks found for keywords: {keywords_input}")
        return

    # Step 5: Print track info interactively
    print(f"\n🎶 Found {len(tracks)} tracks for keywords: {keywords_input}\n")
    for i, track in enumerate(tracks, start=1):
        duration_ms = track['duration_ms']
        minutes, seconds = divmod(duration_ms // 1000, 60)
        formatted_duration = f"{minutes}:{seconds:02d}"

        print(f"{i}. {track['name']} – {track['artists'][0]['name']}")
        print(f"   Duration: {formatted_duration}")
        print(f"   Spotify URL: {track['external_urls']['spotify']}\n")

if __name__ == "__main__":
    generate_playlist()
