from __future__ import annotations

import os

from news_summarizer.llm.base import LLMProvider
from news_summarizer.llm.openai_provider import OpenAIConfig, OpenAIProvider
from news_summarizer.llm.ollama_provider import OllamaConfig, OllamaProvider
from news_summarizer.models import NewsItem


def build_provider(provider: str) -> LLMProvider:
    provider = provider.strip().lower()

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise SystemExit("Missing OPENAI_API_KEY for OpenAI provider.")
        model = (os.getenv("OPENAI_MODEL") or "gpt-5.2").strip()
        return OpenAIProvider(OpenAIConfig(api_key=api_key, model=model))

    if provider == "ollama":
        host = (os.getenv("OLLAMA_HOST") or "http://localhost:11434").strip()
        model = (os.getenv("OLLAMA_MODEL") or "llama3.2").strip()
        timeout_s = int(os.getenv("OLLAMA_TIMEOUT_S") or "180")
        schema = NewsItem.model_json_schema()
        return OllamaProvider(OllamaConfig(host=host, model=model, timeout_s=timeout_s), schema=schema)

    raise SystemExit(f"Unknown provider: {provider}")


def build_provider_from_env() -> LLMProvider:
    return build_provider(os.getenv("LLM_PROVIDER") or "openai")
