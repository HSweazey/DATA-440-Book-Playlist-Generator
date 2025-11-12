# Install dependencies first:
# pip install spotipy

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# --- SETUP ---
CLIENT_ID = "b4e4a0fb88344c8d81d1419afa71d7a9"
CLIENT_SECRET = "574971712e62498e881e2af5416fc5ae"

auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# --- USER INPUT ---
keywords = input("Enter your search keywords (e.g. 'instrumental lofi chill'): ")
num_tracks = int(input("How many tracks do you want to retrieve? "))

# --- SEARCH ---
results = sp.search(q=keywords, type="track", limit=num_tracks)

tracks = results['tracks']['items']

if tracks:
    print(f"\n🎶 Found {len(tracks)} tracks for '{keywords}':\n")
    for i, track in enumerate(tracks, start=1):
        print(f"{i}. {track['name']} – {track['artists'][0]['name']}")
        print(f"   Album: {track['album']['name']}")
        print(f"   Release Date: {track['album']['release_date']}")
        print(f"   Popularity: {track['popularity']}")
        print(f"   Spotify URL: {track['external_urls']['spotify']}\n")
else:
    print("No tracks found for that search.")