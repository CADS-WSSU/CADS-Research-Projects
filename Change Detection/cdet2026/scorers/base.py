"""Swappable scorer interfaces. The day loop and output code depend ONLY on these
ABCs, never on a concrete implementation (plan: architecture rule). A stronger
reranker, an entailment model, or an LLM judge can be substituted in M7 without
touching the loop. Concrete classes are resolved from config.toml.

A Candidate carries the per-document signals produced during a day so downstream
stages (novelty in M3, policy, output) can reason without re-reading raw docs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Candidate:
    doc_id: str
    text: str
    date: str = ""                 # full publication timestamp (for within-day "keep first")
    embedding: np.ndarray | None = None
    relevance: float = 0.0
    novelty: float = 0.0
    combined: float = 0.0
    extra: dict = field(default_factory=dict)


class RelevanceScorer(ABC):
    """Scores how relevant each of a day's documents is to a question's text."""

    @abstractmethod
    def score_day(self, question_text: str, candidates: list[Candidate]) -> None:
        """Set `relevance` (and `embedding` if available) on each Candidate in place."""
        raise NotImplementedError


class NoveltyScorer(ABC):
    """Scores how novel each candidate is relative to a question's accumulated memory
    of already-accepted documents. Implemented in M3."""

    @abstractmethod
    def score_day(self, question_memory, candidates: list[Candidate]) -> None:
        """Set `novelty` on each Candidate in place."""
        raise NotImplementedError
