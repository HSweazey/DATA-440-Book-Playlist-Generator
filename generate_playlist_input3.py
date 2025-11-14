import os
import json
from clients import GeminiClient

GEMINI_API_KEY = "AIzaSyA1M372by3Ha6hlOZRmSygZmtlU3q2nyxI"
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

LINE_BREAK = '-' * 50 + '\n'

def generate_playlist_input():
    print("\n📚 Yay Playlist Keyword Generation 📚")

    book = input("Enter the book title: ")
    author = input("Enter the author: ")
    total_pages_input = input("Enter total number of pages (optional, press enter if unknown): ")

    total_pages = int(total_pages_input) if total_pages_input.strip() else 0
# chosen from this list: acoustic, alternative, ambient, classical, chill, country, dance, electronic, folk, hip-hop, indie-pop, jazz, latin, metal, new-age, pop, r-n-b, rock, sad, sleep, songwriter, study, synth-pop.
    prompt = f"""
    Analyze the book "{book}"{f" by {author}" if author else ""}.
    Your response must contain **only** a single Python list of **exactly three** lowercase, keywords that capture the story's tone and mood.
    The first keyword **must** be a valid Spotify genre.
    The second and third keywords **must** relate to broader instrumental styles of music.
    Respond **ONLY** as a single-line Python list without any extra characters or words. Do not offer any other input or explanation.
    
    Example Output: ['pop', 'ambient', 'lofi']
    """

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
