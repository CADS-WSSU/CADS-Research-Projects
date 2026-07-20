"""Judge token pricing and a cost accumulator.

These prices estimate the cost of running the **judge** (not the models under
test). Numbers are approximate USD per 1,000,000 tokens and live in one editable
table. Local providers (Ollama, vLLM, deterministic) are free.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, Tuple

from models.schemas import Usage

# (input_per_million, output_per_million) USD, keyed by lowercase model id.
_PRICES: Dict[str, Tuple[float, float]] = {
    # Anthropic Claude (default judge)
    "claude-opus-4-8": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    # OpenAI (representative)
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    # Gemini (representative)
    "gemini-1.5-pro": (1.25, 5.0),
    "gemini-1.5-flash": (0.075, 0.3),
    # Local / offline judges: no marginal cost.
    "deterministic": (0.0, 0.0),
    "ollama-local": (0.0, 0.0),
    "vllm-local": (0.0, 0.0),
}

_DEFAULT_PRICE: Tuple[float, float] = (0.0, 0.0)


def estimate_cost(model: str, usage: Usage) -> float:
    """Estimate the USD cost of a single judge call. Tolerant of provider prefixes."""
    key = model.lower().split("/")[-1]
    in_price, out_price = _PRICES.get(key, _DEFAULT_PRICE)
    cost = (usage.prompt_tokens / 1_000_000) * in_price
    cost += (usage.completion_tokens / 1_000_000) * out_price
    return round(cost, 6)


@dataclass
class CostTracker:
    """Thread-safe accumulator of judge token usage and estimated cost."""

    total_usage: Usage = field(default_factory=Usage)
    total_cost_usd: float = 0.0
    n_calls: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, *, provider: str, model: str, usage: Usage) -> float:
        """Record one call's usage; return its estimated cost."""
        cost = estimate_cost(model, usage)
        with self._lock:
            self.total_usage = self.total_usage + usage
            self.total_cost_usd = round(self.total_cost_usd + cost, 6)
            self.n_calls += 1
        return cost

    def summary(self) -> Dict[str, float | int]:
        return {
            "n_calls": self.n_calls,
            "prompt_tokens": self.total_usage.prompt_tokens,
            "completion_tokens": self.total_usage.completion_tokens,
            "total_tokens": self.total_usage.total_tokens,
            "total_cost_usd": self.total_cost_usd,
        }
