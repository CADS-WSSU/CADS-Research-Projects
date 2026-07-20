"""Abstract base class shared by every judge-LLM provider adapter.

A provider subclass implements only :meth:`LLMClient._raw_complete_json` — the
thin "call the API, return a dict + token usage" step. Everything cross-cutting
(caching, exponential-backoff retries, judge cost accounting, the JSON contract)
lives here so behaviour is identical across Anthropic, OpenAI, Gemini, Ollama,
vLLM and the deterministic offline judge.

Deterministic mode: temperature 0 + a fixed seed + the on-disk cache mean
identical requests yield identical results without re-billing.
"""

from __future__ import annotations

import abc
import json
from typing import Any, Dict, Optional, Tuple

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from models.schemas import Usage

from .cache import ResponseCache
from .cost import CostTracker


class LLMError(RuntimeError):
    """Raised on a (by default retryable) judge LLM failure."""


class LLMClient(abc.ABC):
    """Base class for all judge-LLM provider adapters."""

    #: Provider key, e.g. ``"anthropic"``. Set per subclass; used in cache keys.
    provider: str = "base"

    def __init__(
        self,
        model: str,
        *,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        seed: Optional[int] = 7,
        cache: Optional[ResponseCache] = None,
        cost_tracker: Optional[CostTracker] = None,
        max_retries: int = 4,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.seed = seed
        self.cache = cache
        self.cost_tracker = cost_tracker
        self.max_retries = max_retries

    # ------------------------------------------------------------------
    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: Dict[str, Any],
        schema_name: str = "Response",
    ) -> Tuple[Dict[str, Any], Usage]:
        """Return a JSON object conforming to ``schema`` plus token usage.

        Cache hit → return stored object with zero usage (no charge). Miss → call
        the provider through the retry wrapper, validate, record cost, cache.
        """
        cache_key = self._cache_key(system=system, user=user, schema=schema)

        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached, Usage()

        obj, usage = await self._complete_with_retry(
            system=system, user=user, schema=schema, schema_name=schema_name
        )

        if not isinstance(obj, dict):
            raise LLMError(f"{self.provider} returned non-object JSON: {type(obj)!r}")

        if self.cost_tracker is not None:
            self.cost_tracker.record(provider=self.provider, model=self.model, usage=usage)
        if self.cache is not None:
            self.cache.set(cache_key, obj)

        return obj, usage

    async def aclose(self) -> None:
        """Release network resources. Override where needed."""

    # ------------------------------------------------------------------
    async def _complete_with_retry(
        self, *, system: str, user: str, schema: Dict[str, Any], schema_name: str
    ) -> Tuple[Dict[str, Any], Usage]:
        """Invoke :meth:`_raw_complete_json` with exponential-backoff retries."""
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=30),
            retry=retry_if_exception_type(LLMError),
            reraise=True,
        ):
            with attempt:
                return await self._raw_complete_json(
                    system=system, user=user, schema=schema, schema_name=schema_name
                )
        raise LLMError("retry loop exited unexpectedly")  # pragma: no cover

    # ------------------------------------------------------------------
    @abc.abstractmethod
    async def _raw_complete_json(
        self, *, system: str, user: str, schema: Dict[str, Any], schema_name: str
    ) -> Tuple[Dict[str, Any], Usage]:
        """Perform one provider API call; return (object, usage).

        Raise :class:`LLMError` on transient failures so the retry layer engages.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    def _cache_key(self, *, system: str, user: str, schema: Dict[str, Any]) -> str:
        """Deterministic cache key covering everything that affects the output."""
        payload = {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "seed": self.seed,
            "system": system,
            "user": user,
            "schema": schema,
        }
        return json.dumps(payload, sort_keys=True, ensure_ascii=False)

    @staticmethod
    def _schema_hint(schema: Dict[str, Any]) -> str:
        """Render a schema into a prompt instruction for providers without native constraint."""
        return (
            "You MUST respond with a single JSON object matching this JSON Schema. "
            "Do not include any prose outside the JSON.\n"
            f"{json.dumps(schema, indent=2)}"
        )
