"""Judge 5 — Corpus Awareness (weight 10%).

Evaluates whether the report correctly identifies evidence gaps; rewards unknowns
and collection requirements, penalizes invented details and false completeness.
"""

from __future__ import annotations

from .base_judge import BaseJudge


class CorpusAwarenessJudge(BaseJudge):
    metric = "corpus_awareness"
    weight = 0.10
    prompt_name = "corpus_awareness"
    persona = "You are a collection manager assessing whether the report knows the limits of its evidence."
