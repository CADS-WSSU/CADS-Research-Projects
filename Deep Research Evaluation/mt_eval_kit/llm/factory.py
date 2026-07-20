"""Construct configured judge-LLM clients from a provider name + config dict.

Adding a new provider is a one-line edit to :data:`_REGISTRY`. Call sites never
import concrete client classes.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from .anthropic_client import AnthropicClient
from .base import LLMClient
from .cache import ResponseCache
from .cost import CostTracker
from .deterministic_client import DeterministicClient
from .gemini_client import GeminiClient
from .ollama_client import OllamaClient
from .openai_client import OpenAIClient
from .vllm_client import VLLMClient

_REGISTRY: Dict[str, Callable[..., LLMClient]] = {
    "anthropic": AnthropicClient,
    "claude": AnthropicClient,  # alias
    "openai": OpenAIClient,
    "gemini": GeminiClient,
    "google": GeminiClient,  # alias
    "ollama": OllamaClient,
    "vllm": VLLMClient,
    "deterministic": DeterministicClient,
    "mock": DeterministicClient,  # alias
}


def available_providers() -> list[str]:
    """Return the sorted list of recognised provider keys."""
    return sorted(_REGISTRY)


def build_client(
    provider: str,
    config: Dict[str, Any],
    *,
    cache: Optional[ResponseCache] = None,
    cost_tracker: Optional[CostTracker] = None,
) -> LLMClient:
    """Instantiate the judge client for ``provider`` using ``config``.

    Per-provider settings live under ``config["providers"][provider]``; top-level
    ``temperature``/``max_tokens``/``seed``/``max_retries`` act as defaults.
    """
    key = provider.lower()
    if key not in _REGISTRY:
        raise ValueError(
            f"Unknown provider '{provider}'. Available: {', '.join(available_providers())}"
        )

    provider_cfg: Dict[str, Any] = dict(config.get("providers", {}).get(key, {}))
    kwargs: Dict[str, Any] = {
        "temperature": config.get("temperature", 0.0),
        "max_tokens": config.get("max_tokens", 2048),
        "seed": config.get("seed", 7),
        "max_retries": config.get("max_retries", 4),
        "cache": cache,
        "cost_tracker": cost_tracker,
    }
    kwargs.update(provider_cfg)  # model, api_key, base_url, overrides
    return _REGISTRY[key](**kwargs)
