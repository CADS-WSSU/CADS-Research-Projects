"""Judge 2 — Coverage (weight 20%).

Evaluates whether the report adequately addresses the question across the expected
CTI dimensions.
"""

from __future__ import annotations

from .base_judge import BaseJudge


class CoverageJudge(BaseJudge):
    metric = "coverage"
    weight = 0.20
    prompt_name = "coverage"
    persona = "You are a threat intelligence analyst checking completeness against the question."
