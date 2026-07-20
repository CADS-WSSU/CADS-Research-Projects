"""Judge 6 — CTI Product Quality (weight 15%).

Evaluates whether the report resembles a professional CTI product (executive
summary, key findings, structured analysis, ATT&CK mapping, indicators, chronology,
confidence language).
"""

from __future__ import annotations

from .base_judge import BaseJudge


class CTIQualityJudge(BaseJudge):
    metric = "cti_quality"
    weight = 0.15
    prompt_name = "cti_quality"
    persona = "You are a senior CTI analyst judging whether this reads like a professional product."
