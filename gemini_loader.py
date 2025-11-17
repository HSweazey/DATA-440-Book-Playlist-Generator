import os
from dotenv import load_dotenv
from gemini_client_real import GeminiClientReal
from gemini_client_dummy import GeminiClientDummy

def load_gemini_client():
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY", None)

    if key in (None, "", "DUMMY", "dummy", "test"):
        return GeminiClientDummy()

    return GeminiClientReal(api_key=key)
