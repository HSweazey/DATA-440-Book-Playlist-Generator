import os
import json
from clients import GeminiClient
from KEYS import GEMINI_API_KEY

os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

LINE_BREAK = '-' * 50 + '\n'

def generate_playlist_input():
    print("\n📚 Gemini Playlist Keyword Generation 📚")

    book = input("Enter the book title: ")
    author = input("Enter the author: ")
    total_pages_input = input("Enter total number of pages (optional, press enter if unknown): ")

    total_pages = int(total_pages_input) if total_pages_input.strip() else 0

    # --- UPDATED PROMPT: Requesting 3 pure mood/style keywords ---
    prompt = f"""
    Analyze the book "{book}"{f" by {author}" if author else ""}.

    Your response must be a single Python dictionary with two keys:
    1. 'mood_keywords': A list of exactly three unique, lowercase, descriptive mood and style keywords that capture the story's tone and atmosphere. These keywords will be used to search for instrumental ambient music.
    2. 'score_query': (OPTIONAL) If the book has a well-known movie or TV adaptation, include this key with the official name of the instrumental score or soundtrack album (e.g., 'Dune Soundtrack 2021' or 'The Lord of the Rings: The Two Towers Score'). If NO adaptation exists, omit this key entirely.

    Respond **ONLY as a single-line Python dictionary** without any extra characters or words.
    
    Example (With Score): {{'mood_keywords': ['heroic', 'epic', 'grand'], 'score_query': 'Dune Soundtrack 2021'}}
    """
    # --- End Prompt ---

    client = GeminiClient()
    client.set_request(prompt)
    client.send_request()
    result = client.get_result()

    # --- Robust parsing ---
    text_output = "[]"

    # 1 Try candidates first
    try:
        candidates = result.get("candidates", [])
        if candidates:
            text_output = candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass

    # 2 Fallback to top-level 'response' key if candidates is empty
    if text_output == "[]" and "response" in result:
        text_output = str(result["response"]).strip()

    # 3 Ensure text_output is a proper stringified list
    if not text_output.startswith('['):
        text_output = f"[{text_output}]"

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