import os
import json
from clients import GeminiClient

GEMINI_API_KEY = "AIzaSyA1M372by3Ha6hlOZRmSygZmtlU3q2nyxI"
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

LINE_BREAK = '-' * 50 + '\n'

def generate_playlist_input():
    print("\n📚 Yay Playlist Keyword Generation 📚")

    book = input("Enter the book title: ")
    author = input("Enter the author (optional): ")
    current_page_input = input("Enter your current page (optional, press enter for 0): ")
    total_pages_input = input("Enter total number of pages (optional, press enter if unknown): ")

    current_page = int(current_page_input) if current_page_input.strip() else 0
    total_pages = int(total_pages_input) if total_pages_input.strip() else 0

    prompt = f"""
    Given the book "{book}"{f" by {author}" if author else ""},
    provide exactly four descriptive keywords that best capture the atmosphere 
    or mood of songs that would match the story's tone.
    Respond ONLY as a Python list of four lowercase words, comma-separated.
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
        "current_page": current_page,
        "total_pages": total_pages
    }

if __name__ == "__main__":
    generate_playlist_input()
