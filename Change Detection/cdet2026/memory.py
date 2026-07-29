"""Per-question memory of documents already accepted as relevant on earlier days.

Each question accumulates: the embeddings of accepted docs (for cosine-novelty), the
set of content terms seen, and the set of named entities seen. Novelty on later days
is measured against this memory, so a restatement of something already reported scores
low and the question does not re-fire on it.

Persisted with pickle to the state dir so a run is resumable across process restarts.
"""
from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from .config import ROOT


class QuestionMemory:
    def __init__(self):
        self._embs: list[np.ndarray] = []
        self.doc_ids: list[str] = []
        self.terms: set[str] = set()
        self.entities: set[str] = set()
        # per-question background of the daily relevance signal (Welford running mean/var),
        # for change-point / z-score calibration (idea B). Updated from PAST days only.
        self.bg_n: int = 0
        self.bg_mean: float = 0.0
        self.bg_M2: float = 0.0

    @property
    def is_empty(self) -> bool:
        return not self.doc_ids

    @property
    def bg_std(self) -> float:
        return (self.bg_M2 / (self.bg_n - 1)) ** 0.5 if self.bg_n > 1 else 0.0

    def zscore(self, x: float, min_bg: int) -> float | None:
        """Deviation of today's signal from this question's own background, in std units.
        None until `min_bg` past days have accumulated (cold-start warm-up)."""
        if self.bg_n < min_bg:
            return None
        sd = self.bg_std
        return (x - self.bg_mean) / sd if sd > 1e-9 else 0.0

    def update_bg(self, x: float) -> None:
        """Fold today's signal into the running background (call AFTER using zscore)."""
        self.bg_n += 1
        d = x - self.bg_mean
        self.bg_mean += d / self.bg_n
        self.bg_M2 += d * (x - self.bg_mean)

    def working_copy(self) -> tuple[list, set, set]:
        """Mutable snapshot (embeddings list, term set, entity set) for within-day
        accumulation without touching the persisted memory."""
        return list(self._embs), set(self.terms), set(self.entities)

    def max_cosine(self, vec: np.ndarray) -> float:
        """Max cosine of `vec` (L2-normalized) to any accepted doc. 0.0 if empty."""
        if not self._embs:
            return 0.0
        mat = np.vstack(self._embs)  # already L2-normalized
        return float(np.max(mat @ vec))

    def add(self, doc_id: str, vec: np.ndarray, terms: set[str], entities: set[str]) -> None:
        if doc_id in self.doc_ids:
            return
        self._embs.append(vec.astype(np.float32))
        self.doc_ids.append(doc_id)
        self.terms |= terms
        self.entities |= entities


class MemoryStore:
    """Holds a QuestionMemory per (topic_id, qid). Pickled to one file."""

    def __init__(self, path: str | Path):
        p = Path(path)
        if not p.is_absolute():
            p = ROOT / p
        p.parent.mkdir(parents=True, exist_ok=True)
        self.path = p
        self._mem: dict[tuple[str, str], QuestionMemory] = {}

    def get(self, tid: str, qid: str) -> QuestionMemory:
        key = (tid, qid)
        if key not in self._mem:
            self._mem[key] = QuestionMemory()
        return self._mem[key]

    def save(self) -> None:
        with open(self.path, "wb") as f:
            pickle.dump(self._mem, f)

    def load(self) -> "MemoryStore":
        if self.path.exists():
            with open(self.path, "rb") as f:
                self._mem = pickle.load(f)
        return self
