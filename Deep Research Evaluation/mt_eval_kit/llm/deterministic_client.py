"""Deterministic, offline judge client.

This client never touches the network. It inspects the report embedded in the
user prompt and produces a **fully deterministic** structured verdict by mapping
textual quality signals (citations, ATT&CK technique IDs, confidence/caveat
language, gap statements, CTI structure) onto 0-10 scores. It exists so that:

* Unit tests run with no API keys and no flakiness.
* The benchmark + leaderboard demo works out of the box.
* "Deterministic evaluation mode" (a hard requirement) is satisfied.

It is a transparent fixture, **not** a substitute for a real model's judgement.
The same report always yields the same scores, so leaderboards/Pareto results are
reproducible.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Tuple

from models.schemas import METRIC_NAMES, Usage

from .base import LLMClient

# Quality signal -> case-insensitive regex.
_SIGNALS: Dict[str, re.Pattern[str]] = {
    "citation": re.compile(r"\[\d+\]|\(https?://|source:|references?\b", re.I),
    "attack_id": re.compile(r"\bT\d{4}(?:\.\d{3})?\b"),
    "confidence": re.compile(r"\b(high|moderate|low) confidence\b|confidence assessment", re.I),
    "caveat": re.compile(r"\b(however|although|it is possible|alternativ|uncertain|may indicate|likely|assess(?:ed|ment))\b", re.I),
    "gap": re.compile(r"\b(intelligence gap|unknown|not (?:available|observed|confirmed)|collection requirement|insufficient)\b", re.I),
    "exec_summary": re.compile(r"executive summary|key findings|key judg|bluf", re.I),
    "attribution": re.compile(r"attribut|aliases?|also known as|aka\b", re.I),
    "ioc": re.compile(r"\b(?:[0-9a-f]{32,64})\b|indicator|hash|c2|command[- ]and[- ]control", re.I),
    "ttp": re.compile(r"\b(ttp|tactic|technique|procedure|lateral movement|persistence|exfiltrat)\b", re.I),
    "timeline": re.compile(r"\b(19|20)\d{2}\b|campaign|timeline|chronolog", re.I),
    "overclaim": re.compile(r"\b(definitely|certainly|100%|undetectable|unstoppable|never fail|no doubt|every (?:single|company|computer))\b", re.I),
}


def _count(pattern: re.Pattern[str], text: str) -> int:
    return len(pattern.findall(text))


def _scale(count: int, *, saturates_at: int) -> float:
    """Map a raw signal count onto a 0-10 sub-score with a baseline floor."""
    floor = 2.0
    if count <= 0:
        return floor
    span = 10.0 - floor
    return min(10.0, floor + span * min(count, saturates_at) / saturates_at)


def _extract(tag: str, prompt: str) -> str:
    """Pull text between ``<tag>...</tag>`` markers, or '' if absent."""
    m = re.search(rf"<{tag}>(.*?)</{tag}>", prompt, re.S | re.I)
    return m.group(1) if m else ""


class DeterministicClient(LLMClient):
    """Offline deterministic judge for tests and the zero-key demo."""

    provider = "deterministic"

    def __init__(self, model: str = "deterministic", **kwargs: Any) -> None:
        super().__init__(model=model, **kwargs)

    async def _raw_complete_json(
        self, *, system: str, user: str, schema: Dict[str, Any], schema_name: str
    ) -> Tuple[Dict[str, Any], Usage]:
        usage = Usage(prompt_tokens=len(user) // 4, completion_tokens=64)
        props = set(schema.get("properties", {}).keys())
        if {"winner", "confidence"}.issubset(props):
            return self._pairwise(user), usage
        report = _extract("report", user) or user
        return self._metric(report, system + user), usage

    # ------------------------------------------------------------------
    def _metric(self, report: str, salt: str) -> Dict[str, Any]:
        sig = {name: _count(pat, report) for name, pat in _SIGNALS.items()}
        metric = self._infer_metric(salt)
        score = self._score_for_metric(metric, sig, report)
        strengths, weaknesses = self._notes(sig)
        return {
            "metric": metric,
            "score": round(score, 2),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "rationale": (
                f"[deterministic] Heuristic assessment of '{metric}'. Signals: "
                + ", ".join(f"{k}={v}" for k, v in sorted(sig.items()) if v)
                + "."
            ),
        }

    @staticmethod
    def _infer_metric(salt: str) -> str:
        lowered = salt.lower()
        for name in METRIC_NAMES:
            if name in lowered or name.replace("_", " ") in lowered:
                return name
        return "evidence_support"

    @staticmethod
    def _score_for_metric(metric: str, sig: Dict[str, int], report: str) -> float:
        # An overclaim penalty applies to dimensions where false certainty hurts.
        overclaim_penalty = min(4.0, 1.5 * sig["overclaim"])
        if metric == "evidence_support":
            base = _scale(sig["citation"], saturates_at=8) * 0.6 + _scale(sig["caveat"], saturates_at=6) * 0.4
            return max(0.0, base - overclaim_penalty)
        if metric == "coverage":
            covered = sum(1 for k in ("attribution", "ttp", "ioc", "timeline", "attack_id") if sig[k])
            return _scale(covered, saturates_at=5)
        if metric == "utility":
            return _scale(sig["ioc"], saturates_at=6) * 0.5 + _scale(sig["attack_id"], saturates_at=6) * 0.5
        if metric == "uncertainty":
            base = _scale(sig["confidence"], saturates_at=4) * 0.5 + _scale(sig["caveat"], saturates_at=6) * 0.5
            return max(0.0, base - overclaim_penalty)  # overconfidence is penalised hardest here
        if metric == "corpus_awareness":
            base = _scale(sig["gap"], saturates_at=4)
            return max(0.0, base - overclaim_penalty)  # fabricated completeness penalised
        if metric == "cti_quality":
            structural = sum(1 for k in ("exec_summary", "attribution", "attack_id", "ioc", "confidence", "timeline") if sig[k])
            length_bonus = 1.0 if len(report) > 1200 else 0.0
            return max(0.0, min(10.0, _scale(structural, saturates_at=6) + length_bonus - overclaim_penalty * 0.5))
        return 5.0

    @staticmethod
    def _notes(sig: Dict[str, int]) -> Tuple[List[str], List[str]]:
        strengths: List[str] = []
        weaknesses: List[str] = []
        (strengths if sig["citation"] else weaknesses).append(
            "Findings cite sources." if sig["citation"] else "Claims lack citations."
        )
        (strengths if sig["attack_id"] else weaknesses).append(
            "Includes ATT&CK technique IDs." if sig["attack_id"] else "No ATT&CK mapping."
        )
        (strengths if sig["gap"] else weaknesses).append(
            "Acknowledges intelligence gaps." if sig["gap"] else "Does not surface gaps/unknowns."
        )
        if sig["overclaim"]:
            weaknesses.append("Contains overconfident / unsupported certainty.")
        return strengths, weaknesses

    # ------------------------------------------------------------------
    def _pairwise(self, user: str) -> Dict[str, Any]:
        a = _extract("report_a", user)
        b = _extract("report_b", user)
        sa = self._score_for_metric("cti_quality", {k: _count(p, a) for k, p in _SIGNALS.items()}, a)
        sb = self._score_for_metric("cti_quality", {k: _count(p, b) for k, p in _SIGNALS.items()}, b)
        if abs(sa - sb) < 0.25:
            winner = "tie"
        elif sa > sb:
            winner = "system_a"
        else:
            winner = "system_b"
        digest = int(hashlib.sha256(user.encode("utf-8")).hexdigest(), 16)
        confidence = ["low", "medium", "high"][digest % 3] if winner != "tie" else "low"
        return {
            "winner": winner,
            "confidence": confidence,
            "rationale": f"[deterministic] CTI-quality heuristic A={sa:.2f} vs B={sb:.2f} -> {winner}.",
        }
