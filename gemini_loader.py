import os
from gemini_client_real import GeminiClientReal
from gemini_client_dummy import GeminiClientDummy

def load_gemini_client():
    key = os.getenv("GEMINI_API_KEY", None)

    if key in (None, "", "DUMMY", "dummy", "test"):
        print("Using DUMMY Gemini client")
        return GeminiClientDummy()
    
    print("Using REAL Gemini client")
    return GeminiClientReal(api_key = key)
