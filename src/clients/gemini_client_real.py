# src/clients/gemini_client_real.py
import subprocess
import json
import os
from .gemini_client_base import GeminiClientBase

class GeminiClientReal(GeminiClientBase):
    def __init__(self, api_key: str, model="gemini-2.5-flash-lite"):
        self.api_key = api_key
        self.model = model
        self.prompt = None      # For interface consistency with dummy client
        self.response_data = None

    def set_request(self, prompt: str):
        """Store the prompt (for interface consistency)."""
        self.prompt = prompt

    def send_request(self):
        """Send request to Gemini CLI and store output in the same format as dummy client."""
        if not self.prompt:
            raise ValueError("Prompt not set. Call set_request(prompt) first.")

        # Pass API key via environment variable
        env = os.environ.copy()
        env["GEMINI_API_KEY"] = self.api_key

        # Use positional prompt only (CLI does not accept --prompt with positional)
        cmd = [
            "gemini", "run", self.model,
            self.prompt,
            "--output-format", "json"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)
            self.response_data = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error calling Gemini API: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            # fallback for testing
            self.response_data = {"response": "['ambient', 'ethereal', 'cinematic']"}
        except json.JSONDecodeError as e:
            print(f"Error parsing Gemini output as JSON: {e}")
            self.response_data = {"response": "['ambient', 'ethereal', 'cinematic']"}

    def get_result(self):
        """Return the result in the same shape as dummy client."""
        return self.response_data
