"""Judge 3 — Intelligence Utility (weight 15%).

Evaluates usefulness for a CTI analyst: actionability, operational relevance,
decision support.
"""

from __future__ import annotations

from .base_judge import BaseJudge


class UtilityJudge(BaseJudge):
    metric = "utility"
    weight = 0.15
    prompt_name = "utility"
    persona = "You are a SOC / CTI analyst assessing whether you could act on this report."
