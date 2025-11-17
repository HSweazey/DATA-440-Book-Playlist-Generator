# Install dependencies first:
# pip install spotipy pandas

import pandas as pd
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

# --- SETUP ---
CLIENT_ID = "b4e4a0fb88344c8d81d1419afa71d7a9"
CLIENT_SECRET = "574971712e62498e881e2af5416fc5ae"

auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = Spotify(auth_manager=auth_manager)

# --- USER INPUT ---
queries = [
    "instrumental lofi",
    "ambient piano",
    "cinematic soundtrack"
]

num_tracks_per_query = 5  # you can change this

# --- MAIN LOOP ---
all_tracks = []

for query in queries:
    print(f"Searching Spotify for '{query}'...")
    results = sp.search(q=query, type="track", limit=num_tracks_per_query)
    tracks = results['tracks']['items']

    # Collect track IDs for audio feature lookup
    track_ids = [t['id'] for t in tracks if t['id']]

    if not track_ids:
        continue

    # Get audio features (includes instrumentalness, speechiness, etc.)
    features = sp.audio_features(track_ids)
    features = {f['id']: f for f in features if f}  # map ID → features

    for t in tracks:
        tid = t['id']
        f = features.get(tid, {})

        all_tracks.append({
            "query": query,
            "track_name": t['name'],
            "artist": t['artists'][0]['name'],
            "album": t['album']['name'],
            "release_date": t['album']['release_date'],
            "popularity": t['popularity'],
            "duration_ms": t['duration_ms'],
            "duration_min": round(t['duration_ms'] / 60000, 2),
            "spotify_url": t['external_urls']['spotify'],
            "instrumentalness": f.get('instrumentalness'),
            "speechiness": f.get('speechiness'),
            "acousticness": f.get('acousticness'),
            "energy": f.get('energy'),
            "valence": f.get('valence'),
            "tempo": f.get('tempo'),
        })

# --- CONVERT TO DATAFRAME ---
df = pd.DataFrame(all_tracks)

print("\n✅ Retrieved", len(df), "tracks total.\n")
print(df.head())

# Optionally save to CSV
df.to_csv("spotify_track_metadata.csv", index=False)
print("\n💾 Data saved to 'spotify_track_metadata.csv'")