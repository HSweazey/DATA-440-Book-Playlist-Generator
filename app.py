import streamlit as st
import pandas as pd
import re
import time
import json
import ast

# Imports
from src.processing.generate_playlist_csv_app import get_final_tracks 
from src.processing.csv_backup_generation_app import generate_backup_playlist, UI_GENRE_OPTIONS

# --- UI CONFIGURATION ---
st.set_page_config(page_title="🎧 Reading Playlist Generator", layout="centered", initial_sidebar_state="collapsed")
if 'debug_info' not in st.session_state: st.session_state['debug_info'] = {}

custom_css = """
<style>
[data-testid="stAppViewContainer"] { background-color: #1a1a2e; color: #e0e0e0; }
.stButton>button { background-color: #f7b731; color: #1a1a2e; border-radius: 12px; border: 1px solid #d39c28; font-weight: bold; }
.stTextInput>div>div>input, .stNumberInput>div>div>input { background-color: #2c2c44; color: #f0f0f0; border-radius: 8px; border: 1px solid #4a4a6e; }
[data-testid="stForm"] { background-color: #202035; border-radius: 15px; padding: 20px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5); }
h1, h2, h3 { color: #f7b731; }
.stSelectbox>div>div>div { background-color: #2c2c44; color: white; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- HELPERS ---
def convert_to_csv(tracks):
    if not isinstance(tracks, list) or not all(isinstance(t, dict) for t in tracks) or not tracks:
        return pd.DataFrame().to_csv(index=False).encode('utf-8')
    return pd.DataFrame(tracks).to_csv(index=False).encode('utf-8')

def convert_to_json(tracks):
    if not isinstance(tracks, list) or not all(isinstance(t, dict) for t in tracks) or not tracks:
         return "{}"
    return json.dumps(tracks, indent=4).encode('utf-8')

def extract_spotify_track_id(spotify_url: str) -> str | None:
    match = re.search(r'track/([^?]+)', spotify_url)
    if match: return match.group(1)
    return None

def display_embedded_tracks(tracks: list):
    if not tracks:
        st.warning("No tracks were generated.")
        return
    EMBED_LIMIT = 6 
    featured_tracks = tracks[:EMBED_LIMIT]
    remaining_tracks = tracks[EMBED_LIMIT:]

    st.subheader(f"🎧 Playlist Preview (Top {len(featured_tracks)})")
    st.markdown("---")
    cols_featured = st.columns(2)
    for i, track in enumerate(featured_tracks):
        track_id = extract_spotify_track_id(track.get('spotify_url', ''))
        with cols_featured[i % 2]:
            if track_id:
                embed_url = f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator"
                embed_html = f"""<iframe src="{embed_url}" width="100%" height="80" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>"""
                st.components.v1.html(embed_html, height=100)
            else:
                st.error(f"Could not embed: {track.get('track_name')}")

    if remaining_tracks:
        st.markdown("<br>", unsafe_allow_html=True) 
        st.subheader(f"📋 Full Track List ({len(remaining_tracks)} more)")
        st.markdown("---")
        cols_list = st.columns(2)
        for i, track in enumerate(remaining_tracks):
            track_name = track.get('track_name', 'Unknown Title')
            artist_name = track.get('artist_name', 'Unknown Artist')
            spotify_url = track.get('spotify_url', '#')
            card_html = f"""
            <div style="background-color: #2c2c44; padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 1px solid #4a4a6e; display: flex; justify-content: space-between; align-items: center;">
                <div style="overflow: hidden; white-space: nowrap; text-overflow: ellipsis; padding-right: 10px;">
                    <strong style="color: #f0f0f0;">{track_name}</strong><br>
                    <span style="color: #bbb; font-size: 0.85em;">{artist_name}</span>
                </div>
                <a href="{spotify_url}" target="_blank" style="background-color: #f7b731; color: #1a1a2e; padding: 6px 12px; text-decoration: none; font-size: 0.8em; font-weight: bold; border-radius: 15px; white-space: nowrap;">Play ↗</a>
            </div>
            """
            with cols_list[i % 2]:
                st.markdown(card_html, unsafe_allow_html=True)

def display_export_buttons(tracks: list, book_title: str):
    if not tracks or not isinstance(tracks, list): return
    safe_title = re.sub(r'[^\w\-_\. ]', '', book_title.lower().replace(' ', '_'))
    csv_data = convert_to_csv(tracks)
    json_data = convert_to_json(tracks)
    st.subheader("⬇️ Export Playlist")
    col_csv, col_json = st.columns(2)
    with col_csv: st.download_button("Download as CSV", csv_data, f"{safe_title}_playlist.csv", "text/csv", type="primary")
    with col_json: st.download_button("Download as JSON", json_data, f"{safe_title}_playlist.json", "application/json", type="secondary")

# --- MAIN LOGIC ---
st.title("📚 Reading Playlist Creator")
st.markdown("A personalized reading playlist powered by AI and Spotify.")

# 1. MAIN FORM
with st.form("playlist_input_form"):
    st.subheader("Book Details")
    book_title = st.text_input("Book Title", placeholder="e.g., 'The Midnight Library'")
    author_name = st.text_input("Author Name", placeholder="e.g., Matt Haig")
    page_count = st.number_input("Total Page Count", min_value=1, value=300)
    submitted = st.form_submit_button("Generate My Custom Playlist ✨")

# 2. STATE MANAGEMENT FOR FALLBACK
if 'fallback_needed' not in st.session_state:
    st.session_state['fallback_needed'] = False

if submitted:
    if book_title and author_name and page_count > 0:
        # Clear previous debug info on new submit
        st.session_state['debug_info'] = {}

        with st.spinner(f"Curating your perfect reading soundtrack..."):
            final_tracks = get_final_tracks(book_title, author_name, page_count)

        # CHECK FOR FAILURE STATUS
        if isinstance(final_tracks, dict) and final_tracks.get('status') == "FAIL_NEED_GENRE":
            st.session_state['fallback_needed'] = True
            st.error(f"⚠️ Generation failed: {final_tracks.get('reason')}")
            st.info("The automated system could not build a playlist. Please select a genre manually below to generate a backup playlist.")
        
        elif isinstance(final_tracks, list) and final_tracks:
            # Success!
            st.session_state['fallback_needed'] = False # Reset
            
            # --- AESTHETIC STATUS UPDATES (No more debug menu) ---
            if 'gemini_parsed' in st.session_state['debug_info']:
                g_info = st.session_state['debug_info']['gemini_parsed']
                if isinstance(g_info, dict):
                    moods = g_info.get('Mood Keywords', 'N/A')
                    st.toast(f"🧠 AI Vibes Detected: {moods}", icon='✨')
            
            if 'target_metrics' in st.session_state['debug_info']:
                metrics = st.session_state['debug_info']['target_metrics']
                count = metrics.get('num_tracks_target', 0)
                st.toast(f"🎯 Target: {count} tracks for your reading session.", icon='📖')

            display_export_buttons(final_tracks, book_title)
            st.markdown("---")
            display_embedded_tracks(final_tracks)
        else:
            st.error("Unknown error. Please try again.")

# 3. FALLBACK UI (Shows only if generation failed)
if st.session_state.get('fallback_needed'):
    st.markdown("---")
    st.subheader("📂 Manual Backup Generator")
    with st.form("backup_form"):
        # Dropdown with Nice Names
        selected_genre_name = st.selectbox("Select Book Genre:", options=list(UI_GENRE_OPTIONS.keys()))
        backup_submit = st.form_submit_button("Generate Backup Playlist 📂")

    if backup_submit:
        # Get the code (e.g., "b") from the name (e.g., "Biography")
        genre_code = UI_GENRE_OPTIONS[selected_genre_name]
        
        with st.spinner("Loading backup tracks..."):
            backup_tracks = generate_backup_playlist(total_pages=page_count, genre_code=genre_code)
        
        # Display results
        if backup_tracks:
            # Add Spotify URL format for UI compatibility if missing
            for t in backup_tracks:
                if 'spotify_url' not in t: t['spotify_url'] = None

            display_export_buttons(backup_tracks, book_title)
            st.markdown("---")
            display_embedded_tracks(backup_tracks)
            st.success(f"Generated {len(backup_tracks)} tracks from {selected_genre_name} backup.")
        else:
            st.error("Could not load backup tracks.")