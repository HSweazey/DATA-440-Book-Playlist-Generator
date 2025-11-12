import os
import json
from clients import GeminiClient

# -------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------
# Real key (if you have one) — or dummy key for testing.
# Replace this with a real one temporarily when verifying locally.
GEMINI_API_KEY = "AIzaSyA1M372by3Ha6hlOZRmSygZmtlU3q2nyxI"

# Inject into environment for subprocess calls.
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

LINE_BREAK = '-' * 50 + '\n'


def generate_playlist_input():
    print("\n📚 Gemini Playlist Keyword Generator 📚")

    book = input("Enter the book title: ")
    author = input("Enter the author (optional): ")

    prompt = f"""
    Given the book "{book}"{f" by {author}" if author else ""},
    provide exactly four descriptive keywords that best capture the atmosphere 
    or mood of songs that would match the story's tone.
    Respond ONLY as a Python list of four lowercase words, comma-separated.
    """

    client = GeminiClient()
    client.set_request(prompt)
    client.send_request()

    # Parse result
    result = client.get_result()

    # Try to extract text safely
    try:
        # Most Gemini CLI JSONs have this structure:
        # {"candidates": [{"content": {"parts": [{"text": "..."}]}}]}
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

    return text_output


if __name__ == "__main__":
    generate_playlist_input()
