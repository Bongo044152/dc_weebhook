from .clock import *
from typing import Callable
from typing import Dict, Any
import json, requests

class ProcessUnit:
    def __init__(self, callback: Callable[[], Dict[str, Any]], clock: BaseClock) -> None:
        assert isinstance(clock, BaseClock), "clock must be a BaseClock instance"
        self.clock = clock
        self.callback = callback

    def run(self) -> None:
        self.clock.start_point()
        while True:
            self.clock.sleep()
            message = self.callback()
            self._post_out(message)

    def _load_config(self, path: str) -> list[str]:
        with open(path, "r") as f:
            return json.load(f)
    
    def _post_out(self, body: Dict[str, Any]):
        conf: list[str] = self._load_config("bot.json")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        for bot_url in conf:
            resp = requests.post(bot_url, json=body, headers=headers)
            resp.raise_for_status()
