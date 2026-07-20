"""Judge 1 — Evidence Support (weight 30%).

Evaluates whether findings appear supported by evidence and reasoning.
"""

from __future__ import annotations

from .base_judge import BaseJudge


class EvidenceJudge(BaseJudge):
    metric = "evidence_support"
    weight = 0.30
    prompt_name = "evidence"
    persona = "You are a senior intelligence reviewer scrutinizing how well claims are evidenced."
