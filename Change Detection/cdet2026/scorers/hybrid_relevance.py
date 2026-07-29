"""Default relevance scorer: hybrid of dense cosine (bge-small-en-v1.5 on MPS) and
Okapi BM25 over the current day's documents.

Design notes (tied to the metric, see plan):
- `relevance` is set to the *absolute* dense cosine (bge-v1.5 cosines are comparable
  across days). The relevance THRESHOLD gates on this, which is what lets the system
  stay silent on a day with no relevant docs. (BM25's per-day min-max would force some
  doc to 1.0 every day and structurally defeat silence, so it must NOT be in the gate.)
- BM25 is rank-shaped, not absolute; it is min-max normalized within the day and folded
  into `extra["rank_blend"]`, used only to REORDER docs that already passed the gate
  (ordering = gain-order, which the metric rewards). Its weight is `dense_weight`.
- rank_blend = dense_weight * cosine + (1 - dense_weight) * bm25_norm
"""
from __future__ import annotations

import numpy as np
from rank_bm25 import BM25Okapi

from ..embeddings import Embedder
from ..text_utils import tokenize
from .base import Candidate, RelevanceScorer


def _minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = float(x.min()), float(x.max())
    if hi - lo < 1e-9:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)


class HybridRelevanceScorer(RelevanceScorer):
    def __init__(self, cfg: dict):
        rc = cfg["relevance"]
        self.dense_weight = float(rc["dense_weight"])
        self.embedder = Embedder(
            model_name=rc["model"],
            device=rc["device"],
            cache_path=cfg["paths"]["embeddings_cache"] + "/emb.sqlite",
            batch_size=int(rc.get("batch_size", 64)),
        )
        # Per-day artifacts (doc matrix, BM25) are cached so the ~N per-question calls
        # within one day reuse them instead of re-embedding/re-tokenizing each time.
        self._day_ids: tuple[str, ...] | None = None
        self._day_mat = None
        self._day_bm25 = None

    def _prepare_day(self, candidates: list[Candidate]) -> None:
        ids = tuple(c.doc_id for c in candidates)
        if ids == self._day_ids:
            return  # same day's document set as last call — reuse cached artifacts
        texts = [c.text for c in candidates]
        self._day_mat = self.embedder.encode_docs(list(ids), texts)
        self._day_bm25 = BM25Okapi([tokenize(t) for t in texts])
        self._day_ids = ids

    def score_day(self, question_text: str, candidates: list[Candidate]) -> None:
        if not candidates:
            return
        self._prepare_day(candidates)
        doc_mat = self._day_mat
        for c, v in zip(candidates, doc_mat):
            c.embedding = v

        # Dense: cosine of L2-normalized vectors == dot product.
        qv = self.embedder.encode_query(question_text)
        cos = np.clip(doc_mat @ qv, 0.0, 1.0)

        # Lexical: BM25 over THIS day's documents only.
        bm25_scores = np.asarray(self._day_bm25.get_scores(tokenize(question_text)), dtype=np.float32)
        bm25_norm = _minmax(bm25_scores)

        rank_blend = self.dense_weight * cos + (1.0 - self.dense_weight) * bm25_norm
        for c, dn, bn, rb in zip(candidates, cos, bm25_norm, rank_blend):
            c.relevance = float(dn)  # ABSOLUTE dense cosine — what the gate thresholds on
            c.extra["dense_cos"] = float(dn)
            c.extra["bm25_norm"] = float(bn)
            c.extra["rank_blend"] = float(rb)  # dense+BM25, for ordering passed docs only

    def close(self) -> None:
        self.embedder.close()
