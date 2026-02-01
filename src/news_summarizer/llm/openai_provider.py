from __future__ import annotations

from dataclasses import dataclass

from news_summarizer.llm.base import LLMBlockedByRegionError

@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    model: str


class OpenAIProvider:
    def __init__(self, cfg: OpenAIConfig) -> None:
        self.cfg = cfg
        from openai import OpenAI  # type: ignore
        self._client = OpenAI(api_key=cfg.api_key)

    def generate_text(self, prompt: str) -> str:
        try:
            resp = self._client.responses.create(model=self.cfg.model, input=prompt)
            return (resp.output_text or "").strip()
        except Exception as e:
            # The OpenAI SDK raises PermissionDeniedError; message contains unsupported_country_region_territory
            msg = str(e)
            if "unsupported_country_region_territory" in msg:
                raise LLMBlockedByRegionError(msg) from e
            raise
