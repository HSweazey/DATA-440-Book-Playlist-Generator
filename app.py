import streamlit as st
import pandas as pd
import re
import time
import json

# CORRECT IMPORT: Pointing to the CSV_APP file which contains 'get_final_tracks'
from src.processing.generate_playlist_csv_app import get_final_tracks 

# --- UI CONFIGURATION ---
st.set_page_config(
    page_title="🎧 Reading Playlist Generator", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# In app.py (near the top)
if 'debug_info' not in st.session_state:
    st.session_state['debug_info'] = {}

custom_css = """
<style>
[data-testid="stAppViewContainer"] {
    background-color: #1a1a2e; 
    color: #e0e0e0; 
}
.stButton>button {
    background-color: #f7b731; 
    color: #1a1a2e; 
    border-radius: 12px;
    border: 1px solid #d39c28;
    font-weight: bold;
}
.stTextInput>div>div>input, .stNumberInput>div>div>input {
    background-color: #2c2c44; 
    color: #f0f0f0;
    border-radius: 8px;
    border: 1px solid #4a4a6e;
}
[data-testid="stForm"] {
    background-color: #202035; 
    border-radius: 15px; 
    padding: 20px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5); 
}
h1, h2, h3 { color: #f7b731; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- LOGIC WRAPPERS ---
def convert_to_csv(tracks: list) -> str:
    """Converts the list of track dictionaries to a CSV string."""
    if not tracks:
        return ""
    # Ensure all required columns are present for the DataFrame
    df = pd.DataFrame(tracks)
    return df.to_csv(index=False).encode('utf-8')

def convert_to_json(tracks: list) -> str:
    """Converts the list of track dictionaries to a JSON string."""
    return json.dumps(tracks, indent=4) # Use json.dumps for clean formatting

def extract_spotify_track_id(spotify_url: str) -> str | None:
    match = re.search(r'track/([^?]+)', spotify_url)
    if match: return match.group(1)
    return None

def display_embedded_tracks(tracks: list):
    if not tracks:
        st.warning("No tracks were generated. Please check the logs or try a different book.")
        return

    st.subheader(f"🎶 Your Reading Playlist ({len(tracks)} Tracks)")
    st.markdown("---")
    cols = st.columns(2)
    
    for i, track in enumerate(tracks):
        track_id = extract_spotify_track_id(track.get('spotify_url', ''))
        
        if track_id:
            # --- CORRECTED LINE ---
            embed_url = f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator"
            
            embed_html = f"""
            <iframe src="{embed_url}" width="100%" height="80" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>
            """
            with cols[i % 2]: 
                st.components.v1.html(embed_html, height=100)
        else:
            # Fallback for tracks with missing IDs/URLs
            with cols[i % 2]:
                 st.markdown(f"**{track.get('track_name', 'Unknown Track')}** by {track.get('artist_name', 'Unknown Artist')} (URL error)")

def generate_playlist_ui_wrapper(book_title, author_name, page_count):
    with st.spinner(f"Generating playlist..."):
        try:
            final_tracks = get_final_tracks(book_title, author_name, page_count)
            return final_tracks
        except Exception as e:
            st.error(f"❌ Error: {e}")
            return []

def display_export_buttons(tracks: list, book_title: str):
    if not tracks:
        return

    # Sanitize book title for filename (using your existing logic from generate_playlist_csv.py)
    safe_title = re.sub(r'[^\w\-_\. ]', '', book_title.lower().replace(' ', '_'))
    
    # 1. Prepare CSV data
    csv_data = convert_to_csv(tracks)
    csv_filename = f"{safe_title}_playlist.csv"

    # 2. Prepare JSON data
    json_data = convert_to_json(tracks)
    json_filename = f"{safe_title}_playlist.json"

    st.subheader("⬇️ Export Playlist")
    
    # Use columns to place buttons side-by-side
    col_csv, col_json = st.columns(2)
    
    with col_csv:
        st.download_button(
            label="Download as CSV",
            data=csv_data,
            file_name=csv_filename,
            mime="text/csv",
            type="primary" # Uses the custom primary color
        )
    
    with col_json:
        st.download_button(
            label="Download as JSON",
            data=json_data,
            file_name=json_filename,
            mime="application/json",
            type="secondary" # Uses the default secondary color
        )

# --- MAIN LAYOUT ---
st.title("📚 Reading Playlist Creator")
st.markdown("A personalized reading playlist powered by AI and Spotify.")

with st.form("playlist_input_form"):
    st.subheader("Book Details")
    book_title = st.text_input("Book Title", placeholder="e.g., 'The Midnight Library'")
    author_name = st.text_input("Author Name", placeholder="e.g., Matt Haig")
    page_count = st.number_input("Total Page Count", min_value=1, value=300)
    submitted = st.form_submit_button("Generate My Custom Playlist ✨")

if submitted:
    if book_title and author_name and page_count > 0:
        
        # Ensure session state is initialized before running the function
        if 'debug_info' not in st.session_state:
            st.session_state['debug_info'] = {}

        final_tracks = generate_playlist_ui_wrapper(book_title, author_name, page_count)

        # --- DEBUG DISPLAY 1: Toasts for quick alerts ---
        if 'gemini_parsed' in st.session_state['debug_info']:
            g_info = st.session_state['debug_info']['gemini_parsed']
            
            # --- FIX: Check if g_info is a dictionary before using .get() ---
            if isinstance(g_info, dict):
                st.toast(f"✅ Gemini Moods: {g_info.get('Mood Keywords', 'N/A')}", icon='🧠')
            else:
                # If it's not a dict, display the error string directly
                st.toast(f"❌ Gemini Error: {g_info}", icon='⚠️')
            # --- END FIX ---
            
        if 'spotify_query' in st.session_state['debug_info']:
            s_info = st.session_state['debug_info']
            st.toast(f"🎵 Spotify: Found {s_info.get('tracks_returned', 0)} tracks using '{s_info.get('successful_attempt', 'N/A')}'", icon='🎶')
        
        # --- DEBUG DISPLAY 2: Detailed Expander ---
        with st.expander("🛠️ Debug Information (Gemini & Spotify Queries)"):
            # Retrieve data from session state
            debug_info = st.session_state['debug_info']
            target_metrics = debug_info.get('target_metrics', {})
            
            st.subheader("⏱️ Read Time & Target Metrics")
            st.markdown(f"**Target Read Time**: **{target_metrics.get('target_read_time_min', 'N/A')} minutes**")
            st.markdown(f"**Target Track Count**: **{target_metrics.get('num_tracks_target', 'N/A')}**")
            # Retrieve the data
            gemini_output = st.session_state['debug_info'].get('gemini_parsed', {'status': 'Error: Not available'}) # <-- Error is sourced here

            st.subheader("Gemini Output")

            # --- VULNERABLE CODE BLOCK (WHERE YOU NEED TO ADD THE FIX) ---
            # It currently looks like:
            # st.json(gemini_output) 
            
            # --- REPLACE WITH THE TYPE-CHECKED FIX ---
            if isinstance(gemini_output, dict):
                st.json(gemini_output)
            elif isinstance(gemini_output, str):
                st.error(f"Gemini Parsing Failure")
                st.code(gemini_output) 
            else:
                st.code(str(gemini_output))
            # -----------------------------------------------------------
            
            st.subheader("Spotify Search Summary")
            st.markdown(f"**Successful Query**: `{st.session_state['debug_info'].get('spotify_query', 'N/A')}`")
            st.markdown(f"**Tracks Returned**: **{st.session_state['debug_info'].get('tracks_returned', 0)}**")
            st.markdown(f"**Attempt Used**: {st.session_state['debug_info'].get('successful_attempt', 'N/A')}")
            
            st.subheader("Raw Gemini CLI Output")
            st.code(st.session_state['debug_info'].get('gemini_raw', 'N/A'))
            
        # --- NEW CALL: Display Export Buttons ---
        display_export_buttons(final_tracks, book_title)
        st.markdown("---")
        # ----------------------------------------

        # --- REST OF YOUR DISPLAY LOGIC ---
        display_embedded_tracks(final_tracks)
        
    else:
        st.error("Please ensure all fields are filled.")