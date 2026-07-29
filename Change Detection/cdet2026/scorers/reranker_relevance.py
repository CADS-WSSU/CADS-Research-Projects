"""Default relevance scorer (M6 redesign): bi-encoder cosine pre-filter followed by a
local cross-encoder reranker on chunked passages.

Why: diagnostics on the proxy qrel showed bi-encoder cosine cannot separate relevant
docs from the best non-relevant doc on a nil day (both ~0.58-0.60 cosine), so no cosine
threshold yields correct silence. A cross-encoder (BAAI/bge-reranker-v2-m3) scores the
(question, passage) pair directly and is far more discriminative — nil-day false-fires
drop from ~82% to ~3-5%.

Pipeline per (question, day):
  1. cosine over all day docs (cheap) -> keep the top prefilter_n as rerank candidates
     (relevant docs are ~89% in the top-10, so this barely costs recall);
  2. split each candidate into <=max_chunks passages, cross-encoder score each
     (question, passage), take the max -> the document's relevance probability;
  3. relevance = that probability (0 for docs outside the top-N). The fire gate
     thresholds on it.

Reranker scores are cached on disk keyed by (question-hash, doc id) so they are computed
once and reused across the tuning sweep and re-runs (the score is threshold-independent).
"""
from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import numpy as np

from rank_bm25 import BM25Okapi

from ..config import ROOT
from ..embeddings import Embedder
from ..text_utils import tokenize
from ..textclean import clean_text
from .base import Candidate, RelevanceScorer


def _qhash(q: str) -> str:
    return hashlib.sha1(q.encode("utf-8")).hexdigest()[:16]


class RerankScoreCache:
    """(question-hash, doc id) -> reranker probability."""

    def __init__(self, path: str | Path):
        p = Path(path)
        if not p.is_absolute():
            p = ROOT / p
        p.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(p))
        self.conn.execute("CREATE TABLE IF NOT EXISTS rr (qh TEXT, did TEXT, score REAL, PRIMARY KEY (qh, did))")
        self.conn.commit()

    def get_many(self, qh: str, dids: list[str]) -> dict[str, float]:
        out: dict[str, float] = {}
        for i in range(0, len(dids), 800):
            chunk = dids[i : i + 800]
            q = f"SELECT did, score FROM rr WHERE qh=? AND did IN ({','.join('?' * len(chunk))})"
            for did, score in self.conn.execute(q, [qh, *chunk]):
                out[did] = score
        return out

    def put_many(self, qh: str, scores: dict[str, float]) -> None:
        self.conn.executemany(
            "INSERT OR REPLACE INTO rr (qh, did, score) VALUES (?, ?, ?)",
            [(qh, did, float(s)) for did, s in scores.items()],
        )
        self.conn.commit()


def _chunks(text: str, n: int, overlap: int, max_chunks: int) -> list[str]:
    text = text.strip()
    if len(text) <= n:
        return [text]
    out, i = [], 0
    while i < len(text) and len(out) < max_chunks:
        out.append(text[i : i + n])
        i += n - overlap
    return out


class RerankerRelevanceScorer(RelevanceScorer):
    def __init__(self, cfg: dict):
        from sentence_transformers import CrossEncoder

        rc = cfg["relevance"]
        self.prefilter_n = int(rc["prefilter_n"])
        self.chunk_chars = int(rc["chunk_chars"])
        self.chunk_overlap = int(rc["chunk_overlap"])
        self.max_chunks = int(rc["max_chunks"])
        self.embedder = Embedder(rc["model"], rc["device"], cfg["paths"]["embeddings_cache"] + "/emb.sqlite",
                                 batch_size=int(rc.get("batch_size", 64)))
        self.ce = CrossEncoder(rc["reranker_model"], device=rc["device"], max_length=512)
        # Optional bf16 reranker inference (~3-4x on Ada/L4 tensor cores; verify decision-parity
        # vs fp32 before trusting). Uses a separate cache salt so bf16 scores never mix with fp32.
        self.bf16 = bool(rc.get("reranker_bf16", False))
        self.rerank_bs = int(rc.get("reranker_batch_size", 64))
        if self.bf16:
            import torch
            self.ce.model = self.ce.model.to(torch.bfloat16)
        self.cache = RerankScoreCache(cfg["paths"]["embeddings_cache"] + "/rerank.sqlite")
        self.clean = bool(rc.get("clean_text", False))  # A3: boilerplate-strip before reranking
        self.fusion = bool(rc.get("fusion", False))     # A1: union cosine-top + BM25-top candidate pool
        self._day_ids: tuple[str, ...] | None = None
        self._day_mat = None
        self._day_bm25 = None

    def _prepare_day(self, candidates: list[Candidate]) -> None:
        ids = tuple(c.doc_id for c in candidates)
        if ids != self._day_ids:
            self._day_mat = self.embedder.encode_docs(list(ids), [c.text for c in candidates])
            self._day_bm25 = BM25Okapi([tokenize(c.text) for c in candidates]) if self.fusion else None
            self._day_ids = ids

    def score_day(self, question_text: str, candidates: list[Candidate]) -> None:
        if not candidates:
            return
        self._prepare_day(candidates)
        doc_mat = self._day_mat
        for c, v in zip(candidates, doc_mat):
            c.embedding = v
            c.relevance = 0.0

        # 1) candidate pool to rerank: cosine top-N, optionally UNIONed with BM25 top-N (A1).
        qv = self.embedder.encode_query(question_text)
        cos = doc_mat @ qv
        cos_order = np.argsort(-cos)
        cos_rank_of = {int(i): r for r, i in enumerate(cos_order, start=1)}
        pool = list(cos_order[: self.prefilter_n])
        if self.fusion:
            bm = np.asarray(self._day_bm25.get_scores(tokenize(question_text)), dtype=np.float32)
            bm_order = np.argsort(-bm)
            bm_rank_of = {int(i): r for r, i in enumerate(bm_order, start=1)}
            for i in bm_order[: self.prefilter_n]:
                if int(i) not in {int(x) for x in pool}:
                    pool.append(int(i))
        top = [candidates[int(i)] for i in pool]
        for i in pool:
            candidates[int(i)].extra["dense_cos"] = float(cos[int(i)])
            candidates[int(i)].extra["cos_rank"] = cos_rank_of[int(i)]
            if self.fusion:
                candidates[int(i)].extra["bm25_rank"] = bm_rank_of[int(i)]

        # 2) reranker probability for the top-N (cache-backed). Salt the cache key when
        #    cleaning so cleaned scores don't collide with the cached raw-text scores.
        qh = _qhash(question_text + ("\x00clean" if self.clean else "") + ("\x00bf16" if self.bf16 else ""))
        cached = self.cache.get_many(qh, [c.doc_id for c in top])
        missing = [c for c in top if c.doc_id not in cached]
        if missing:
            pairs, owner = [], []
            for c in missing:
                doc_text = clean_text(c.text) if self.clean else c.text
                for ch in _chunks(doc_text, self.chunk_chars, self.chunk_overlap, self.max_chunks):
                    pairs.append((question_text, ch))
                    owner.append(c.doc_id)
            probs = np.asarray(self.ce.predict(pairs, batch_size=self.rerank_bs, show_progress_bar=False))
            best: dict[str, float] = {}
            for did, p in zip(owner, probs):
                best[did] = max(best.get(did, 0.0), float(p))
            self.cache.put_many(qh, best)
            cached.update(best)

        # 3) relevance = reranker probability; reorder by it
        for c in top:
            c.relevance = float(cached.get(c.doc_id, 0.0))
            c.extra["rank_blend"] = c.relevance  # reranker prob is already the ordering signal

    def close(self) -> None:
        self.embedder.close()
