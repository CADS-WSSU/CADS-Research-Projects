"""Pairwise quality judge.

Given a question and two reports, decides which is the better intelligence product.
Returns a :class:`PairwiseVerdict` (winner system_a/system_b/tie + confidence +
rationale). The round-robin tournament logic lives in :mod:`orchestrator`.
"""

from __future__ import annotations

from typing import Any, Dict

from llm.base import LLMClient
from models.schemas import PairwiseVerdict
from prompts import render


def _coerce_winner(value: Any) -> str:
    """Map a model-provided winner into the canonical enum.

    Local judges often answer ``"A"``, ``"report_a"``, ``"system a"`` or even the
    model name instead of the exact literal ``system_a``. We normalise the common
    variants; anything unrecognised defaults to ``"tie"`` so one odd response never
    aborts a round-robin.
    """
    text = str(value).strip().lower()
    if text in {"system_a", "a", "report_a", "report a", "system a", "1", "first", "left"}:
        return "system_a"
    if text in {"system_b", "b", "report_b", "report b", "system b", "2", "second", "right"}:
        return "system_b"
    if text in {"tie", "draw", "equal", "even", "neither", "both"}:
        return "tie"
    # Fall back: look for an 'a'/'b' token; else tie.
    if text.endswith("_a") or text.endswith(" a") or text == "a":
        return "system_a"
    if text.endswith("_b") or text.endswith(" b") or text == "b":
        return "system_b"
    return "tie"


def _coerce_confidence(value: Any) -> str:
    """Coerce confidence into low/medium/high (default medium)."""
    text = str(value).strip().lower()
    if text in {"low", "medium", "high"}:
        return text
    if text in {"med", "moderate"}:
        return "medium"
    return "medium"


def coerce_pairwise_obj(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise a raw pairwise response into a valid ``PairwiseVerdict`` payload."""
    if not isinstance(obj, dict):
        obj = {}
    return {
        "winner": _coerce_winner(obj.get("winner")),
        "confidence": _coerce_confidence(obj.get("confidence")),
        "rationale": str(obj.get("rationale", "") or ""),
    }

_PAIRWISE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "winner": {"type": "string", "enum": ["system_a", "system_b", "tie"]},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "rationale": {"type": "string"},
    },
    "required": ["winner", "rationale"],
}


class PairwiseJudge:
    """Judge two reports head-to-head for the same question."""

    persona = "You are a senior cyber threat intelligence analyst comparing two reports."

    def __init__(self, client: LLMClient) -> None:
        self.client = client

    async def compare(self, *, question: str, report_a: str, report_b: str) -> PairwiseVerdict:
        """Return the verdict for report A vs report B.

        ``system_a`` maps to ``report_a`` and ``system_b`` to ``report_b``; the caller
        maps these back to model names and handles order balancing.
        """
        user_prompt = render("pairwise", question=question, report_a=report_a, report_b=report_b)
        obj, _usage = await self.client.complete_json(
            system=self.persona,
            user=user_prompt,
            schema=_PAIRWISE_SCHEMA,
            schema_name="pairwise_verdict",
        )
        return PairwiseVerdict.model_validate(coerce_pairwise_obj(obj))
