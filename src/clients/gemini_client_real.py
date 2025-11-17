# gemini_client_real.py
import subprocess
import json
from .gemini_client_base import GeminiClientBase

class GeminiClientReal(GeminiClientBase):
    def __init__(self, api_key: str, model="gemini-2.5-flash-lite"):
        self.api_key = api_key
        self.model = model
        self.prompt = None      # For interface consistency with dummy client
        self.response_data = None

    def set_request(self, prompt: str):
        """Store the prompt (not actually required for real client, just for interface)."""
        self.prompt = prompt

    def send_request(self):
        """Send request to Gemini model and store output in a dict similar to dummy client."""
        if not self.prompt:
            raise ValueError("Prompt not set. Call set_request(prompt) first.")

        cmd = [
            "gemini", "run", self.model,
            "--prompt", self.prompt,
            "--output-format", "json",
            "--api-key", self.api_key
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            parsed = json.loads(result.stdout)
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            parsed = {"response": "['ambient', 'ethereal', 'cinematic']"}  # fallback

        # Store result in same format as dummy client
        self.response_data = parsed

    def get_result(self):
        """Return result in the same shape as dummy client."""
        return self.response_data
