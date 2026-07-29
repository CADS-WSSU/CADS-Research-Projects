"""Sentence-gain engine — single-stage LLM-free scoring (SENTENCE_GAIN_PLAN.md §1/§4).

gain(d, q) = sum over sentences s of d with rel(s,q) >= tau of rel(s,q) * new(s,q)
  rel = cosine(sentence, question vector)  (bge-small; optional seed-doc anchoring §10.A)
  new = max cosine to the question's reported-sentence memory (+ accepted-earlier-today) < nu

Fire iff gain >= gamma (optionally per-question background z-score, §10.B). Docs ordered
by gain; emitted score = gain; graded bin (1/5/10) via config bins — placeholder until
Phase 3 boundary-LLM grading. Sentence memory keeps TEXT alongside embeddings so Phase 3
can build the known-facts summary.

Per-day sentence index is computed once and shared across every topic/question that day
(~27k sentences ≈ 42 MB fp32, seconds on GPU) — no giant disk cache.
"""
from __future__ import annotations

import numpy as np

from .textclean import clean_text


class SentenceMemory:
    """Per-question memory of reported relevant sentences (+ firing background stats)."""

    def __init__(self, cap: int = 300):
        self.cap = cap
        self.embs = np.zeros((0, 384), dtype=np.float32)
        self.texts: list[str] = []
        # background stats of daily max-gain (for optional z-score firing, §10.B)
        self.bg_n = 0
        self.bg_mean = 0.0
        self.bg_m2 = 0.0

    def add(self, embs: np.ndarray, texts: list[str]) -> None:
        if not len(embs):
            return
        self.embs = np.vstack([self.embs, embs])[-self.cap:]
        self.texts = (self.texts + list(texts))[-self.cap:]

    def max_sim(self, embs: np.ndarray, extra: np.ndarray | None = None) -> np.ndarray:
        mem = self.embs if extra is None or not len(extra) else np.vstack([self.embs, extra])
        if not len(mem) or not len(embs):
            return np.zeros(len(embs), dtype=np.float32)
        return (embs @ mem.T).max(axis=1)

    def bg_update(self, x: float) -> None:
        self.bg_n += 1
        d = x - self.bg_mean
        self.bg_mean += d / self.bg_n
        self.bg_m2 += d * (x - self.bg_mean)

    def bg_z(self, x: float) -> float:
        if self.bg_n < 8:
            return 0.0
        sd = (self.bg_m2 / max(1, self.bg_n - 1)) ** 0.5
        return (x - self.bg_mean) / (sd + 1e-6)


class SentGainEngine:
    """Owns the sentencizer, encoder, per-day shared sentence index, and question vectors."""

    def __init__(self, cfg: dict):
        import spacy
        from sentence_transformers import SentenceTransformer

        sc = cfg.get("sentgain", {})
        self.tau = float(sc.get("tau", 0.70))
        self.nu = float(sc.get("nu", 0.90))
        self.gamma = float(sc.get("gamma", 0.0))          # set from nil percentile at tuning
        self.use_zscore = bool(sc.get("use_zscore", False))
        self.z_thr = float(sc.get("z_thr", 3.0))
        self.mem_cap = int(sc.get("max_mem_sents", 300))
        self.seed_alpha = float(sc.get("seed_alpha", 1.0))  # 1.0 = plain question vector
        g1, g5 = sc.get("gain_bins", [1.5, 3.0])
        self.bins = (float(g1), float(g5))                 # gain<g1 ->1, <g5 ->5, else 10
        self.max_doc_sents = int(sc.get("max_doc_sents", 60))

        self.nlp = spacy.blank("en")
        self.nlp.add_pipe("sentencizer")
        dev = cfg["relevance"].get("device", "cuda")
        self.enc = SentenceTransformer(cfg["relevance"]["model"], device=dev)

        self._day_key = None
        self._S = None            # (n_sents, 384)
        self._owner_slices = None  # doc_id -> (start, end) into _S
        self._sent_texts = None
        self._qvec: dict[str, np.ndarray] = {}
        self._seed_init: dict[str, tuple[np.ndarray, list[str]]] = {}

    # ---- question setup ----
    # NB: cache MUST be keyed by question TEXT — qids ("q_1"...) repeat across topics;
    # keying by qid scored 7 of 8 topics against the wrong questions (has-ans 0.43→0.05).
    def qvec(self, qid: str, question: str) -> np.ndarray:
        if question not in self._qvec:
            self._qvec[question] = self.enc.encode([question], normalize_embeddings=True)[0]
        return self._qvec[question]

    def set_seeds(self, qid: str, question: str, seed_texts: list[str]) -> None:
        """§10.A anchoring: blend question vector with seed-sentence centroid; stash the
        tau-passing seed sentences as the question's initial memory."""
        pq = self.enc.encode([question], normalize_embeddings=True)[0]
        sents = []
        for t in seed_texts:
            sents += self._sentencize(t)
        if not sents:
            self._qvec[qid] = pq
            return
        S = self.enc.encode(sents, normalize_embeddings=True, batch_size=256)
        top_idx = np.argsort(-(S @ pq))[:10]
        cen = S[top_idx].mean(axis=0)
        cen /= (np.linalg.norm(cen) + 1e-9)
        v = self.seed_alpha * pq + (1 - self.seed_alpha) * cen
        self._qvec[question] = v / (np.linalg.norm(v) + 1e-9)   # keyed by TEXT (qids collide)
        m = (S @ self._qvec[question]) >= self.tau
        self._seed_init[question] = (S[m], [sents[i] for i in np.where(m)[0]])

    def init_memory(self, question: str, mem: SentenceMemory) -> None:
        if question in self._seed_init:
            mem.add(*self._seed_init[question])

    # ---- per-day index (shared across all questions/topics that day) ----
    def _sentencize(self, text: str) -> list[str]:
        doc = self.nlp(clean_text(text)[:20000])
        out = [s.text.strip() for s in doc.sents if 20 <= len(s.text.strip()) <= 600]
        return out[: self.max_doc_sents]

    def prepare_day(self, day_docs) -> None:
        key = (len(day_docs), day_docs[0].id if day_docs else "", day_docs[-1].id if day_docs else "")
        if key == self._day_key:
            return
        texts, slices, pos = [], {}, 0
        for d in day_docs:
            sents = self._sentencize(d.text)
            slices[d.id] = (pos, pos + len(sents))
            texts += sents
            pos += len(sents)
        self._S = self.enc.encode(texts, normalize_embeddings=True, batch_size=512) \
            if texts else np.zeros((0, 384), dtype=np.float32)
        self._sent_texts = texts
        self._owner_slices = slices
        self._day_key = key

    # ---- core scoring for one question over the prepared day ----
    def score_question(self, qid: str, question: str, mem: SentenceMemory):
        """-> list of (doc_id, gain, cand_embs, cand_texts) with gain>0, gain desc,
        applying within-day keep-first (docs in index order = publication order proxy)."""
        qv = self.qvec(qid, question)
        rel = self._S @ qv if len(self._S) else np.zeros(0, dtype=np.float32)
        out = []
        work_extra = np.zeros((0, 384), dtype=np.float32)
        for did, (a, b) in self._owner_slices.items():
            if b <= a:
                continue
            r = rel[a:b]
            m = r >= self.tau
            if not m.any():
                continue
            embs = self._S[a:b][m]
            sims = mem.max_sim(embs, extra=work_extra)
            novel = sims < self.nu
            gain = float((r[m] * novel).sum())
            if gain <= 0:
                continue
            cand_embs = embs[novel]
            cand_texts = [self._sent_texts[a:b][i] for i in np.where(m)[0][novel]]
            out.append((did, gain, cand_embs, cand_texts))
            work_extra = np.vstack([work_extra, cand_embs])   # keep-first within the day
        out.sort(key=lambda x: -x[1])
        return out

    def bin_gain(self, gain: float) -> float:
        g1, g5 = self.bins
        return 1.0 if gain < g1 else 5.0 if gain < g5 else 10.0

    def close(self) -> None:          # harness contract (rel.close())
        pass


def decide_question_sentgain(cfg, engine: SentGainEngine, memory, qid, question_text, day_docs):
    """Sentence-gain decision, mirroring policy.decide_question's contract."""
    from .policy import QuestionDecision
    from .scorers import Candidate

    engine.prepare_day(day_docs)
    if not hasattr(memory, "sent_mem"):
        memory.sent_mem = SentenceMemory(cap=engine.mem_cap)
        engine.init_memory(question_text, memory.sent_mem)
    mem = memory.sent_mem

    scored = engine.score_question(qid, question_text, mem)
    day_max = scored[0][1] if scored else 0.0
    z = mem.bg_z(day_max)
    mem.bg_update(day_max)                       # background includes nil days

    # z-gate only once enough background history exists (warmup: fall back to gamma-only)
    z_ok = (not engine.use_zscore) or mem.bg_n < 8 or z >= engine.z_thr
    fire = day_max >= engine.gamma and z_ok
    if not scored or not fire:
        return QuestionDecision(qid, question_text, [])

    reported, pend_embs, pend_texts = [], [], []
    cap = int(cfg["policy"]["max_docs_per_question"])
    for did, gain, cand_embs, cand_texts in scored[:cap]:
        if gain < engine.gamma:                   # truncate below the fire bar
            break
        c = Candidate(doc_id=did, text="")
        c.relevance = gain
        c.novelty = 1.0
        c.combined = engine.bin_gain(gain)        # graded bin (placeholder until Phase 3)
        c.extra["sent_gain"] = gain
        reported.append(c)
        pend_embs.append(cand_embs)
        pend_texts += cand_texts
    if not reported:
        return QuestionDecision(qid, question_text, [])
    dec = QuestionDecision(qid, question_text, reported, best_combined=reported[0].combined)
    dec.pending_sents = (np.vstack(pend_embs) if pend_embs else np.zeros((0, 384), dtype=np.float32),
                         pend_texts)
    return dec
