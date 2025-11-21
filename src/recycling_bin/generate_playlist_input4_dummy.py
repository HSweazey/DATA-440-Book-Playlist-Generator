import os
from clients.gemini_loader import load_gemini_client

LINE_BREAK = '-' * 50 + '\n'

def generate_playlist_input():
    print("\n📚 Yay Playlist Keyword Generation 📚")

    # ------------ USER INPUT ------------
    book = input("Enter the book title: ")
    author = input("Enter the author: ")
    total_pages_input = input("Enter total number of pages (optional, press enter if unknown): ")

    total_pages = int(total_pages_input) if total_pages_input.strip() else 0

    # ------------ GEMINI REQUEST PROMPT ------------
    prompt = f"""
    Analyze the book "{book}"{f" by {author}" if author else ""}.
    Your response must contain **only** a single Python list of **exactly three** lowercase keywords 
    that capture the story's tone and mood.

    The first keyword **must** be a valid Spotify genre.
    The second and third keywords **must** relate to broader instrumental styles of music.

    Respond **ONLY** as a single-line Python list without any extra characters or explanation.
    
    Example Output: ['pop', 'ambient', 'lofi']
    """

    # ------------ LOAD CLIENT (REAL OR DUMMY) ------------
    client = load_gemini_client()
    client.set_request(prompt)
    client.send_request()

    # CORRECT METHOD — use get_result()
    result = client.get_result()

    # ------------ ROBUST PARSING ------------
    text_output = "[]"

    # 1. Preferred path: Gemini "candidates" field
    try:
        candidates = result.get("candidates", [])
        if candidates:
            text_output = candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass

    # 2. Fallback: top-level "response" (dummy mode)
    if text_output == "[]" and "response" in result:
        text_output = str(result["response"]).strip()

    # 3. Ensure valid Python list syntax
    if not text_output.startswith("["):
        text_output = f"[{text_output}]"

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
