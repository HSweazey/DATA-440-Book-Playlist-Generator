import subprocess
import json
from gemini_client_base import GeminiClientBase

class GeminiClientReal(GeminiClientBase):
    def __init__(self, api_key: str, model = "gemini-2.0-flash-exp"):
        self.api_key = api_key
        self.model = model
        self.raw_output = None

    def send_request(self, prompt: str):
        cmd = [
            "gemini", "run", self.model,
            "--prompt", prompt,
            "--api-key", self.api_key
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        self.raw_output = result.stdout

    def get_response(self):
        if not self.raw_output:
            return None

        parsed = json.loads(self.raw_output)
        try:
            # navigate Gemini structure:
            text = (
                parsed["candidates"][0]["content"]["parts"][0]["text"]
            )
            return text
        except:
            return None
