"""Metric-aware decision policy — the core of the baseline.

Why these rules (from the truncated-ranking metric, see plan):
- The terminal document scores an empty ranking 1.0 when nothing is relevant, so the
  system must STAY SILENT unless there is a genuine update. We fire a question on a day
  only if at least one doc clears BOTH the relevance and novelty thresholds.
- Trailing non-relevant items strictly lower the score, so we never pad toward 100: we
  order accepted docs by combined score and truncate where it falls below threshold.
- Graded gains reward the best item at rank 0, so we order docs by predicted gain
  (combined score) and order fired questions by their best doc's score.

This module is pure decision logic over already-scored candidates; the day loop owns
I/O and memory persistence.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .memory import QuestionMemory
from .scorers import Candidate, NoveltyScorer, RelevanceScorer


@dataclass
class QuestionDecision:
    qid: str
    question_text: str
    reported: list[Candidate]          # ordered by combined desc, truncated; [] = silent
    best_combined: float = 0.0
    pending_sents: object = None       # sentgain path: (embs, texts) to commit on fire
    rank_key: float | None = None      # cross-question ranking key (z-score, idea B); None -> best_combined

    @property
    def fired(self) -> bool:
        return bool(self.reported)


def decide_question(
    cfg: dict,
    rel_scorer: RelevanceScorer,
    nov_scorer: NoveltyScorer,
    memory: QuestionMemory,
    qid: str,
    question_text: str,
    day_docs,
    relevance_query: str | None = None,
) -> QuestionDecision:
    """Decide what (if anything) to report for one question on one day's documents.

    Gate vs order (matches the task's gain = newsworthiness, not pure relevance):
      - relevance (reranker) GATES candidacy: is this doc on-topic at all (gain>0)?
      - novelty GATES firing (is there genuinely new info?) AND drives ORDER: among
        relevant docs the most NEW/vital ranks first (predicted gain = combined score).
        On a question's first day memory is empty so novelty is uniform and relevance
        breaks ties; on later days novelty promotes updates over restatements.
      - within-day dedup ("keep first"): same-day docs are judged in publication-time
        order against memory PLUS docs already accepted earlier today, so a later
        near-duplicate of an earlier same-day doc is dropped — we keep the first.
    """
    # single-stage sentence-gain path (SENTENCE_GAIN_PLAN): rel_scorer is the engine.
    if cfg["relevance"].get("method") == "sentgain":
        from .sentgain import decide_question_sentgain
        return decide_question_sentgain(cfg, rel_scorer, memory, qid, question_text, day_docs)

    rel_thr = float(cfg["relevance"]["threshold"])
    nov_thr = float(cfg["novelty"]["threshold"])
    cap = int(cfg["policy"]["max_docs_per_question"])
    # Task gain (TREC 0/1/5/10) = relevance AND novelty combined. A restatement of
    # already-reported info is "on topic but not an update today" -> capped low.
    # restatement_gain_cap = 1.0 reports restatements at gain 1 (faithful to the scale);
    # set 0.0 to stay SILENT on restatements (report only genuine updates).
    restat_cap = float(cfg["policy"].get("restatement_gain_cap", 1.0))

    candidates = [Candidate(doc_id=d.id, text=d.text, date=getattr(d, "date", "")) for d in day_docs]
    if not candidates:
        return QuestionDecision(qid, question_text, [])

    # 1) Relevance gate: keep docs the reranker says are on-topic. Optional rank-aware
    #    ensemble: also admit a top-cosine doc with a MODERATE reranker score (recovers
    #    rank-1 gold docs the reranker undervalues, without lowering the bar globally).
    rel_scorer.score_day(relevance_query or question_text, candidates)
    ens_k = int(cfg["relevance"].get("ensemble_cos_rank", 0))
    ens_min = float(cfg["relevance"].get("ensemble_min_prob", rel_thr))
    # #2 pure cosine rescue: admit a very-top-cosine doc regardless of the reranker floor.
    # Diagnosis: 80% of recall misses are cos_rank<=3 with reranker~0.009, so the reranker
    # floor (ens_min) blocks them; this recovers them (at some silence cost — tune on gold).
    cos_rescue = int(cfg["relevance"].get("ensemble_cos_rescue_rank", 0))

    def _passes(c) -> bool:
        if c.relevance >= rel_thr:
            return True
        if cos_rescue > 0 and c.extra.get("cos_rank", 10**9) <= cos_rescue:
            return True
        if ens_k <= 0 or c.relevance < ens_min:
            return False
        # top-cosine OR (A1 fusion) top-BM25 in the day, with a reranker floor for silence
        return c.extra.get("cos_rank", 10**9) <= ens_k or c.extra.get("bm25_rank", 10**9) <= ens_k

    rel_pass = [c for c in candidates if _passes(c)]

    # LLM RESCUE (Job A): content-judge the top-cosine docs the reranker rejected.
    # Runs on every day (nil days included — the judge sees only the doc, not the day);
    # silence is preserved iff the judge grades nil-day topical noise as 0.
    rc = cfg["relevance"]
    if rc.get("llm_rescue", False):
        from .scorers.llm_relevance import LLMJudge
        judge = LLMJudge.get(cfg, "rescue")
        confirm = LLMJudge.get(cfg, "grade") if rc.get("llm_rescue_confirm", True) else None
        K = int(rc.get("llm_rescue_top_k", 3))
        admit = int(rc.get("llm_rescue_admit_gain", 1))
        t_cos = float(rc.get("llm_rescue_trigger_cos", 0.0))   # Tier-2 budget trigger (0 = always)
        passed = {c.doc_id for c in rel_pass}
        for c in candidates:
            if c.doc_id in passed or c.extra.get("cos_rank", 10**9) > K:
                continue
            if c.extra.get("dense_cos", 0.0) < t_cos:
                continue
            g = judge.grade(question_text, c.text)         # tier-1: cheap volume judge (Sonnet)
            if g < admit:
                continue
            # tier-2 confirmation: an INDEPENDENT stronger judge (Opus) must also admit.
            # Two-model agreement guards silence — a topically-plausible-but-doesn't-answer
            # doc that Sonnet over-rates is knocked back here. Opus's grade is authoritative.
            if confirm is not None:
                g = confirm.grade(question_text, c.text)
                if g < admit:
                    continue
            c.extra["llm_gain"] = g
            c.relevance = max(c.relevance, g / 10.0)
            rel_pass.append(c)

    # idea B: per-question background calibration. Signal = the day's PEAK relevance for
    # this question (post-rescue). z vs the question's own past background makes firing and
    # ranking scale-invariant across questions. z uses PAST days only; fold today in after.
    pcfg = cfg["policy"]
    z_rank = pcfg.get("question_zscore_rank", False)
    z_gate = pcfg.get("question_zscore_gate", False)
    z = None
    if z_rank or z_gate:
        day_signal = max((c.relevance for c in candidates), default=0.0)
        z = memory.zscore(day_signal, int(pcfg.get("zscore_min_bg", 8)))
        memory.update_bg(day_signal)

    if not rel_pass:
        return QuestionDecision(qid, question_text, [])  # correct silence: nothing relevant
    # Bound novelty/NER work to the top-K by relevance (deeper docs are never reported).
    top_k = int(cfg["policy"].get("novelty_top_k", 50))
    rel_pass.sort(key=lambda c: c.relevance, reverse=True)
    rel_pass = rel_pass[:top_k]

    # 2) Novelty: set each candidate's novelty vs memory + docs seen earlier today (the
    #    "today/new" dimension of the gain). Novel docs also update the within-day working
    #    memory so a later same-day near-duplicate reads as non-novel (keep-first).
    if hasattr(nov_scorer, "novelty_against"):
        nov_scorer.attach_features(rel_pass)
        work_embs, work_terms, work_ents = memory.working_copy()
        for c in sorted(rel_pass, key=lambda c: c.date):  # earliest published first
            c.novelty = nov_scorer.novelty_against(
                c.embedding, c.extra["terms"], c.extra["entities"], work_embs, work_terms, work_ents)
            if c.novelty >= nov_thr:
                work_embs.append(c.embedding)
                work_terms |= c.extra["terms"]; work_ents |= c.extra["entities"]
    else:  # fallback for a swapped-in novelty scorer without incremental support
        nov_scorer.score_day(memory, rel_pass)

    # idea C: corroboration / burst prior. Cluster today's relevant candidates by embedding
    # cosine; a candidate echoed by several distinct docs is a corroborated burst (vital),
    # a singleton is likely noise. cluster size (incl. self) is stored for boost/gate below.
    corr_boost = pcfg.get("corroboration_boost", False)
    corr_gate = pcfg.get("corroboration_gate", False)
    corr_min = int(pcfg.get("corr_min_cluster", 2))
    if (corr_boost or corr_gate) and rel_pass and all(getattr(c, "embedding", None) is not None for c in rel_pass):
        M = np.vstack([c.embedding for c in rel_pass])          # L2-normalized rows
        S = M @ M.T
        thr = float(pcfg.get("corr_cos_thr", 0.80))
        sizes = (S >= thr).sum(axis=1)                          # includes self
        for c, s in zip(rel_pass, sizes):
            c.extra["corr"] = int(s)

    # 3) Task gain = importance combined with novelty (TREC 0/1/5/10 semantics):
    #      novel      -> gain = importance (5/10 for a real update, 1 if only mildly on-topic)
    #      restatement-> gain = min(importance, restat_cap)  (on-topic but not new today)
    #    Importance is the relevance stage's 0/1/5/10 grade (LLM), else derived from the
    #    reranker/cosine relevance. All rel_pass docs are on-topic, so importance >= 1.
    # GRADE-AT-REPORT (Job B): every gate-passing doc gets a true LLM 0/1/5/10 grade
    # (rescued docs reuse their cached rescue grade). Volume = reported docs only.
    if rc.get("llm_grade_reported", False):   # Job B is its own lever (decoupled from rescue)
        from .scorers.llm_relevance import LLMJudge
        grader = LLMJudge.get(cfg, "grade")
        for c in rel_pass:
            if c.novelty >= nov_thr and "llm_gain" not in c.extra:
                c.extra["llm_gain"] = grader.grade(question_text, c.text)

    def _importance(c) -> float:
        g = c.extra.get("llm_gain")
        if g is not None:
            return float(g)
        r = c.relevance
        return 10.0 if r >= 0.8 else 5.0 if r >= 0.5 else 1.0

    corr_vital = int(pcfg.get("corr_vital_cluster", 4))
    for c in rel_pass:
        imp = _importance(c)
        if corr_boost:                                         # burst -> importance floor (only raises)
            cl = c.extra.get("corr", 1)
            if cl >= corr_vital:
                imp = max(imp, 10.0)
            elif cl >= corr_min:
                imp = max(imp, 5.0)
        c.combined = imp if c.novelty >= nov_thr else min(imp, restat_cap)

    reported = [c for c in rel_pass if c.combined >= 1.0]     # drop capped-to-0 restatements
    # corroboration gate: drop singleton reports (uncorroborated -> likely noise). Only
    # suppresses -> raises silence; risky for genuinely single-source updates, so it's a
    # separate opt-in lever (tested apart from the boost).
    if corr_gate:
        reported = [c for c in reported if c.extra.get("corr", 1) >= corr_min]
    if not reported:
        return QuestionDecision(qid, question_text, [])       # nothing to report today -> silent
    # z-gate (idea B): suppress firing if today is NOT anomalous vs this question's own
    # background (only suppresses -> raises silence; never adds a fire). Skipped during
    # cold-start warm-up (z is None) so early days keep the calibrated global behavior.
    if z_gate and z is not None and z < float(pcfg.get("question_z_thr", 2.0)):
        return QuestionDecision(qid, question_text, [])
    # order by task gain (most vital/new first); novelty then relevance break ties
    reported.sort(key=lambda c: (c.combined, c.novelty, c.relevance), reverse=True)
    reported = reported[:cap]
    rk = z if (z_rank and z is not None) else None
    return QuestionDecision(qid, question_text, reported, best_combined=reported[0].combined, rank_key=rk)


def order_questions(decisions: list[QuestionDecision]) -> list[QuestionDecision]:
    """Among fired questions, order by best doc score (most confident first) and assign
    a 0-based question rank. Returns only fired questions, ranked."""
    fired = [d for d in decisions if d.fired]
    # rank by the cross-question-comparable z-score when available (idea B); questions
    # still in cold-start warm-up (rank_key None) fall back to their raw best_combined.
    fired.sort(key=lambda d: (d.rank_key if d.rank_key is not None else d.best_combined), reverse=True)
    return fired


def commit_to_memory(memory: QuestionMemory, decision: QuestionDecision) -> None:
    """Add reported docs to the question's memory so later days see them as not-novel."""
    if decision.pending_sents is not None:                 # sentgain path: sentence memory
        embs, texts = decision.pending_sents
        memory.sent_mem.add(embs, texts)
        return
    for c in decision.reported:
        memory.add(c.doc_id, c.embedding, c.extra.get("terms", set()), c.extra.get("entities", set()))


def propose_new_questions(*args, **kwargs):
    """STUB (M3 leaves this intentionally unimplemented; plan defers it).

    Intent for a later milestone (M7, option 3): when a cluster of relevant documents
    on a day fits no existing question for a topic, an LLM could propose a new analytic
    question. The baseline never invents questions. Returns no proposals.
    """
    return []
