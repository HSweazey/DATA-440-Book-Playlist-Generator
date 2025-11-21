import streamlit as st
import pandas as pd
import re
import time
from src.processing.generate_playlist_csv_app import get_final_tracks # Assuming this is the correct path

# --- 0. UI CUSTOMIZATION: Dark Mode & Cozy Aesthetic ---
# We are changing the Streamlit base theme to 'dark' and then 
# using custom CSS to refine the colors for a lo-fi/cozy look.

st.set_page_config(
    page_title="🎧 Cozy Reads Playlist Generator", 
    layout="centered",
    initial_sidebar_state="collapsed"
    # Set Streamlit's built-in theme to 'dark' for the best base
    # NOTE: This setting is typically best done in a .streamlit/config.toml file, 
    # but we force the style here for immediate change.
)

custom_css = """
<style>
/* 1. Base Dark Mode Background & Text */
[data-testid="stAppViewContainer"] {
    background-color: #1a1a2e; /* Deep dark purple/blue */
    color: #e0e0e0; /* Light gray for main text */
}

/* 2. Primary Color (Soft Warm Gold/Cream for accents) */
.stButton>button {
    background-color: #f7b731; /* Soft Gold/Amber */
    color: #1a1a2e; /* Dark text on button for contrast */
    border-radius: 12px;
    border: 1px solid #d39c28;
    transition: all 0.2s ease-in-out;
    font-weight: bold;
}
.stButton>button:hover {
    background-color: #ffc84d; 
    border: 1px solid #ffc84d;
}

/* 3. Input Field Styling */
.stTextInput>div>div>input, .stNumberInput>div>div>input {
    background-color: #2c2c44; /* Slightly lighter dark background for input boxes */
    color: #f0f0f0;
    border-radius: 8px;
    border: 1px solid #4a4a6e;
    padding: 10px;
}

/* 4. Rounded Containers (Input Form) */
[data-testid="stForm"] {
    background-color: #202035; /* Dark container background */
    border-radius: 15px; 
    padding: 20px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5); /* Stronger shadow for depth */
    border: 1px solid #3a3a50;
}

/* 5. Header Styling */
h1, h2, h3 {
    color: #f7b731; /* Use the soft gold for headings */
}

/* 6. Info/Success Boxes (Better contrast) */
.stAlert {
    background-color: #35354e !important;
    border-radius: 8px;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
# You may need to also set the Streamlit configuration file (.streamlit/config.toml) 
# to achieve the full dark mode effect perfectly across all elements.

# ----------------------------------------------------------------------------------
# --- 1. CORE LOGIC WRAPPER (Integration with your refactored code) ---
# ----------------------------------------------------------------------------------

def extract_spotify_track_id(spotify_url: str) -> str | None:
    """Extracts the Track ID from a full Spotify track URL."""
    match = re.search(r'track/([^?]+)', spotify_url)
    if match:
        return match.group(1)
    return None

def display_embedded_tracks(tracks: list):
    """Renders the list of tracks as embedded Spotify tiles."""
    if not tracks:
        st.warning("No tracks were generated for the playlist. Please check the logs.")
        return

    st.subheader(f"🎶 Your Cozy Reading Playlist ({len(tracks)} Tracks)")
    st.markdown("---")
    
    # Use st.columns for a multi-tile display (e.g., 2 tiles wide)
    cols = st.columns(2)
    
    for i, track in enumerate(tracks):
        track_id = extract_spotify_track_id(track.get('spotify_url', ''))
        
        if track_id:
            # Spotify Embed URL structure (uses placeholder 4 from previous instructions)
            embed_url = f"https://open.spotify.com/embed/track/{track_id}"
            
            embed_html = f"""
            <iframe 
                src="{embed_url}" 
                width="100%" 
                height="100" 
                frameborder="0" 
                allowtransparency="true" 
                allow="encrypted-media"
                style="border-radius: 10px;"
            ></iframe>
            """
            
            # Display the tile in a column
            with cols[i % 2]: # Cycle between column 0 and 1
                st.components.v1.html(embed_html, height=110)
        else:
            # Fallback for tracks without a valid ID
            with cols[i % 2]:
                 st.markdown(f"**{track.get('track_name', 'Unknown Track')}** - {track.get('artist_name', 'Unknown Artist')} (URL error)")


def generate_playlist_ui_wrapper(book_title, author_name, page_count):
    """
    Connects Streamlit inputs to your backend logic.
    """
    
    # Display loading message in the UI
    with st.spinner(f"Generating Playlist..."):
        try:
            # CALL TO YOUR REFRACTORED CODE
            final_tracks = get_final_tracks(book_title, author_name, page_count)
            
            return final_tracks
            
        except Exception as e:
            # We catch the error and display it directly in the UI for clarity
            st.error(f"❌ An error occurred during generation: {e}")
            st.warning("Please check your Spotify credentials, API keys, and network connection.")
            return [] 

# ----------------------------------------------------------------------------------
# --- 2. MAIN STREAMLIT LAYOUT ---
# ----------------------------------------------------------------------------------

st.title("📚 Cozy Reads Soundtrack Creator")
st.markdown("A personalized reading playlist powered by AI and Spotify.")

# Input Form: Use st.form for the clean, contained, rounded box
with st.form("playlist_input_form"):
    st.subheader("Book Details")
    
    # Input for Book Title
    book_title = st.text_input(
        "Book Title", 
        placeholder="e.g., 'The Midnight Library'",
    )
    
    # Input for Author Name
    author_name = st.text_input(
        "Author Name", 
        placeholder="e.g., Matt Haig",
    )
    
    # Input for Page Count (Your clarified third input)
    page_count = st.number_input(
        "Total Page Count", 
        min_value=1, 
        max_value=5000, 
        value=300, 
        help="Used to estimate the required playlist length (approx. 2 min/page)."
    )
    
    # Generate Button
    submitted = st.form_submit_button("Generate My Cozy Playlist ✨")

# Output Section
if submitted:
    if book_title and author_name and page_count > 0:
        
        # 1. Call the wrapper function to generate the playlist
        final_tracks = generate_playlist_ui_wrapper(book_title, author_name, page_count)
        
        # 2. Display the embedded tiles
        display_embedded_tracks(final_tracks)
        
    else:
        st.error("Please ensure the Book Title, Author Name, and Page Count are all entered.")