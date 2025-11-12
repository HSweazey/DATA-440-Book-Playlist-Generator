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

# -------------------------------------------------------
# TEST PROMPT
# -------------------------------------------------------
prompt_text = "List three genres similar to fantasy books."

# -------------------------------------------------------
# RUN TEST
# -------------------------------------------------------
try:
    client = GeminiClient(model=GeminiClient.Models.LITE)
    client.set_request(prompt_text)
    client.send_request()
    result = client.get_result()

    print("✅ Gemini client ran successfully!")
    print(json.dumps(result, indent=2))

except Exception as e:
    print("❌ Error during Gemini client test:")
    print(str(e))
