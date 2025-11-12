import os
import json
from clients import GeminiClient

# CONFIGURATION (copy and paste from testing file)
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
    provide exactly four descriptive keywords that best capture the atmosphere 
    or mood of songs that would match the story's tone.
    Respond ONLY as a Python list of four lowercase words, comma-separated.
    """

    # Call Gemini
    client = GeminiClient()
    client.set_request(prompt)
    client.send_request()

    # Parse result
    result = client.get_result()

    # Try to extract text safely
    try:
        candidates = result.get("candidates", [])
        if candidates:
            text_output = candidates[0]["content"]["parts"][0]["text"]
        else:
            text_output = str(result)
    except Exception as e:
        text_output = f"[Error parsing output] {e}\nRaw result: {json.dumps(result, indent=2)}"

    print(LINE_BREAK)
    print(f"🎧 Playlist input generated for '{book}':\n")
    print(text_output)
    print(LINE_BREAK)

    # Return all relevant info as a dictionary
    return {
        "keywords": text_output,
        "book": book,
        "author": author,
        "current_page": current_page,
        "total_pages": total_pages
    }


if __name__ == "__main__":
    generate_playlist_input()
