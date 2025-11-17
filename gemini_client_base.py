from abc import ABC, abstractmethod

class GeminiClientBase(ABC):
    @abstractmethod
    def send_request(self, prompt: str):
        pass

    @abstractmethod
    def get_response(self):
        pass