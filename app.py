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
        st.warning("No tracks were generated.")
        return

    # 1. Split the tracks into "Featured" (Embeds) and "Remaining" (List)
    EMBED_LIMIT = 6 
    featured_tracks = tracks[:EMBED_LIMIT]
    remaining_tracks = tracks[EMBED_LIMIT:]

    # ---------------------------------------------------------
    # SECTION 1: PLAYLIST PREVIEW (Embedded Players)
    # ---------------------------------------------------------
    st.subheader(f"🎧 Playlist Preview (Top {len(featured_tracks)})")
    st.markdown("---")
    
    cols_featured = st.columns(2)
    
    for i, track in enumerate(featured_tracks):
        track_id = extract_spotify_track_id(track.get('spotify_url', ''))
        
        with cols_featured[i % 2]:
            if track_id:
                embed_url = f"https://open.spotify.com/embed/track/{track_id}?utm_source=generator"
                embed_html = f"""
                <iframe src="{embed_url}" width="100%" height="80" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>
                """
                st.components.v1.html(embed_html, height=100)
            else:
                st.error(f"Could not embed: {track.get('track_name')}")

    # ---------------------------------------------------------
    # SECTION 2: FULL TRACK LIST (Clickable Cards)
    # ---------------------------------------------------------
    if remaining_tracks:
        st.markdown("<br>", unsafe_allow_html=True) # Add a little vertical spacer
        st.subheader(f"📋 Full Track List ({len(remaining_tracks)} more)")
        st.markdown("---")

        cols_list = st.columns(2)
        
        for i, track in enumerate(remaining_tracks):
            track_name = track.get('track_name', 'Unknown Title')
            artist_name = track.get('artist_name', 'Unknown Artist')
            spotify_url = track.get('spotify_url', '#')
            
            # Use HTML to make a clean, clickable card
            card_html = f"""
            <div style="
                background-color: #2c2c44; 
                padding: 12px; 
                border-radius: 10px; 
                margin-bottom: 12px; 
                border: 1px solid #4a4a6e;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: 0.3s;">
                <div style="overflow: hidden; white-space: nowrap; text-overflow: ellipsis; padding-right: 10px;">
                    <strong style="color: #f0f0f0;">{track_name}</strong><br>
                    <span style="color: #bbb; font-size: 0.85em;">{artist_name}</span>
                </div>
                <a href="{spotify_url}" target="_blank" style="
                    background-color: #f7b731;
                    color: #1a1a2e;
                    padding: 6px 12px;
                    text-decoration: none;
                    font-size: 0.8em;
                    font-weight: bold;
                    border-radius: 15px;
                    white-space: nowrap;">
                    Play ↗
                </a>
            </div>
            """
            
            with cols_list[i % 2]:
                st.markdown(card_html, unsafe_allow_html=True)

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
        with st.expander("🛠️ Debug Information (Pipeline Metrics)"):
            
            # Retrieve data from session state
            debug_info = st.session_state.get('debug_info', {})
            target_metrics = debug_info.get('target_metrics', {})
            
            st.subheader("⏱️ Read Time & Target Metrics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Target Read Time", f"{target_metrics.get('target_read_time_min', '0')} min")
            with col2:
                st.metric("Target Track Count", target_metrics.get('num_tracks_target', '0'))
            
            st.markdown("---")
            st.subheader("🧠 Gemini Output")
            gemini_output = debug_info.get('gemini_parsed', {'status': 'Error: Not available'})
            
            if isinstance(gemini_output, dict):
                st.json(gemini_output)
            elif isinstance(gemini_output, str):
                st.error(f"Gemini Parsing Failure")
                st.code(gemini_output) 
            else:
                st.code(str(gemini_output))

            st.markdown("---")
            st.subheader("🎵 Track Generation Log")
            
            # --- NEW: DISPLAY THE GRANULAR LOG ---
            search_log = debug_info.get('search_log', [])
            if search_log:
                st.dataframe(
                    pd.DataFrame(search_log),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Source": st.column_config.TextColumn("Source (Method: Keyword)"),
                        "Tracks Added": st.column_config.NumberColumn("Tracks Found"),
                        "Query": st.column_config.TextColumn("Spotify Query Used"),
                    }
                )
            else:
                st.info("No search logs available.")

            st.caption(f"Final Playlist Length: {debug_info.get('post_adjustment_length', 0)} tracks")
            
        # --- NEW CALL: Display Export Buttons ---
        display_export_buttons(final_tracks, book_title)
        st.markdown("---")
        # ----------------------------------------

        # --- REST OF YOUR DISPLAY LOGIC ---
        display_embedded_tracks(final_tracks)
        
    else:
        st.error("Please ensure all fields are filled.")