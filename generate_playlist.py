import os
import math
import csv
from generate_playlist_input import generate_playlist_input
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from KEYS import CLIENT_ID, CLIENT_SECRET, DUMMY_ID, DUMMY_SECRET

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------
# Use real key if available, else dummy keys
CLIENT_ID = CLIENT_ID
CLIENT_SECRET = CLIENT_SECRET

# Setup Spotify client
auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Average song length in minutes
AVG_SONG_LENGTH_MIN = 3

def compute_playlist_length(current_page: int, total_pages: int) -> int:
    """Compute number of songs based on pages left and average song length."""
    pages_left = max(0, total_pages - current_page)
    num_songs = max(1, math.ceil(pages_left / AVG_SONG_LENGTH_MIN))
    return num_songs

def generate_playlist():
    # Step 1: Get Gemini keywords and page info
    data = generate_playlist_input()
    
    # Step 2: Compute number of tracks
    num_tracks = compute_playlist_length(
        current_page=data.get("current_page", 0),
        total_pages=data.get("total_pages", 0)
    )
    
    # Step 3: Prepare keywords for Spotify
    keywords_input = data.get("keywords", "")
    # Remove brackets if Gemini returned a Python list string
    keywords_input = keywords_input.strip("[]").replace("'", "").replace('"', '')
    
    # Step 4: Search Spotify
    results = sp.search(q=keywords_input, type="track", limit=num_tracks)
    tracks = results['tracks']['items']
    
    if not tracks:
        print(f"No tracks found for '{keywords_input}'.")
        return

    # Step 5: Collect data and print
    track_data_for_csv = []
    for i, track in enumerate(tracks, start=1):
        duration_ms = track['duration_ms']
        total_seconds = int(duration_ms / 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        formatted_duration = f"{minutes}:{seconds:02d}"

        print(f"{i}. {track['name']} – {track['artists'][0]['name']}")
        print(f"   Album: {track['album']['name']}")
        print(f"   Duration: {formatted_duration}")
        print(f"   Release Date: {track['album']['release_date']}")
        print(f"   Popularity: {track['popularity']}")
        print(f"   Spotify URL: {track['external_urls']['spotify']}\n")

        track_data_for_csv.append({
            'ID': i,
            'Name': track['name'],
            'Artist': track['artists'][0]['name'],
            'Album': track['album']['name'],
            'Duration': formatted_duration,
            'Release_Date': track['album']['release_date'],
            'Popularity': track['popularity'],
            'Spotify_URL': track['external_urls']['spotify']
        })

    # Step 6: Save CSV
    output_filename = f"{data.get('book','playlist').replace(' ','_')}_spotify_tracks.csv"
    fieldnames = ['ID', 'Name', 'Artist', 'Album', 'Duration', 'Release_Date', 'Popularity', 'Spotify_URL']

    if os.path.exists(output_filename):
        print(f"⚠️ Warning: File '{output_filename}' already exists and will be overwritten.")

    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(track_data_for_csv)
        print(f"✅ Successfully wrote {len(track_data_for_csv)} tracks to '{output_filename}'")
    except Exception as e:
        print(f"❌ An error occurred while writing the CSV file: {e}")


if __name__ == "__main__":
    generate_playlist()
