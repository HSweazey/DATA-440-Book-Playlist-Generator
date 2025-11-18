# src/clients/gemini_loader.py
import os
import json
from .gemini_client_real import GeminiClientReal
from .gemini_client_dummy import GeminiClientDummy

# Path to JSON file containing real Gemini API key
KEY_FILE = os.path.join(os.path.dirname(__file__), "keys", "gemini_key.json")


def load_real_key():
    """Load real Gemini API key from JSON file."""
    print(f"Looking for key file at: {KEY_FILE}")
    if not os.path.exists(KEY_FILE):
        print("Key file not found.")
        return None

    try:
        with open(KEY_FILE, "r") as f:
            data = json.load(f)
            api_key = data.get("api_key")
            if api_key and api_key.strip():
                print("Loaded key from JSON: FOUND")
                return api_key
            else:
                print("Loaded key from JSON: EMPTY or INVALID")
                return None
    except Exception as e:
        print(f"Error reading key file: {e}")
        return None


def load_gemini_client():
    """
    Load the real Gemini client if a valid key exists.
    Otherwise, fall back to the dummy client.
    """
    api_key = load_real_key()

    if api_key:
        print("🔑 Using REAL Gemini API key from gemini_key.json")
        return GeminiClientReal(api_key=api_key)

    print("⚠️ No real key found — using DUMMY Gemini client")
    client = GeminiClientDummy()

    # Ensure dummy get_result always returns a dict
    original_get_result = client.get_result

    def get_result_dict():
        res = original_get_result()
        if isinstance(res, dict):
            return res

        try:
            parsed = eval(res)
            if isinstance(parsed, list):
                return {"mood_keywords": parsed}
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        return {}

    client.get_result = get_result_dict
    return client
