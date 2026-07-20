"""Judge LLM client layer.

These clients drive the *judge* (the evaluator), not the models under test. All
concrete providers implement :class:`llm.base.LLMClient` and are constructed via
:func:`llm.factory.build_client` so caching, retries and cost tracking are wired
consistently.
"""

from .base import LLMClient, LLMError
from .cache import ResponseCache
from .cost import CostTracker, estimate_cost
from .factory import available_providers, build_client

__all__ = [
    "LLMClient",
    "LLMError",
    "ResponseCache",
    "CostTracker",
    "estimate_cost",
    "build_client",
    "available_providers",
]
