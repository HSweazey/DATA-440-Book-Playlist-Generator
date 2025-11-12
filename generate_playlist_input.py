import os
import json
from clients import GeminiClient

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------
# Real key (if you have one) — or dummy key for testing.
GEMINI_API_KEY = "AIzaSyA1M372by3Ha6hlOZRmSygZmtlU3q2nyxI"

# Inject into environment for subprocess calls.
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

LINE_BREAK = '-' * 50 + '\n'


def generate_playlist_input():
    print("\n📚 Gemini Playlist Keyword Generator 📚")

    # Collect all input at once
    book = input("Enter the book title: ")
    author = input("Enter the author (optional): ")
    current_page_input = input("Enter your current page (optional, press enter for 0): ")
    total_pages_input = input("Enter total number of pages (optional, press enter if unknown): ")

    # Convert page inputs to integers or use defaults
    current_page = int(current_page_input) if current_page_input.strip() else 0
    total_pages = int(total_pages_input) if total_pages_input.strip() else 0

    # Build Gemini prompt
    prompt = f"""
    Given the book "{book}"{f" by {author}" if author else ""},
    please provide a Python list of exactly four descriptive lowercase keywords 
    that capture the atmosphere or mood of songs matching the story's tone. 
    Respond ONLY with the list, no extra text or explanation.
    """

    # Call Gemini
    client = GeminiClient()
    client.set_request(prompt)
    client.send_request()

    # Parse result
    result = client.get_result()

    # Try to extract just the keyword string safely
    try:
        candidates = result.get("candidates", [])
        if candidates:
            keywords_text = candidates[0]["content"]["parts"][0]["text"]
        else:
            keywords_text = "[]"
    except Exception as e:
        keywords_text = "[]"
        print(f"[Error parsing Gemini output] {e}\nRaw result: {json.dumps(result, indent=2)}")

    # Remove leading/trailing whitespace
    keywords_text = keywords_text.strip()

    print(LINE_BREAK)
    print(f"🎧 Playlist input generated for '{book}':\n")
    print(keywords_text)
    print(LINE_BREAK)

    # Return all relevant info in the correct format
    return {
        "keywords": keywords_text,
        "book": book,
        "author": author,
        "current_page": current_page,
        "total_pages": total_pages
    }


if __name__ == "__main__":
    generate_playlist_input()
