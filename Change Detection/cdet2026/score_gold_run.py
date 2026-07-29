"""Score OUR model and the reference retrieval methods (BM25, bi-encoder) against the
graded gold dataset (dataset/qrels_graded.jsonl), using the truncated ranking metrics
with GRADED gains (0/1/5/10).

- our_model: full policy (relevance gate + novelty + task-gain ordering + silence),
  run day-by-day over each question's gold days (memory accumulates in order).
- bm25 / bienc: rank the day's docs and return the top-N (no silence/novelty) — the
  organizers' reference style.

Scores each (topic, question, day) unit in the gold with graded gains, reports has-answer
means per metric, and our model's silence rate on has-answer days.

Run on the VM:  python -m cdet2026.score_gold_run [--cos-rescue N] [--ref-topn 10]
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from cdet_api.models import Document, db

from .config import ROOT, load_config
from .memory import QuestionMemory
from .metrics import score_ranking
from .policy import commit_to_memory, decide_question
from .query import build_relevance_query
from .scorers import build_novelty_scorer, build_relevance_scorer
from .text_utils import tokenize

METRICS = ["RR_prime", "RBP_prime", "NDCG_prime", "AP_prime"]
DS = ROOT / "gold_testset" / "dataset"


def load_gold():
    gold = defaultdict(dict)   # (tid,qid,day) -> {doc_id: gain}
    for l in (DS / "qrels_graded.jsonl").read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            gold[(r["topic"], r["qid"], r["day"])][r["doc_id"]] = float(r["gain"])
    topics = [json.loads(l) for l in (DS / "topics.jsonl").read_text().splitlines() if l.strip()]
    return gold, topics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cos-rescue", type=int, default=None, help="override ensemble_cos_rescue_rank")
    ap.add_argument("--ref-topn", type=int, default=10, help="reference methods return top-N")
    ap.add_argument("--skip-refs", action="store_true", help="score only our_model (references unchanged)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = load_config()
    if args.cos_rescue is not None:
        cfg["relevance"]["ensemble_cos_rescue_rank"] = args.cos_rescue
    gold, topics = load_gold()
    db.connect(reuse_if_open=True)

    # units grouped by question, in day order (for memory)
    units_by_q = defaultdict(list)
    for (tid, qid, day) in gold:
        units_by_q[(tid, qid)].append(day)
    for k in units_by_q:
        units_by_q[k].sort()
    qtext = {(t["tid"], q["qid"]): q["question"] for t in topics for q in t["questions"]}
    tmap = {t["tid"]: t for t in topics}

    daydocs = {}
    def docs_for(day):
        if day not in daydocs:
            daydocs[day] = list(Document.select().where(Document.day == day))
        return daydocs[day]

    # ---- our model ----
    rel = build_relevance_scorer(cfg); nov = build_novelty_scorer(cfg)
    model_rank, fired_on = {}, {}
    for (tid, qid), days in units_by_q.items():
        mem = QuestionMemory()
        t = tmap[tid]; q_txt = qtext[(tid, qid)]
        rq = build_relevance_query(cfg, t, q_txt)
        for day in days:
            dec = decide_question(cfg, rel, nov, mem, qid, q_txt, docs_for(day), relevance_query=rq)
            model_rank[(tid, qid, day)] = [c.doc_id for c in dec.reported]
            fired_on[(tid, qid, day)] = dec.fired
            if dec.fired:
                commit_to_memory(mem, dec)
    rel.close()

    # ---- reference methods (bm25, bi-encoder) ----
    bm25_rank, bienc_rank = {}, {}
    if args.skip_refs:
        pass
    else:
      from sentence_transformers import SentenceTransformer
      enc = SentenceTransformer(cfg["relevance"]["model"], device=cfg["relevance"]["device"])
      day_cache = {}
      for (tid, qid), days in units_by_q.items():
        q_txt = qtext[(tid, qid)]
        qv = enc.encode([q_txt], normalize_embeddings=True)[0]
        qtok = tokenize(q_txt)
        for day in days:
            docs = docs_for(day)
            if day not in day_cache:
                from rank_bm25 import BM25Okapi
                embs = enc.encode([d.text for d in docs], normalize_embeddings=True, batch_size=128)
                day_cache[day] = (embs, BM25Okapi([tokenize(d.text) for d in docs]), [d.id for d in docs])
            embs, bm, ids = day_cache[day]
            cos = embs @ qv
            bienc_rank[(tid, qid, day)] = [ids[i] for i in np.argsort(-cos)[: args.ref_topn]]
            bms = np.asarray(bm.get_scores(qtok))
            bm25_rank[(tid, qid, day)] = [ids[i] for i in np.argsort(-bms)[: args.ref_topn]]

    # ---- score all providers with GRADED gains ----
    def score(ranks):
        acc = defaultdict(float); n = 0
        for unit, gmap in gold.items():
            ranking = ranks.get(unit, [])
            gains = [gmap.get(d, 0.0) for d in ranking]
            m = score_ranking(gains, list(gmap.values()))
            for k in METRICS:
                acc[k] += m[k]
            n += 1
        return {k: acc[k] / n for k in METRICS}, n

    providers = {"our_model": model_rank}
    if not args.skip_refs:
        providers["ref_bm25"] = bm25_rank
        providers["ref_biencoder"] = bienc_rank
    res = {name: score(r)[0] for name, r in providers.items()}
    n_units = len(gold)
    fired = sum(1 for v in fired_on.values() if v)

    cfgline = f"cos_rescue={cfg['relevance'].get('ensemble_cos_rescue_rank',0)} " \
              f"restat_cap={cfg['policy'].get('restatement_gain_cap',1.0)} method={cfg['relevance'].get('method')}"
    print(f"\n=== GRADED gold scoring — {n_units} has-answer units ({cfgline}) ===")
    print(f"{'provider':16}{'RR_prime':>10}{'RBP_prime':>11}{'NDCG_prime':>12}{'AP_prime':>10}")
    for name in providers:
        r = res[name]
        print(f"{name:16}{r['RR_prime']:>10.3f}{r['RBP_prime']:>11.3f}{r['NDCG_prime']:>12.3f}{r['AP_prime']:>10.3f}")
    print(f"\nour_model fired on {fired}/{n_units} has-answer units ({100*fired//n_units}%)  "
          f"(silent on {n_units-fired})")
    print("note: RBP' can exceed 1 under graded gains (rate). references return top-%d each day." % args.ref_topn)
    if args.out:
        json.dump({"config": cfgline, "n_units": n_units, "results": res,
                   "fired": fired}, open(args.out, "w"), indent=2)


if __name__ == "__main__":
    main()
