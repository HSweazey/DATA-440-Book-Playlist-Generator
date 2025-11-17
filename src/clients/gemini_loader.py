import os
from dotenv import load_dotenv
from .gemini_client_real import GeminiClientReal
from .gemini_client_dummy import GeminiClientDummy
from src.utils.KEYS import * # <-- remove when env working, hardcoded return line

def load_gemini_client():
    """
    Returns a Gemini client (real or dummy) depending on the API key.
    The dummy client will now return Python dictionaries directly for easier parsing.
    """
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY", None)

    if key in (None, "", "DUMMY", "dummy", "test"):
        client = GeminiClientDummy()
        
        # Wrap its get_result to always return a dict
        original_get_result = client.get_result
        def get_result_dict():
            res = original_get_result()
            if isinstance(res, str):
                # Attempt to eval the string safely
                try:
                    parsed = eval(res)
                    if isinstance(parsed, list):
                        # Wrap list in dict with proper key
                        return {'mood_keywords': parsed}
                    elif isinstance(parsed, dict):
                        return parsed
                except Exception:
                    # fallback to default empty dict
                    return {}
            elif isinstance(res, dict):
                return res
            return {}
        client.get_result = get_result_dict
        return client

    return GeminiClientReal(api_key=GEMINI_API_KEY)
