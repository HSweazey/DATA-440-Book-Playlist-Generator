import os
import ast 
import streamlit as st # Added for debugging output
from src.clients.gemini_loader import load_gemini_client 

LINE_BREAK = '-' * 50 + '\n'

def generate_playlist_input(book=None, author=None, total_pages=0, suppress_input=False):
    """
    Handles user input and calls the Gemini client, printing debug info to UI on error.
    """
    if not book: raise ValueError("Book title is required for generation.")

    prompt = f"""
    Analyze the book "{book}"{f" by {author}" if author else ""}.

    Your response must be a single Python dictionary with the following keys:
    1. 'mood_keywords': A list of exactly five unique, lowercase, descriptive mood and style keywords that capture the story's tone and atmosphere. These keywords will be used to search for instrumental ambient music.
    2. 'score_query': (OPTIONAL) If the book has a well-known movie or TV adaptation, include this key with the official name of the instrumental score or soundtrack album. If NO adaptation exists, omit this key entirely.
    3. 'composer_name': (CONDITIONAL) If you include 'score_query', you **must** include this key with the primary composer's full name (e.g., 'Hans Zimmer', 'Max Richter'). Omit this key if 'score_query' is omitted.

    Respond **ONLY as a single-line Python dictionary** without any extra characters or words.
    
    Example (With Score): {{'mood_keywords': ['heroic', 'epic', 'grand', 'cinematic', 'intense'], 'score_query': 'Dune Soundtrack 2021', 'composer_name': 'Hans Zimmer'}}
    """
    
    # --- Client Loading ---
    try:
        client = load_gemini_client() 
        client.prompt = prompt # Set the prompt regardless of the attribute name
    except Exception as e:
        st.error(f"❌ Gemini Load Error: Failed to instantiate client. Check dependencies. Details: {e}")
        return {}

    # --- Debug Marker A ---
    st.toast("DEBUG: Attempting to send request to Gemini CLI...", icon='⚙️')
    # --- End Debug Marker A ---

    # --- Send Request ---
    try:
        # ... client setup ...
        client.send_request() # <--- THIS LINE IS LIKELY THE BLOCKING POINT
    except Exception as e:
        # ... error handling ...
        return {}

    # --- Debug Marker B ---
    st.toast("DEBUG: Successfully received response from Gemini CLI.", icon='✅')
    # --- End Debug Marker B ---

    # --- Get Result ---
    try:
        result = client.get_result()
    except Exception:
        result = {"response": None}

    # --- Robust Parsing ---
    text_output = "{}" 
    try:
        candidates = result.get("candidates", [])
        if candidates:
            text_output = candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass
    
    if (text_output == "{}" or not text_output) and "response" in result:
        text_output = str(result.get("response", "")).strip()

    try:
        parsed = ast.literal_eval(text_output)
        if isinstance(parsed, list):
            text_output = str({'mood_keywords': parsed})
    except Exception:
        pass

    if isinstance(text_output, dict):
        text_output = str(text_output)
    elif not text_output.startswith("{"):
        text_output = f"{{{text_output}}}"

    if not suppress_input: 
        print(f"🎧 Playlist input generated for '{book}':\n")
        print(text_output)
        print(LINE_BREAK)

    # --- DEBUG CAPTURE: Store Gemini Output ---
    st.session_state['debug_info']['gemini_raw'] = text_output
    
    try:
        # Use literal_eval to safely parse the output dictionary
        parsed_dict = ast.literal_eval(text_output)
        
        # Format the mood keywords for easy reading
        moods = parsed_dict.get('mood_keywords', 'N/A')
        score = parsed_dict.get('score_query', 'N/A')
        
        st.session_state['debug_info']['gemini_parsed'] = {
            "Mood Keywords": ", ".join(moods) if isinstance(moods, list) else moods,
            "Score Query": score
        }
    except Exception:
        st.session_state['debug_info']['gemini_parsed'] = "Error: Failed to parse output into a dictionary."
    # --- END DEBUG CAPTURE ---
    
    # ... (remaining return statement) ...
    return {
        "response": text_output,
        "book": book,
        "author": author,
        "total_pages": total_pages
    }

if __name__ == "__main__":
    generate_playlist_input()