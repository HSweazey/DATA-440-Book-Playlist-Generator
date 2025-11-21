# generate_playlist_input.py (MODIFIED)
import os
import ast 
# Assuming src.clients.gemini_loader and spotipy are accessible
# from src.clients.gemini_loader import load_gemini_client 

LINE_BREAK = '-' * 50 + '\n'

def generate_playlist_input(book=None, author=None, total_pages=0, suppress_input=False):
    """
    Handles user input (CLI or UI) and calls the Gemini client.
    
    If suppress_input is True, it uses the provided arguments instead of
    reading from the terminal.
    """
    print("\n📚 Gemini Playlist Keyword Generation 📚") # Retained for optional CLI status

    # ------------ USER INPUT (Conditional based on suppress_input) ------------
    if not suppress_input:
        book = input("Enter the book title: ")
        author = input("Enter the author: ")
        total_pages_input = input("Enter total number of pages (optional, press enter if unknown): ")
        total_pages = int(total_pages_input) if total_pages_input.strip() else 0
        print(LINE_BREAK)

    if not book:
        # Raise error only if no book title is provided, regardless of input source
        raise ValueError("Book title is required for generation.")

    # ------------ GEMINI REQUEST PROMPT ------------
    prompt = f"""
    Analyze the book "{book}"{f" by {author}" if author else ""}.

    Your response must be a single Python dictionary with two keys:
    1. 'mood_keywords': A list of exactly three unique, lowercase, descriptive mood and style keywords that capture the story's tone and atmosphere. These keywords will be used to search for instrumental ambient music.
    2. 'score_query': (OPTIONAL) If the book has a well-known movie or TV adaptation, include this key with the official name of the instrumental score or soundtrack album (e.g., 'Dune Soundtrack 2021' or 'The Lord of the Rings: The Two Towers Score'). If NO adaptation exists, omit this key entirely.

    Respond **ONLY as a single-line Python dictionary** without any extra characters or words.
    
    Example (With Score): {{'mood_keywords': ['heroic', 'epic', 'grand'], 'score_query': 'Dune Soundtrack 2021'}}
    """

    # ------------ LOAD CLIENT (Assumed Placeholder for External Tool) ------------
    # In a real environment: client = load_gemini_client() 
    # For this demonstration, we assume client has a prompt/send/get mechanism.
    
    # --- Set prompt and send request (Simulated) ---
    # client.set_request(prompt) 
    # client.send_request()

    # --- GET RESULT (Simulated placeholder for actual API call) ---
    # result = client.get_result()
    # For testing, we can simulate a successful return:
    result = {"response": "{'mood_keywords': ['pensive', 'cozy', 'melancholic']}"} 


    # ------------ ROBUST PARSING ------------
    text_output = "{}" 

    try:
        candidates = result.get("candidates", [])
        if candidates:
            text_output = candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass

    if (text_output == "{}" or not text_output) and "response" in result and result["response"]:
        text_output = str(result["response"]).strip()

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

    # ------------ OUTPUT ------------
    if not suppress_input: 
        print(f"🎧 Playlist input generated for '{book}':\n")
        print(text_output)
        print(LINE_BREAK)

    return {
        "response": text_output,
        "book": book,
        "author": author,
        "total_pages": total_pages
    }

if __name__ == "__main__":
    generate_playlist_input()