"""Google Gemini judge adapter.

Gemini supports native JSON output via ``generation_config`` with
``response_mime_type="application/json"``. The schema is embedded in the system
instruction as a hint. The SDK is synchronous, so the blocking call is offloaded
to a thread via ``asyncio.to_thread`` to keep the pipeline non-blocking.

``google-generativeai`` is imported lazily so it is only required when Gemini is
actually selected.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Tuple

from models.schemas import Usage

from .base import LLMClient, LLMError


class GeminiClient(LLMClient):
    """Judge backed by Google's Generative AI (Gemini) API."""

    provider = "gemini"

    def __init__(self, model: str = "gemini-1.5-pro", *, api_key: str | None = None, **kwargs: Any) -> None:
        super().__init__(model=model, **kwargs)
        try:
            import google.generativeai as genai
        except ImportError as exc:  # pragma: no cover
            raise LLMError(
                "The 'google-generativeai' package is required for the Gemini judge. "
                "Install it with `pip install google-generativeai`."
            ) from exc
        self._genai = genai
        if api_key:
            genai.configure(api_key=api_key)

    async def _raw_complete_json(
        self, *, system: str, user: str, schema: Dict[str, Any], schema_name: str
    ) -> Tuple[Dict[str, Any], Usage]:
        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
            "response_mime_type": "application/json",
        }
        model = self._genai.GenerativeModel(
            model_name=self.model,
            system_instruction=f"{system}\n\n{self._schema_hint(schema)}",
            generation_config=generation_config,
        )

        def _blocking_call() -> Any:
            return model.generate_content(user)

        try:
            resp = await asyncio.to_thread(_blocking_call)
        except Exception as exc:  # SDK raises varied error types
            raise LLMError(f"Gemini API error: {exc}") from exc

        text = getattr(resp, "text", "") or ""
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Gemini returned non-JSON content: {text[:200]!r}") from exc

        meta = getattr(resp, "usage_metadata", None)
        usage = Usage(
            prompt_tokens=getattr(meta, "prompt_token_count", 0) if meta else 0,
            completion_tokens=getattr(meta, "candidates_token_count", 0) if meta else 0,
        )
        return obj, usage
