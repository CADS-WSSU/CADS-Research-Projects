"""Base class for the six single-metric quality judges.

Each judge is a declarative object: it knows its **metric name**, **composite
weight**, **prompt template**, and **persona**. The shared logic — render the
prompt, call the judge LLM with the right JSON schema, validate into a
:class:`JudgeResult` — lives here. The schema handed to the model is derived from
:class:`models.schemas.JudgeResult`, so what the model sees and what we validate
can never drift.
"""

from __future__ import annotations

import re
from typing import Any, Dict

from llm.base import LLMClient
from models.schemas import JudgeResult
from prompts import render

# JSON Schema for a single judge verdict.
_JUDGE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "metric": {"type": "string"},
        "score": {"type": "number", "minimum": 0, "maximum": 10},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "weaknesses": {"type": "array", "items": {"type": "string"}},
        "rationale": {"type": "string"},
    },
    "required": ["metric", "score", "rationale"],
}


class BaseJudge:
    """Score one quality dimension of a report.

    Subclasses set :attr:`metric`, :attr:`weight`, :attr:`prompt_name`,
    :attr:`persona`.
    """

    metric: str = ""
    weight: float = 0.0
    prompt_name: str = ""
    persona: str = "You are a senior cyber threat intelligence analyst."

    def __init__(self, client: LLMClient) -> None:
        self.client = client

    async def evaluate(self, *, question: str, report: str) -> JudgeResult:
        """Run the judge on one (question, report) pair, returning a JudgeResult.

        The ``metric`` field is pinned to this judge's canonical name regardless of
        what the model echoes, so composite math always finds the expected key.
        """
        user_prompt = render(self.prompt_name, question=question, report=report)
        system_prompt = f"{self.persona}\nYou are scoring the metric: {self.metric}."

        obj, _usage = await self.client.complete_json(
            system=system_prompt,
            user=user_prompt,
            schema=_JUDGE_SCHEMA,
            schema_name=f"{self.metric}_result",
        )
        return JudgeResult.model_validate(coerce_judge_obj(obj, metric=self.metric))


# ---------------------------------------------------------------------------
# Output coercion (robustness for real / local judges)
# ---------------------------------------------------------------------------
#
# Providers that enforce the schema (Anthropic tool-use) always return clean
# objects, but local judges (Ollama, vLLM) and some OpenAI-compatible servers
# only guarantee "some JSON". They may emit a score of 12, "8/10", a string
# instead of a list, or omit optional fields. Rather than let one malformed
# response crash an entire benchmark via a Pydantic ValidationError, we normalise
# the object into the expected shape first. This is lenient on purpose: a score
# of 12 becomes 10 (the model clearly meant "max"), not a hard failure.


def _coerce_score(value: Any) -> float:
    """Coerce a model-provided score into a float clamped to [0, 10].

    Accepts numbers, numeric strings, and strings like ``"8/10"`` or
    ``"score: 7.5"`` (the first number found is used). Falls back to ``5.0``
    (neutral) only if no number can be extracted at all, so a single odd response
    never aborts the run.
    """
    if isinstance(value, bool):  # guard: bools are ints in Python
        value = float(value)
    if isinstance(value, (int, float)):
        score = float(value)
    elif isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        score = float(match.group(0)) if match else 5.0
    else:
        score = 5.0
    return round(max(0.0, min(10.0, score)), 2)


def _coerce_str_list(value: Any) -> list[str]:
    """Coerce a value into a list of strings (a bare string becomes one item)."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)]


def coerce_judge_obj(obj: Dict[str, Any], *, metric: str) -> Dict[str, Any]:
    """Normalise a raw judge response into a valid ``JudgeResult`` payload.

    The ``metric`` is pinned to the judge's canonical name regardless of what the
    model echoed back, so downstream composite math always finds the expected key.
    """
    if not isinstance(obj, dict):
        obj = {}
    return {
        "metric": metric,
        "score": _coerce_score(obj.get("score")),
        "strengths": _coerce_str_list(obj.get("strengths")),
        "weaknesses": _coerce_str_list(obj.get("weaknesses")),
        "rationale": str(obj.get("rationale", "") or ""),
    }
