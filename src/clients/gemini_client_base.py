from abc import ABC, abstractmethod

class GeminiClientBase(ABC):

    @abstractmethod
    def set_request(self, prompt: str):
        pass

    @abstractmethod
    def send_request(self):
        pass

    @abstractmethod
    def get_result(self):
        pass
