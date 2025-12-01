import json
import os
from .gemini_client_base import GeminiClientBase

DUMMY_DATA_PATH = "src/processing/keys/dummy_gemini.json"

class GeminiClientDummy(GeminiClientBase):
    def __init__(self):
        print("Using DUMMY Gemini client")
        self.prompt = None
        self.response_data = None

    def set_request(self, prompt: str):
        self.prompt = prompt  # not used, but needed for symmetry

    def send_request(self):
        try:
            with open(DUMMY_DATA_PATH, "r") as f:
                self.response_data = json.load(f)
        except Exception as e:
            print(f"Warning loading dummy file: {e}")
            self.response_data = {"response": "['ambient', 'cinematic', 'ethereal']"}

    def get_result(self):
        return self.response_data
