import json
from gemini_client_base import GeminiClientBase

class GeminiClientDummy(GeminiClientBase):
    def __init__(self, json_path = "dummy_gemini.json"):
        with open(json_path, "r") as f:
            self.data = json.load(f)

    def send_request(self, prompt: str):
        # do nothing; dummy response already loaded
        pass

    def get_response(self):
        return self.data.get("response", None)