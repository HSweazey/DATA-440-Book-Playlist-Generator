import math
import ast
from generate_playlist_input import generate_playlist_input
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from KEYS import CLIENT_ID, CLIENT_SECRET

# -------------------------------------------------------
# SPOTIFY SETUP
# -------------------------------------------------------
auth_manager = SpotifyClientCredentials(client_id = CLIENT_ID, client_secret = CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Average song length in minutes
AVG_SONG_LENGTH_MIN = 3

def compute_playlist_length(current_page: int, total_pages: int) -> int:
    """
    Compute number of songs based on pages left and average song length.
    """

    pages_left = max(0, total_pages - current_page)
    return max(1, math.ceil(pages_left / AVG_SONG_LENGTH_MIN))

def generate_playlist():
    """
    Generate a Spotify playlist based on book keywords from Gemini.
    """

    # Step 1: Get Gemini keywords and page info
    data = generate_playlist_input()

    print(data)

    current_page = data.get("current_page", 0)
    total_pages = data.get("total_pages", 0)
    pages_left = max(0, total_pages - current_page)

    # Step 2: Compute number of tracks
    num_tracks = compute_playlist_length(current_page=current_page, total_pages=total_pages)

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

    # Step 4: Search Spotify for initial playlist
    try:
        results = sp.search(q=keywords_input, type="track", limit=num_tracks)
        tracks = results.get('tracks', {}).get('items', [])
    except Exception as e:
        print(f"Error searching Spotify: {e}")
        return

    if not tracks:
        print(f"No tracks found for keywords: {keywords_input}")
        return

    # Step 5: Check total playlist duration
    total_duration_min = sum(track['duration_ms'] for track in tracks) / 60000  # convert ms to minutes
    if total_duration_min < pages_left:
        print(f"Playlist duration ({total_duration_min:.1f} min) is less than pages left ({pages_left}). Adding 10 more songs.")
        try:
            extra_results = sp.search(q=keywords_input, type="track", limit=10)
            extra_tracks = extra_results.get('tracks', {}).get('items', [])
            tracks.extend(extra_tracks)
            total_duration_min = sum(track['duration_ms'] for track in tracks) / 60000
        except Exception as e:
            print(f"Error adding extra songs: {e}")

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