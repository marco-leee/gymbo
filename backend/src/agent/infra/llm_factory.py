"""OpenRouter LLM client factory."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

DEFAULT_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"


class LLMClientFactory:
    def __init__(self, *, dry_run: bool = False) -> None:
        self._dry_run = dry_run
        self._client: ChatOpenAI | None = None

    @classmethod
    def from_env(cls, *, dry_run: bool = False) -> LLMClientFactory:
        return cls(dry_run=dry_run)

    def get_client(self) -> ChatOpenAI | None:
        if self._dry_run:
            return None
        if self._client is None:
            api_key = os.environ.get("OPENROUTER_API_KEY")
            if not api_key:
                raise RuntimeError("OPENROUTER_API_KEY is required")
            self._client = ChatOpenAI(
                model=os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL),
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                temperature=0.2,
            )
        return self._client
