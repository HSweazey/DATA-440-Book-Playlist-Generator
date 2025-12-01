import spotipy
import math
import os
import csv
from spotipy.oauth2 import SpotifyClientCredentials
from src.processing.keys.spotify_client_info import CLIENT_ID, CLIENT_SECRET

# --- SETUP ---
CLIENT_ID = CLIENT_ID
CLIENT_SECRET = CLIENT_SECRET

auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# --- USER INPUT ---
keywords = input("Enter your search keywords (e.g. 'instrumental,lofi,chill'): ")
num_tracks = int(input("How many tracks do you want to retrieve? "))

# --- SEARCH ---
results = sp.search(q=keywords, type="track", limit=num_tracks)

tracks = results['tracks']['items']

if tracks:
    print(f"\n🎶 Found {len(tracks)} tracks for '{keywords}':\n")
    track_data_for_csv = []
    
    for i, track in enumerate(tracks, start=1):
        
        # 1. Get duration in milliseconds
        duration_ms = track['duration_ms']
        
        # 2. Convert to minutes and seconds (using integer division and modulo)
        # Note: We use math.floor to ensure we get a whole number of minutes.
        total_seconds = int(duration_ms / 1000)
        minutes = math.floor(total_seconds / 60)
        seconds = total_seconds % 60
        
        # 3. Format seconds to always have two digits (e.g., 05 instead of 5)
        formatted_duration = f"{minutes}:{seconds:02d}"

        print(f"{i}. {track['name']} – {track['artists'][0]['name']}")
        print(f"   Album: {track['album']['name']}")
        print(f"   Duration: {formatted_duration}") # <- NEW LINE ADDED
        print(f"   Release Date: {track['album']['release_date']}")
        print(f"   Popularity: {track['popularity']}")
        print(f"   Spotify URL: {track['external_urls']['spotify']}\n")

        # 2. Collect the data into a dictionary
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
else:
    print("No tracks found for that search.")

output_filename = "test_spotify_tracks.csv"
fieldnames = ['ID', 'Name', 'Artist', 'Album', 'Duration', 'Release_Date', 'Popularity', 'Spotify_URL']

# Check if the file already exists and provide feedback
if os.path.exists(output_filename):
    print(f"⚠️ Warning: File '{output_filename}' already exists and will be overwritten.")

# 4. Write the data to the CSV file
try:
    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write the header row
        writer.writeheader()
        
        # Write all the track data rows
        writer.writerows(track_data_for_csv)
        
    print(f"✅ Successfully wrote {len(track_data_for_csv)} tracks to '{output_filename}'")
    
except Exception as e:
    print(f"❌ An error occurred while writing the CSV file: {e}")