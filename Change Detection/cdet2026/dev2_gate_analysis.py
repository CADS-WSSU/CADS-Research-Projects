"""Instrument WHY the model is silent on dev2 has-answer days: for each has-answer
(topic, question, day), find the ground-truth doc(s) among that day's candidates and
record exactly where each died in our pipeline —

  RELEVANCE gate:
     - PREFILTER miss : GT doc not in the cosine top-`prefilter_n` (reranker never saw it)
     - RERANKER low   : GT in top-N but reranker prob < threshold and not rescued by ensemble
  NOVELTY gate:
     - RESTATEMENT    : GT passed relevance but novelty < threshold (filtered as not-new)
  FOUND: GT passed both gates and was reported.

This replaces the assumption "later-day silence = correct restatement" with data: it tells
us whether the low has-answer score is a RECALL problem (relevance gate) or a
restatement-filtering effect (novelty gate). Faithfully mirrors policy.decide_question.

Run on the VM:  python -m cdet2026.dev2_gate_analysis
"""
from __future__ import annotations

from collections import defaultdict

from cdet_api.models import Document, db

from .config import load_config, load_topics
from .memory import QuestionMemory
from .policy import commit_to_memory, decide_question
from .query import build_relevance_query
from .scorers import Candidate, build_novelty_scorer, build_relevance_scorer

TOPICS_FILE = "data/dev-topics-all-docs.jsonl"


def classify_gt(cfg, rel, nov, mem, qtext, rq, day_docs, relset):
    """Return (label, detail) for the best ground-truth doc's fate, mirroring decide_question's
    gates. Does NOT mutate memory (caller uses decide_question for the real decision)."""
    rel_thr = float(cfg["relevance"]["threshold"])
    nov_thr = float(cfg["novelty"]["threshold"])
    ens_k = int(cfg["relevance"].get("ensemble_cos_rank", 0))
    ens_min = float(cfg["relevance"].get("ensemble_min_prob", rel_thr))
    prefilter_n = int(cfg["relevance"].get("prefilter_n", 20))
    top_k = int(cfg["policy"].get("novelty_top_k", 50))

    candidates = [Candidate(doc_id=d.id, text=d.text, date=getattr(d, "date", "")) for d in day_docs]
    rel.score_day(rq or qtext, candidates)

    def passes(c):
        if c.relevance >= rel_thr:
            return True
        if ens_k <= 0 or c.relevance < ens_min:
            return False
        return c.extra.get("cos_rank", 10**9) <= ens_k or c.extra.get("bm25_rank", 10**9) <= ens_k

    gt = [c for c in candidates if c.doc_id in relset]
    if not gt:
        return "GT_NOT_IN_DAY", {}                      # GT doc absent from the day's dump (shouldn't happen)
    gt_best = max(gt, key=lambda c: c.relevance)
    gt_cos_rank = min((c.extra.get("cos_rank", 10**9) for c in gt), default=10**9)

    # relevance gate
    if not any(passes(c) for c in gt):
        if gt_cos_rank > prefilter_n:
            return "REL_PREFILTER_MISS", {"cos_rank": gt_cos_rank, "reranker": round(gt_best.relevance, 3)}
        return "REL_RERANKER_LOW", {"cos_rank": gt_cos_rank, "reranker": round(gt_best.relevance, 3)}

    # GT passed relevance -> replicate the novelty loop to get GT's novelty vs memory + earlier-today
    rel_pass = [c for c in candidates if passes(c)]
    rel_pass.sort(key=lambda c: c.relevance, reverse=True)
    rel_pass = rel_pass[:top_k]
    nov.attach_features(rel_pass)
    work_embs, work_terms, work_ents = mem.working_copy()
    gt_ids = {c.doc_id for c in gt}
    gt_novelty = None
    for c in sorted(rel_pass, key=lambda c: c.date):
        c.novelty = nov.novelty_against(c.embedding, c.extra["terms"], c.extra["entities"],
                                        work_embs, work_terms, work_ents)
        if c.doc_id in gt_ids and gt_novelty is None:
            gt_novelty = c.novelty
        if c.novelty >= nov_thr:
            work_embs.append(c.embedding); work_terms |= c.extra["terms"]; work_ents |= c.extra["entities"]
    if gt_novelty is None:
        return "REL_TRUNCATED_TOPK", {"reranker": round(gt_best.relevance, 3)}   # passed rel but below top_k
    if gt_novelty < nov_thr:
        return "NOV_RESTATEMENT", {"novelty": round(gt_novelty, 3), "reranker": round(gt_best.relevance, 3)}
    return "FOUND", {"novelty": round(gt_novelty, 3), "reranker": round(gt_best.relevance, 3)}


def main():
    cfg = load_config()
    topics = load_topics(TOPICS_FILE)
    db.connect(reuse_if_open=True)

    qrel = {}
    for t in topics:
        for q in t["questions"]:
            per_day = defaultdict(set)
            for did in q["rel_docs"]:
                r = Document.get_or_none(Document.id == did)
                if r:
                    per_day[r.day].add(did)
            qrel[(t["tid"], q["qid"])] = dict(per_day)

    rel = build_relevance_scorer(cfg)
    nov = build_novelty_scorer(cfg)
    daydocs = {}

    counts = defaultdict(int)
    counts_first = defaultdict(int)
    counts_later = defaultdict(int)
    details = []
    for t in topics:
        for q in t["questions"]:
            key = (t["tid"], q["qid"])
            mem = QuestionMemory()
            for i, day in enumerate(sorted(qrel[key])):
                relset = qrel[key][day]
                if day not in daydocs:
                    daydocs[day] = list(Document.select().where(Document.day == day))
                rq = build_relevance_query(cfg, t, q["question"])
                label, detail = classify_gt(cfg, rel, nov, mem, q["question"], rq, daydocs[day], relset)
                counts[label] += 1
                (counts_first if i == 0 else counts_later)[label] += 1
                details.append({"tid": t["tid"], "qid": q["qid"], "day": day, "first": i == 0,
                                "label": label, **detail})
                # advance memory exactly as the real run would
                dec = decide_question(cfg, rel, nov, mem, q["qid"], q["question"], daydocs[day], relevance_query=rq)
                if dec.fired:
                    commit_to_memory(mem, dec)
    rel.close()

    total = sum(counts.values())
    order = ["FOUND", "REL_PREFILTER_MISS", "REL_RERANKER_LOW", "REL_TRUNCATED_TOPK",
             "NOV_RESTATEMENT", "GT_NOT_IN_DAY"]
    print(f"\n=== dev2 gate attribution — {total} has-answer units ===")
    print(f"{'outcome':22} {'all':>10} {'first-day':>12} {'later-day':>12}")
    for k in order:
        if counts.get(k):
            print(f"{k:22} {counts[k]:>5} ({100*counts[k]//total:>3}%) {counts_first.get(k,0):>8} {counts_later.get(k,0):>12}")
    rel_miss = counts["REL_PREFILTER_MISS"] + counts["REL_RERANKER_LOW"] + counts["REL_TRUNCATED_TOPK"]
    print(f"\nSILENCE CAUSE:  relevance-gate (recall) = {rel_miss} ({100*rel_miss//total}%)   "
          f"novelty-gate (restatement) = {counts['NOV_RESTATEMENT']} ({100*counts['NOV_RESTATEMENT']//total}%)")
    print(f"FOUND (passed both) = {counts['FOUND']} ({100*counts['FOUND']//total}%)")

    import json
    with open("dev2_gate_detail.jsonl", "w") as f:
        for d in details:
            f.write(json.dumps(d) + "\n")
    print("per-unit detail -> dev2_gate_detail.jsonl")


if __name__ == "__main__":
    main()
