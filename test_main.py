from src.processing.generate_playlist_fixed_g import *

#generate_playlist()
import os
import pandas as pd

folder = "data"   # <-- update this

for file in os.listdir(folder):
    if file.endswith(".csv"):
        filepath = os.path.join(folder, file)
        df = pd.read_csv(filepath)

        # Group by both fields
        grouped = (
            df.groupby(['track_name', 'artist_name'])
              .size()
              .reset_index(name='count')
        )

        # Keep only groups that appear more than once
        duplicates = grouped[grouped['count'] > 1]

        print(f"\n=== {file} ===")
        if duplicates.empty:
            print("No duplicates found.")
        else:
            print("Duplicate groups (track_name + artist_name):")
            print(duplicates)
