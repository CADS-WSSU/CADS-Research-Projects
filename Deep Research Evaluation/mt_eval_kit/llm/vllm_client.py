"""Local vLLM judge adapter.

vLLM serves an OpenAI-compatible API, so this is a thin subclass of
:class:`~llm.openai_client.OpenAIClient` defaulting ``base_url`` to a local vLLM
server with a dummy key (vLLM ignores it but the client requires one).
"""

from __future__ import annotations

from typing import Any

from .openai_client import OpenAIClient


class VLLMClient(OpenAIClient):
    """OpenAI-compatible judge preconfigured for a local vLLM server."""

    provider = "vllm"

    def __init__(
        self,
        model: str = "vllm-local",
        *,
        base_url: str = "http://localhost:8000/v1",
        api_key: str | None = "EMPTY",
        **kwargs: Any,
    ) -> None:
        super().__init__(model=model, api_key=api_key, base_url=base_url, **kwargs)
