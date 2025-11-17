from abc import ABC, abstractmethod

import json
import shutil
import subprocess
from datetime import datetime as dt

LINE_BREAK = '-'*50 + '\n'

class APIClient(ABC):
    __slots__ = (
        '_host',
        '_request',
        '_result'
    )

    @abstractmethod
    def _find_host(self):
        pass

    @abstractmethod
    def send_request(self, request, params) -> any:
        pass
    
    @abstractmethod
    def get_result(self) -> dict:
        pass

class GeminiClient(APIClient):
    '''
    Gemini CLI client.
    '''
    __slots__ = (
        '_model'
        )
    
    class Models:
        PRO = 'gemini-2.5.-pro'
        FLASH = 'gemini-2.5-flash'
        LITE = 'gemini-2.5-flash-lite'

    def __init__(self, 
                 model: str = Models.LITE
                 ):
        self._find_host()
        self._model = model
        return
    
    def _find_host(self) -> None:
        host_id = "gemini"
        host = shutil.which(host_id)
        if host is not None:
            self._host = host
        else:
            raise Exception(f"shutil couldn't find: {host_id}")
        return None
    
    def set_request(self, prompt: str) -> None:
        request = []
        if prompt is not None:
            request = [
                self._host, 
                "--model", self._model,
                "--output-format", "json",
                "--prompt", prompt
                ]
        self._request = request
        return None
    
    def get_request(self) -> list[str]:
        return self._request.copy()
    
    def send_request(self) -> None:
        t0 = dt.now()
        print(f'{LINE_BREAK}{t0}: Running: {self._request}\n{LINE_BREAK}')
        self._result = subprocess.run(self._request, capture_output=True, text=True, check=True)
        print(f'Finished at {dt.now()}. Runtime: {dt.now()-t0}\n{LINE_BREAK}')
        return None
    
    def get_result(self) -> dict:
        return json.loads(self._result.stdout)

