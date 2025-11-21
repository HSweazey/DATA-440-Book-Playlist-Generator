import os
from src.clients.gemini_loader import load_gemini_client

LINE_BREAK = '-' * 50 + '\n'

def generate_genre_keywords(target_genre: str):
    print(f"\n📚 Gemini Keyword Generation for Genre: {target_genre}📚")


    # ------------ GEMINI REQUEST PROMPT ------------
    prompt = f"""
    Analyze the broad genre of '{target_genre}' and its typical mood, tone, and atmosphere.
    Your task is to generate three unique, lowercase, descriptive mood and style keywords suitable for instrumental ambient music that would capture the essence of this genre.
    Respond **ONLY as a single-line Python DICTIONARY** containing exactly one key: 'keywords', whose value is a list of exactly three strings.

    Example Output for 'Fantasy': {{'keywords': ['epic', 'cinematic', 'medieval']}}
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
    print(f"🎧 Playlist input generated for '{target_genre}':\n")
    print(text_output)
    print(LINE_BREAK)

    return text_output

#if __name__ == "__main__":
# generate_genre_keywords()