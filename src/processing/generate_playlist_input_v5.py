import os
from gemini_loader import load_gemini_client

LINE_BREAK = '-' * 50 + '\n'

def generate_playlist_input():
    print("\n📚 Gemini Playlist Keyword Generation 📚")

    # ------------ USER INPUT ------------
    book = input("Enter the book title: ")
    author = input("Enter the author: ")
    total_pages_input = input("Enter total number of pages (optional, press enter if unknown): ")

    total_pages = int(total_pages_input) if total_pages_input.strip() else 0

    # ------------ GEMINI REQUEST PROMPT ------------
    prompt = f"""
    Analyze the book "{book}"{f" by {author}" if author else ""}.

    Your response must be a single Python dictionary with two keys:
    1. 'mood_keywords': A list of exactly three unique, lowercase, descriptive mood and style keywords that capture the story's tone and atmosphere. These keywords will be used to search for instrumental ambient music.
    2. 'score_query': (OPTIONAL) If the book has a well-known movie or TV adaptation, include this key with the official name of the instrumental score or soundtrack album (e.g., 'Dune Soundtrack 2021' or 'The Lord of the Rings: The Two Towers Score'). If NO adaptation exists, omit this key entirely.

    Respond **ONLY as a single-line Python dictionary** without any extra characters or words.
    
    Example (With Score): {{'mood_keywords': ['heroic', 'epic', 'grand'], 'score_query': 'Dune Soundtrack 2021'}}
    """

    # ------------ LOAD CLIENT (REAL OR DUMMY) ------------
    client = load_gemini_client()  # Handles real vs dummy internally

    # --- Set prompt and send request ---
    try:
        client.set_request(prompt)
    except AttributeError:
        # Some real clients may not have set_request; store prompt in .prompt
        client.prompt = prompt

    client.send_request()

    # ------------ GET RESULT ------------
    try:
        result = client.get_result()
    except AttributeError:
        # fallback for real client if get_result does not exist
        result = {"response": None}

    # ------------ ROBUST PARSING ------------
    text_output = "{}"  # default empty dict string

    # 1. Preferred path: Gemini "candidates" field
    try:
        candidates = result.get("candidates", [])
        if candidates:
            text_output = candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass

    # 2. Fallback: top-level "response" key (dummy mode)
    if (text_output == "{}" or not text_output) and "response" in result and result["response"]:
        text_output = str(result["response"]).strip()

    # 3. If the result is a list (like your dummy JSON), wrap it in a dict
    try:
        parsed = eval(text_output)
        if isinstance(parsed, list):
            # wrap list in a dictionary with proper key
            text_output = str({'mood_keywords': parsed})
    except Exception:
        # leave as-is if eval fails
        pass

    # 4. Ensure text_output is a string representing a dict
    if isinstance(text_output, dict):
        text_output = str(text_output)
    elif not text_output.startswith("{"):
        text_output = f"{{{text_output}}}"

    # ------------ OUTPUT ------------
    print(LINE_BREAK)
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
