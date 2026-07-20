"""Anthropic Claude judge adapter (the default judge).

Claude gives the most reliable structured output via **forced tool use**: a single
tool whose ``input_schema`` is the response schema, with ``tool_choice`` forcing
the call. The tool input *is* the JSON object — no prose parsing.

The ``anthropic`` package is imported lazily so the rest of the framework (and the
offline test suite) does not require it.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from models.schemas import Usage

from .base import LLMClient, LLMError


class AnthropicClient(LLMClient):
    """Judge backed by the Anthropic Messages API."""

    provider = "anthropic"

    def __init__(self, model: str = "claude-opus-4-8", *, api_key: str | None = None, **kwargs: Any) -> None:
        super().__init__(model=model, **kwargs)
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise LLMError(
                "The 'anthropic' package is required for the Anthropic judge. "
                "Install it with `pip install anthropic`."
            ) from exc
        self._anthropic = anthropic
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        # Newer Claude models (e.g. Opus 4.8) deprecate the `temperature` param and
        # reject requests that include it. We send it by default (for older models)
        # but flip this off automatically the first time the API rejects it.
        self._send_temperature = True

    async def _raw_complete_json(
        self, *, system: str, user: str, schema: Dict[str, Any], schema_name: str
    ) -> Tuple[Dict[str, Any], Usage]:
        tool = {
            "name": schema_name,
            "description": "Return the structured evaluation result.",
            "input_schema": schema,
        }
        params: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "tools": [tool],
            "tool_choice": {"type": "tool", "name": schema_name},
            "messages": [{"role": "user", "content": user}],
        }
        if self._send_temperature and self.temperature is not None:
            params["temperature"] = self.temperature

        try:
            resp = await self._client.messages.create(**params)
        except self._anthropic.APIStatusError as exc:
            # If the model deprecates `temperature`, disable it and let the retry
            # layer re-issue the request without it (transparent to the caller).
            if "temperature" in str(exc).lower() and self._send_temperature:
                self._send_temperature = False
                raise LLMError(
                    "Model rejected `temperature` (deprecated); retrying without it."
                ) from exc
            raise LLMError(f"Anthropic API error: {exc}") from exc
        except self._anthropic.APIError as exc:
            raise LLMError(f"Anthropic transport error: {exc}") from exc

        obj: Dict[str, Any] | None = None
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                obj = dict(block.input)
                break
        if obj is None:
            raise LLMError("Anthropic did not return a tool_use block")

        usage = Usage(
            prompt_tokens=getattr(resp.usage, "input_tokens", 0),
            completion_tokens=getattr(resp.usage, "output_tokens", 0),
        )
        return obj, usage

    async def aclose(self) -> None:
        await self._client.close()
