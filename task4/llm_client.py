"""Shared LLM client used by all strategies.

Supports OpenRouter and OpenAI-compatible endpoints.
Caching is done at the eval-harness level to keep strategy code simple.
"""

import time
import json
from typing import Dict, Any, Optional, List

from openai import OpenAI
from config import CONFIG


class LLMClient:
    """Singleton-style LLM client shared across strategies."""

    _instance: Optional["LLMClient"] = None

    def __init__(self):
        if CONFIG.openrouter_api_key:
            self.client = OpenAI(
                base_url=CONFIG.openrouter_base_url,
                api_key=CONFIG.openrouter_api_key,
            )
        elif CONFIG.openai_api_key:
            self.client = OpenAI(
                base_url=CONFIG.openai_base_url,
                api_key=CONFIG.openai_api_key,
            )
        else:
            self.client = None

    @classmethod
    def get(cls) -> "LLMClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Send a chat completion and return (content, input_tokens, output_tokens, latency_ms)."""
        if self.client is None:
            raise RuntimeError(
                "No API key configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY."
            )

        model = model or CONFIG.solver_model
        start = time.perf_counter()

        kwargs = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        if extra_headers:
            kwargs["extra_headers"] = extra_headers

        response = self.client.chat.completions.create(**kwargs)
        latency = (time.perf_counter() - start) * 1000

        choice = response.choices[0]
        content = choice.message.content or ""

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        return {
            "content": content,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency,
        }


# Module-level convenience
_llm = None


def get_llm() -> LLMClient:
    global _llm
    if _llm is None:
        _llm = LLMClient.get()
    return _llm


def chat(messages, model=None, temperature=0.0, max_tokens=1024):
    return get_llm().chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)