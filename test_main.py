from src.processing.generate_playlist_fixed_g import *
import pandas as pd
import os

generate_playlist() #<-- For running

# folder = "data"   # <-- update this

# for file in os.listdir(folder):
#     if file.endswith(".csv"):
#         filepath = os.path.join(folder, file)
#         df = pd.read_csv(filepath)

#         print("Original DataFrame:")
#         print(df)

#         # Group by both fields
#         grouped = (
#             df.groupby(['track_name', 'artist_name'])
#               .size()
#               .reset_index(name='count')
#         )

#         # Keep only groups that appear more than once
#         duplicates = grouped[grouped['count'] > 1]

#         print(f"\n=== {file} ===")
#         if duplicates.empty:
#             print("No duplicates found.")
#         else:
#             print("Duplicate groups (track_name + artist_name):")
#             print(duplicates)
        
    #     df_no_duplicates = df.drop_duplicates(subset=['track_name', 'artist_name'])

    # print("\nDataFrame after removing duplicates based on 'col1' and 'col2':")
    # print(df_no_duplicates)

    # output_dir = "./data" 

    # #filename = f"{output_dir}/{safe_genre}_backup.csv" # <-- put back in
    # filename = filepath

    # # --- Directory Check and Creation ---
    # # The exist_ok=True argument prevents an error if the directory already exists.
    # try:
    #     # os.makedirs works with relative paths and creates all necessary intermediate directories
    #     os.makedirs(output_dir, exist_ok=True)
    #     print(f"Ensured output directory exists: {os.path.abspath(output_dir)}")
    # except OSError as e:
    #     print(f"Error creating directory {output_dir}. Check file system permissions: {e}")
    # # ---------------------------------------------
    # df_no_duplicates.to_csv(filename, index=False)
