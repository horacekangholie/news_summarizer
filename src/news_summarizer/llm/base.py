from __future__ import annotations

from typing import Protocol


class LLMProvider(Protocol):
    def generate_text(self, prompt: str) -> str:
        """Return raw model text output."""

class LLMBlockedByRegionError(RuntimeError):
    pass