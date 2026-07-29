"""Gold-anchored Stage-B (newsworthiness) proxy, to triangulate the colleague's
embedding-derived (silver) Stage-B labels.

Three independent newsworthiness signals per question, decreasing in "goldness":
  1. TOPIC-level pure gold — a topic is newsworthy on any day a NIST-gold relevant doc
     for it appears (qrels.jsonl: relevance + publication day). Zero embeddings.
  2. Gold docs, first-appearance — a question's first-newsworthy day = the earliest gold
     day among its relevant docs (gold day + gold relevance; routing inherited).
  3. Gold docs, RERANKER-routed — same, but a gold doc only counts for a question if our
     CROSS-ENCODER (reranker, cached from Stage-A) says it covers the question (prob >= tau).
     This is an INDEPENDENT matcher from the colleague's bi-encoder, so agreement between
     this and the silver label is real triangulation (different model families).

Output: per-question table of silver vs gold-anchored first-newsworthy day + an agreement
report = a data-driven reliability estimate for the silver Stage-B labels.

Run:  python -m cdet2026.stageB_gold
"""
from __future__ import annotations

import json
from collections import defaultdict

from .config import ROOT, load_config
from .scorers.reranker_relevance import RerankScoreCache, _qhash

DATA = ROOT / "ragtime25_english"
TAU = 0.10  # reranker prob above which a gold doc "covers" a question


def main():
    cfg = load_config()
    cache = RerankScoreCache(cfg["paths"]["embeddings_cache"] + "/rerank.sqlite")

    doc_day, doc_grade = {}, {}
    for l in open(DATA / "qrels.jsonl"):
        d = json.loads(l)
        doc_day[d["doc_id"]] = d["day"]; doc_grade[d["doc_id"]] = d["rel_grade"]
    topics = [json.loads(l) for l in open(DATA / "topics.jsonl")]

    # 1) topic-level pure-gold newsworthy days
    topic_days = {}
    for d in (json.loads(l) for l in open(DATA / "qrels.jsonl")):
        topic_days.setdefault(d["topic_id"], {}).setdefault(d["day"], []).append(d["rel_grade"])

    out_rows = []
    agree_exact = agree_7d = on_gold_day = total = covered = 0
    rr_missing = 0
    for t in topics:
        tid = t["tid"]; tnum = tid.split("_")[1]
        gold_day_set = set(topic_days.get(tnum, {}))
        for q in t["questions"]:
            qdocs = [d for d in q.get("rel_docs", []) if d in doc_day]
            if not qdocs:
                continue
            total += 1
            silver = q.get("newsworthy_day")
            # signal 2: first appearance of any gold doc routed to q
            first_appear = min(doc_day[d] for d in qdocs)
            # signal 3: reranker-routed first appearance
            qh = _qhash(q["question"])
            probs = cache.get_many(qh, qdocs)
            rr_missing += len(qdocs) - len(probs)
            covered_docs = [d for d in qdocs if probs.get(d, 0.0) >= TAU]
            rr_gold = min((doc_day[d] for d in covered_docs), default=None)
            if rr_gold:
                covered += 1
            # agreement: silver vs reranker-routed gold
            if silver and rr_gold:
                if silver == rr_gold:
                    agree_exact += 1
                from datetime import date
                ds = date.fromisoformat(silver); dg = date.fromisoformat(rr_gold)
                if abs((ds - dg).days) <= 7:
                    agree_7d += 1
            if silver in gold_day_set:
                on_gold_day += 1
            out_rows.append({
                "tid": tid, "qid": q["qid"],
                "silver_newsworthy_day": silver,
                "gold_first_appearance": first_appear,
                "reranker_gold_day": rr_gold,
                "n_gold_docs": len(qdocs), "n_reranker_covered": len(covered_docs),
                "max_grade": max(doc_grade[d] for d in qdocs),
            })

    with open(DATA / "question_newsworthy_gold.jsonl", "w") as f:
        for r in out_rows:
            f.write(json.dumps(r) + "\n")
    with open(DATA / "topic_newsworthy_gold.jsonl", "w") as f:
        for tnum, days in topic_days.items():
            for day, grades in sorted(days.items()):
                f.write(json.dumps({"topic_id": tnum, "day": day,
                                    "n_gold_docs": len(grades), "max_grade": max(grades)}) + "\n")

    print(f"questions with gold docs: {total}")
    print(f"  silver day falls on a topic-level gold day: {on_gold_day}/{total} = {on_gold_day/total:.2f}")
    print(f"  reranker-routed coverage (>= {TAU}): {covered}/{total} questions had >=1 covered gold doc")
    print(f"  cached reranker probs missing for {rr_missing} (q,doc) pairs (Stage-A recall not fully cached?)")
    if covered:
        print(f"  silver vs reranker-gold first-newsworthy day: exact={agree_exact}/{covered}={agree_exact/covered:.2f} "
              f"within-7d={agree_7d}/{covered}={agree_7d/covered:.2f}")
    print(f"\nwrote question_newsworthy_gold.jsonl ({len(out_rows)} rows) and topic_newsworthy_gold.jsonl")


if __name__ == "__main__":
    main()
