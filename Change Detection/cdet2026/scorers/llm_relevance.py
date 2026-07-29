"""LLM relevance scorer (improvement #1): bi-encoder cosine pre-filter, then an LLM
judges TOPICAL relevance of only the top-K cosine candidates.

Motivation (verified on dev2): when the model misses a relevant doc, the bi-encoder
already ranks it at cosine rank 1-3 in ~80% of cases — the cross-encoder reranker is
what kills it (scores ~0.009 on genuinely on-topic docs, a QA-vs-topical mismatch). So
we only need a better relevance DECISION on the few top-cosine docs. An LLM reads
topical relevance far better than the QA-tuned reranker.

Leakage: the in-pipeline LLM MUST be disjoint from the gold-dataset judge (gpt-5.2) and
the panel (gemini/deepseek). Default is a CLAUDE model via the LAS gateway — deliberately
held out of the judge panel, so it stays leak-free against the benchmark.

Routes through the same OpenAI-compatible LAS gateway as the judges:
    export OPENAI_BASE_URL="https://llm-west.ncsu-las.net/v1"; export OPENAI_API_KEY="<LAS key>"
Config ([relevance]): method="llm", llm_model, llm_top_k, llm_doc_chars.
LLM verdicts are cached on disk by (question-hash+model, doc id) so each pair is scored once.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path

import numpy as np

from ..config import ROOT
from ..embeddings import Embedder
from .base import Candidate, RelevanceScorer

# LLM relevance grade on the TREC document scale 0/1/5/10 -> normalized relevance (gain/10)
# for the gate + ordering blend. The raw gain is also kept on the candidate (extra["llm_gain"]).
GRADE_TO_SCORE = {0: 0.0, 1: 0.1, 5: 0.5, 10: 1.0}

RUBRIC = """Grade how RELEVANT and IMPORTANT a NEWS DOCUMENT is to an analytic QUESTION, on the \
TREC Change Detection document scale. Judge by the SUBJECT of the question (TOPICAL relevance + \
importance), NOT by whether it states a specific answer, and NOT by novelty/recency (a separate \
stage handles "new vs already-reported").

Return ONLY JSON {"rel": N} where N is exactly one of 0, 1, 5, 10:
- 0  = not relevant — does not discuss the question's subject
- 1  = on topic but not important — a passing mention or minor coverage of the subject
- 5  = moderately important — substantive, notable coverage of the subject
- 10 = highly important — centrally about the subject with major/critical information"""


def _qhash(q: str) -> str:
    return hashlib.sha1(q.encode("utf-8")).hexdigest()[:16]


class LLMScoreCache:
    """(question-hash+model, doc id) -> relevance score."""
    def __init__(self, path: str | Path):
        p = Path(path)
        if not p.is_absolute():
            p = ROOT / p
        p.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(p))
        self.conn.execute("CREATE TABLE IF NOT EXISTS llm (qh TEXT, did TEXT, score REAL, PRIMARY KEY (qh, did))")
        self.conn.commit()

    def get_many(self, qh, dids):
        out = {}
        for i in range(0, len(dids), 800):
            ch = dids[i:i + 800]
            q = f"SELECT did,score FROM llm WHERE qh=? AND did IN ({','.join('?'*len(ch))})"
            for did, s in self.conn.execute(q, [qh, *ch]):
                out[did] = s
        return out

    def put_many(self, qh, scores):
        self.conn.executemany("INSERT OR REPLACE INTO llm (qh,did,score) VALUES (?,?,?)",
                              [(qh, d, float(s)) for d, s in scores.items()])
        self.conn.commit()


class LLMJudge:
    """Reusable graded 0/1/5/10 judge (LLM_INJECTION_PLAN Jobs A/B). One instance per
    role ('rescue' = cheap/volume, 'grade' = quality); disk-cached; call-counted."""

    _instances: dict = {}

    @classmethod
    def get(cls, cfg: dict, role: str) -> "LLMJudge":
        if role not in cls._instances:
            rc = cfg["relevance"]
            model = rc.get(f"llm_{role}_model") or rc.get("llm_model")
            cls._instances[role] = cls(cfg, model, role)
        return cls._instances[role]

    def __init__(self, cfg: dict, model: str, role: str):
        rc = cfg["relevance"]
        self.model = model
        self.role = role
        self.doc_chars = int(rc.get("llm_doc_chars", 1800))
        self.cache = LLMScoreCache(cfg["paths"]["embeddings_cache"] + f"/llm_{role}.sqlite")
        self._client = None
        self.calls = 0
        self.cache_hits = 0

    def grade(self, question: str, doc_text: str) -> int:
        """0/1/5/10 grade for (question, doc); cached by (question+model hash, doc hash)."""
        qh = _qhash(question + "\x00" + self.model)
        dh = _qhash(doc_text[: self.doc_chars])
        hit = self.cache.get_many(qh, [dh])
        if dh in hit:
            self.cache_hits += 1
            return int(hit[dh])
        g = self._call(question, doc_text)
        self.cache.put_many(qh, {dh: g})
        self.calls += 1
        if self.calls % 100 == 0:
            import sys
            sys.stderr.write(f"  [LLMJudge:{self.role}] calls={self.calls} hits={self.cache_hits}\n")
        return g

    def _call(self, question: str, doc_text: str) -> int:
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()
        prompt = f"{RUBRIC}\n\nQUESTION: {question}\n\nDOCUMENT:\n{doc_text[:self.doc_chars]}\n"
        msgs = [{"role": "user", "content": prompt}]
        for attempt in range(3):
            try:
                try:
                    r = self._client.chat.completions.create(model=self.model, messages=msgs, temperature=0.0)
                except Exception as e:
                    if "temperature" not in str(e).lower():
                        raise
                    r = self._client.chat.completions.create(model=self.model, messages=msgs)
                raw = r.choices[0].message.content or ""
                a, b = raw.find("{"), raw.rfind("}")
                if a != -1 and b != -1:
                    g = int(json.loads(raw[a:b + 1]).get("rel"))
                    if g in GRADE_TO_SCORE:
                        return g
            except Exception:  # noqa: BLE001
                pass
            time.sleep(2 * (attempt + 1))
        return 0  # unresolvable -> not relevant (conservative for silence)

    @classmethod
    def stats(cls) -> str:
        return "  ".join(f"{r}: calls={j.calls} cache_hits={j.cache_hits}"
                         for r, j in cls._instances.items()) or "no LLM calls"


class LLMRelevanceScorer(RelevanceScorer):
    def __init__(self, cfg: dict):
        rc = cfg["relevance"]
        self.embedder = Embedder(rc["model"], rc["device"], cfg["paths"]["embeddings_cache"] + "/emb.sqlite",
                                 batch_size=int(rc.get("batch_size", 64)))
        self.top_k = int(rc.get("llm_top_k", 5))
        self.model = rc.get("llm_model", "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0")
        self.doc_chars = int(rc.get("llm_doc_chars", 1800))
        self.cache = LLMScoreCache(cfg["paths"]["embeddings_cache"] + "/llm_rel.sqlite")
        self._client = None
        self._day_ids = None
        self._day_mat = None

    def _call(self, question: str, doc_text: str) -> int:
        """Return the LLM's 0/1/5/10 relevance grade (0 on failure)."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()
        prompt = f"{RUBRIC}\n\nQUESTION: {question}\n\nDOCUMENT:\n{doc_text[:self.doc_chars]}\n"
        msgs = [{"role": "user", "content": prompt}]
        for attempt in range(3):
            try:
                try:
                    r = self._client.chat.completions.create(model=self.model, messages=msgs, temperature=0.0)
                except Exception as e:
                    if "temperature" not in str(e).lower():
                        raise
                    r = self._client.chat.completions.create(model=self.model, messages=msgs)
                raw = r.choices[0].message.content or ""
                a, b = raw.find("{"), raw.rfind("}")
                if a != -1 and b != -1:
                    grade = int(json.loads(raw[a:b + 1]).get("rel"))
                    if grade in GRADE_TO_SCORE:
                        return grade
            except Exception:  # noqa: BLE001 — retry, then give up (grade 0)
                pass
            time.sleep(2 * (attempt + 1))
        return 0

    def score_day(self, question_text: str, candidates: list[Candidate]) -> None:
        if not candidates:
            return
        ids = tuple(c.doc_id for c in candidates)
        if ids != self._day_ids:
            self._day_mat = self.embedder.encode_docs(list(ids), [c.text for c in candidates])
            self._day_ids = ids
        for c, v in zip(candidates, self._day_mat):
            c.embedding = v
            c.relevance = 0.0

        qv = self.embedder.encode_query(question_text)
        cos = self._day_mat @ qv
        cos_order = np.argsort(-cos)
        cos_rank_of = {int(i): r for r, i in enumerate(cos_order, start=1)}
        pool = [int(i) for i in cos_order[: self.top_k]]
        top = [candidates[i] for i in pool]
        for i in pool:
            candidates[i].extra["dense_cos"] = float(cos[i])
            candidates[i].extra["cos_rank"] = cos_rank_of[i]

        # cache stores the raw 0/1/5/10 grade; relevance = grade/10 (normalized for gate + blend)
        qh = _qhash(question_text + "\x00" + self.model)
        cached = self.cache.get_many(qh, [c.doc_id for c in top])
        fresh = {}
        for c in top:
            grade = int(cached[c.doc_id]) if c.doc_id in cached else self._call(question_text, c.text)
            if c.doc_id not in cached:
                fresh[c.doc_id] = grade
            c.extra["llm_gain"] = grade                    # raw TREC-scale gain (for graded ordering/submission)
            c.relevance = GRADE_TO_SCORE.get(grade, 0.0)
        if fresh:
            self.cache.put_many(qh, fresh)

    def close(self) -> None:
        self.embedder.close()
