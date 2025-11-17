import os
import json
from clients import GeminiClient
# NOTE: Removed dependency on KEYS since the API key is defined locally.

GEMINI_API_KEY = "AIzaSyA1M372by3Ha6hlOZRmSygZmtlU3q2nyxI"
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

LINE_BREAK = '-' * 50 + '\n'

def generate_genre_keywords(target_genre: str):
    """
    Prompts Gemini to analyze a given broad genre (e.g., Fantasy) and return 
    three descriptive keywords suitable for instrumental ambient music.
    """
    print(f"\n📚 Gemini Keyword Generation for Genre: {target_genre} 📚")

    # --- UPDATED PROMPT: Analyzing a Genre Input ---
    prompt = f"""
    Analyze the broad genre of '{target_genre}' and its typical mood, tone, and atmosphere.
    Your task is to generate three unique, lowercase, descriptive mood and style keywords suitable for instrumental ambient music that would capture the essence of this genre.
    Respond **ONLY as a single-line Python list** containing exactly three strings, without any extra characters or words.

    Example Output for 'Fantasy': ['epic', 'cinematic', 'medieval']
    """
    # --- End Prompt ---

    client = GeminiClient()
    client.set_request(prompt)
    client.send_request()
    result = client.get_result()

    # --- Robust parsing ---
    text_output = "[]"
    try:
        candidates = result.get("candidates", [])
        if candidates:
            text_output = candidates[0]["content"]["parts"][0]["text"].strip()
    except Exception:
        pass

    if text_output == "[]" and "response" in result:
        text_output = str(result["response"]).strip()

    # Ensure text_output is a proper stringified list
    if not text_output.startswith('['):
        text_output = f"[{text_output}]"

    print(f"Keywords generated: {text_output}")
    print(LINE_BREAK)

    return text_output # Returns the list string of keywords

if __name__ == "__main__":
    # Example standalone run
    generate_genre_keywords("Cyberpunk")