"""OpenAI-compatible judge adapter.

Works against the OpenAI API and any compatible server (vLLM, gateways, LM Studio,
Ollama's ``/v1`` endpoint). Structured output is requested via
``response_format={"type": "json_object"}`` with the schema embedded in the system
prompt as a hint — the most broadly compatible approach across such servers.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Tuple

from models.schemas import Usage

from .base import LLMClient, LLMError


def _repair_json_escapes(s: str) -> str:
    """Double any backslash that is not part of a valid JSON escape.

    Judges frequently quote report text containing Windows paths (``E:\\myvyncs``),
    KQL/Sigma/regex (``\\s+``), etc. inside the rationale string and emit a *literal*
    backslash, which is an invalid JSON escape. We repair those lone backslashes
    without disturbing already-valid escapes (``\\"``, ``\\\\``, ``\\n``, ``\\uXXXX`` …).
    """
    out: list[str] = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == "\\":
            nxt = s[i + 1] if i + 1 < n else ""
            if nxt in '"\\/bfnrtu':
                out.append(c)  # valid escape — keep the pair intact
                out.append(nxt)
                i += 2
                continue
            out.append("\\\\")  # lone backslash — escape it
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _extract_json(text: str) -> Any:
    """Parse a JSON object from model output, tolerating markdown fences/prose.

    Many models (Claude via Bedrock, etc.) wrap JSON in a ```json ... ``` fence or
    add a sentence before/after it. We strip code fences, narrow to the outermost
    ``{ ... }`` block, then parse — retrying once with invalid backslash escapes
    repaired (judges quoting report paths/regex break strict JSON otherwise).
    """
    s = (text or "").strip()
    # Strip a leading ```json (or ```) fence and a trailing ``` fence.
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", s)
        s = re.sub(r"\s*```$", "", s).strip()
    # Narrow to the outermost object if there's surrounding prose.
    if not s.startswith("{"):
        start, end = s.find("{"), s.rfind("}")
        if start != -1 and end > start:
            s = s[start : end + 1]
    for candidate in (s, _repair_json_escapes(s)):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise json.JSONDecodeError("Could not parse JSON after escape repair", s, 0)


class OpenAIClient(LLMClient):
    """Judge backed by an OpenAI-compatible Chat Completions endpoint."""

    provider = "openai"

    def __init__(
        self,
        model: str = "gpt-4o",
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(model=model, **kwargs)
        try:
            import openai
        except ImportError as exc:  # pragma: no cover
            raise LLMError(
                "The 'openai' package is required for the OpenAI/vLLM judge. "
                "Install it with `pip install openai`."
            ) from exc
        self._openai = openai
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        # Some newer OpenAI models (e.g. the o-series) reject `temperature`. Sent by
        # default, disabled automatically on the first rejection (see below).
        self._send_temperature = True

    async def _raw_complete_json(
        self, *, system: str, user: str, schema: Dict[str, Any], schema_name: str
    ) -> Tuple[Dict[str, Any], Usage]:
        system_with_schema = f"{system}\n\n{self._schema_hint(schema)}"
        params: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "seed": self.seed,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_with_schema},
                {"role": "user", "content": user},
            ],
        }
        if self._send_temperature and self.temperature is not None:
            params["temperature"] = self.temperature

        try:
            resp = await self._client.chat.completions.create(**params)
        except self._openai.APIStatusError as exc:
            if "temperature" in str(exc).lower() and self._send_temperature:
                self._send_temperature = False
                raise LLMError(
                    "Model rejected `temperature` (deprecated); retrying without it."
                ) from exc
            raise LLMError(f"OpenAI API error: {exc}") from exc
        except self._openai.APIError as exc:
            raise LLMError(f"OpenAI transport error: {exc}") from exc

        choice = resp.choices[0]
        content = choice.message.content or ""
        try:
            obj = _extract_json(content)
        except json.JSONDecodeError as exc:
            # Truncated JSON is a token-budget problem, not a formatting one:
            # reasoning models (Gemini 2.5, o-series) spend thinking tokens from
            # the same `max_tokens` budget, clipping the visible output.
            if getattr(choice, "finish_reason", None) == "length":
                raise LLMError(
                    f"Response truncated at max_tokens={self.max_tokens} "
                    "(finish_reason=length). Raise `max_tokens` in config.yaml — "
                    "reasoning models consume thinking tokens from the same budget."
                ) from exc
            raise LLMError(f"OpenAI returned non-JSON content: {content[:200]!r}") from exc

        usage = Usage(
            prompt_tokens=getattr(resp.usage, "prompt_tokens", 0) if resp.usage else 0,
            completion_tokens=getattr(resp.usage, "completion_tokens", 0) if resp.usage else 0,
        )
        return obj, usage

    async def aclose(self) -> None:
        await self._client.close()
