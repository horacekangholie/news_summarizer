from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

@dataclass(frozen=True)
class OllamaConfig:
    host: str
    model: str
    timeout_s: int = 180


class OllamaProvider:
    def __init__(self, cfg: OllamaConfig, schema: Optional[dict] = None) -> None:
        self.cfg = cfg
        self.schema = schema
        self._endpoint = cfg.host.rstrip("/") + "/api/generate"

    def generate_text(self, prompt: str) -> str:
        payload = {"model": self.cfg.model, "prompt": prompt, "stream": False}

        if self.schema is not None:
            payload["format"] = self.schema
            payload["options"] = {"temperature": 0}

        r = requests.post(self._endpoint, json=payload, timeout=self.cfg.timeout_s)
        r.raise_for_status()
        data = r.json()
        return (data.get("response") or "").strip()
