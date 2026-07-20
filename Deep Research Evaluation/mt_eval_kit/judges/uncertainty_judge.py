"""Judge 4 — Uncertainty Calibration (weight 10%).

Evaluates whether confidence levels match available evidence; rewards caveats and
confidence assessments, penalizes overconfidence.
"""

from __future__ import annotations

from .base_judge import BaseJudge


class UncertaintyJudge(BaseJudge):
    metric = "uncertainty"
    weight = 0.10
    prompt_name = "uncertainty"
    persona = "You are an analytic tradecraft reviewer assessing confidence calibration."
