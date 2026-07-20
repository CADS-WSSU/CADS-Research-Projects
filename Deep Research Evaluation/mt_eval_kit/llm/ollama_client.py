"""Local Ollama judge adapter.

Talks to a local Ollama server's ``/api/chat`` endpoint with ``format: "json"`` to
constrain output to a JSON object. Uses ``httpx`` (async) directly — Ollama's REST
API is simple enough not to need a heavier SDK, and this keeps the dependency
optional and light.

This makes it possible to run the *judge* itself on a local open-source model,
consistent with the parent cyber-rag-poc Ollama setup. Note: this is the judge,
separate from the open-source models being *evaluated*.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from models.schemas import Usage

from .base import LLMClient, LLMError


class OllamaClient(LLMClient):
    """Judge backed by a local Ollama server."""

    provider = "ollama"

    def __init__(
        self,
        model: str = "ollama-local",
        *,
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(model=model, **kwargs)
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover
            raise LLMError(
                "The 'httpx' package is required for the Ollama judge. "
                "Install it with `pip install httpx`."
            ) from exc
        self._httpx = httpx
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout)

    async def _raw_complete_json(
        self, *, system: str, user: str, schema: Dict[str, Any], schema_name: str
    ) -> Tuple[Dict[str, Any], Usage]:
        payload = {
            "model": self.model,
            "format": "json",
            "stream": False,
            "options": {"temperature": self.temperature, "seed": self.seed},
            "messages": [
                {"role": "system", "content": f"{system}\n\n{self._schema_hint(schema)}"},
                {"role": "user", "content": user},
            ],
        }
        try:
            resp = await self._client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
        except self._httpx.HTTPError as exc:
            raise LLMError(f"Ollama transport error: {exc}") from exc

        data = resp.json()
        content = data.get("message", {}).get("content", "")
        try:
            obj = json.loads(content)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Ollama returned non-JSON content: {content[:200]!r}") from exc

        # Ollama reports token counts as prompt_eval_count / eval_count.
        usage = Usage(
            prompt_tokens=int(data.get("prompt_eval_count", 0) or 0),
            completion_tokens=int(data.get("eval_count", 0) or 0),
        )
        return obj, usage

    async def aclose(self) -> None:
        await self._client.aclose()
