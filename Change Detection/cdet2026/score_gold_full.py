"""Nil-INCLUSIVE evaluation on the gold dataset — the task-faithful metric.

Unlike score_gold_run.py (has-answer days only), this scores the model over BOTH
has-answer days AND nil days (no relevant doc), where the correct action is SILENCE.
A nil unit is any (topic, question, day) not in the gold qrels: an empty ranking scores
1.0 (silence rewarded), firing is penalized. References (BM25/bi-encoder) always return
top-N, so they are penalized on every nil day — this is where our model's silence wins.

Scope (fast, sampled): for each question, all has-answer days + a sample of nil days
drawn from the topic's ACTIVE span (first..last relevant day) — the realistic interspersed
nil days. Memory accumulates over the question's days in date order.

Reports OVERALL (all units, silence-dominated), HAS-ANSWER (detection quality), and the
nil-day SILENCE rate, for our model vs references — all with graded gains.

Run on the VM:  python -m cdet2026.score_gold_full [--nil-per-q 40] [--cos-rescue N] [--skip-refs]
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
from collections import defaultdict
from pathlib import Path

import numpy as np
from cdet_api.models import Document, db

from .config import ROOT, load_config
from .embeddings import Embedder
from .memory import QuestionMemory
from .metrics import score_ranking
from .policy import commit_to_memory, decide_question
from .query import build_relevance_query
from .scorers import build_novelty_scorer, build_relevance_scorer
from .text_utils import tokenize

METRICS = ["RR_prime", "RBP_prime", "NDCG_prime", "AP_prime"]
DS = ROOT / "gold_testset" / "dataset"


def load_gold():
    gold = defaultdict(dict)
    for l in (DS / "qrels_graded.jsonl").read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            gold[(r["topic"], r["qid"], r["day"])][r["doc_id"]] = float(r["gain"])
    topics = [json.loads(l) for l in (DS / "topics.jsonl").read_text().splitlines() if l.strip()]
    return gold, topics


def collection_days():
    con = sqlite3.connect(str(ROOT / "docs.db"))
    days = sorted(r[0] for r in con.execute("SELECT day FROM days"))
    con.close()
    return days


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nil-per-q", type=int, default=40)
    ap.add_argument("--cos-rescue", type=int, default=None)
    ap.add_argument("--ref-topn", type=int, default=10)
    ap.add_argument("--skip-refs", action="store_true")
    ap.add_argument("--dataset", default=str(ROOT / "gold_testset" / "dataset"),
                    help="dataset dir with qrels_graded.jsonl + topics.jsonl (e.g. .../dataset_v2)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    global DS
    DS = Path(args.dataset)

    cfg = load_config()
    if args.cos_rescue is not None:
        cfg["relevance"]["ensemble_cos_rescue_rank"] = args.cos_rescue
    gold, topics = load_gold()
    db.connect(reuse_if_open=True)
    alldays = collection_days()
    rng = random.Random(args.seed)

    qtext = {(t["tid"], q["qid"]): q["question"] for t in topics for q in t["questions"]}
    tmap = {t["tid"]: t for t in topics}

    # has-answer days per question
    hasans = defaultdict(set)
    for (tid, qid, day) in gold:
        hasans[(tid, qid)].add(day)

    # units per question = has-answer + sampled nil days within the active span
    units_by_q = {}
    for key, hdays in hasans.items():
        lo, hi = min(hdays), max(hdays)
        span_nil = [d for d in alldays if lo <= d <= hi and d not in hdays]
        nils = rng.sample(span_nil, min(args.nil_per_q, len(span_nil)))
        units_by_q[key] = sorted([(d, False) for d in hdays] + [(d, True) for d in nils])

    daydocs = {}
    def docs_for(day):
        if day not in daydocs:
            daydocs[day] = list(Document.select().where(Document.day == day))
        return daydocs[day]

    # ---- our model ----
    rel = build_relevance_scorer(cfg); nov = build_novelty_scorer(cfg)
    model_rank = {}
    for (tid, qid), units in units_by_q.items():
        mem = QuestionMemory()
        t = tmap[tid]; q_txt = qtext[(tid, qid)]
        rq = build_relevance_query(cfg, t, q_txt)
        for day, _isnil in units:
            dec = decide_question(cfg, rel, nov, mem, qid, q_txt, docs_for(day), relevance_query=rq)
            model_rank[(tid, qid, day)] = [c.doc_id for c in dec.reported]
            if dec.fired:
                commit_to_memory(mem, dec)
    rel.close()

    # ---- references ----
    bm25_rank, bienc_rank = {}, {}
    if not args.skip_refs:
        from rank_bm25 import BM25Okapi
        # reuse the SAME cached bge-small embedder our model populated (emb.sqlite keyed by
        # doc id) -> reference doc embeddings become cache hits, no re-encoding.
        emb = Embedder(cfg["relevance"]["model"], cfg["relevance"]["device"],
                       cfg["paths"]["embeddings_cache"] + "/emb.sqlite",
                       batch_size=int(cfg["relevance"].get("batch_size", 64)))
        dcache = {}
        for (tid, qid), units in units_by_q.items():
            q_txt = qtext[(tid, qid)]
            qv = emb.encode_query(q_txt)
            qtok = tokenize(q_txt)
            for day, _ in units:
                docs = docs_for(day)
                if day not in dcache:
                    ids = [d.id for d in docs]
                    embs = emb.encode_docs(ids, [d.text for d in docs])   # cached by doc id
                    dcache[day] = (embs, BM25Okapi([tokenize(d.text) for d in docs]), ids)
                embs, bm, ids = dcache[day]
                bienc_rank[(tid, qid, day)] = [ids[i] for i in np.argsort(-(embs @ qv))[: args.ref_topn]]
                bm25_rank[(tid, qid, day)] = [ids[i] for i in np.argsort(-np.asarray(bm.get_scores(qtok)))[: args.ref_topn]]
        emb.close()

    # ---- score with graded gains, split overall / has-answer / nil ----
    def score(ranks):
        ov = defaultdict(float); ha = defaultdict(float)
        n = nha = nil_n = nil_silent = 0
        for (tid, qid), units in units_by_q.items():
            for day, isnil in units:
                unit = (tid, qid, day); gmap = gold.get(unit, {})
                ranking = ranks.get(unit, [])
                gains = [gmap.get(d, 0.0) for d in ranking]
                m = score_ranking(gains, list(gmap.values()))
                for k in METRICS:
                    ov[k] += m[k]
                n += 1
                if gmap:
                    for k in METRICS:
                        ha[k] += m[k]
                    nha += 1
                else:
                    nil_n += 1
                    if not ranking:
                        nil_silent += 1
        return ({k: ov[k] / n for k in METRICS}, {k: ha[k] / nha for k in METRICS},
                nil_silent / nil_n if nil_n else float("nan"), n, nha, nil_n)

    providers = {"our_model": model_rank}
    if not args.skip_refs:
        providers["ref_bm25"] = bm25_rank
        providers["ref_biencoder"] = bienc_rank
    res = {name: score(r) for name, r in providers.items()}
    _, _, _, n, nha, nil_n = res["our_model"]

    cfgline = (f"cos_rescue={cfg['relevance'].get('ensemble_cos_rescue_rank',0)} "
               f"restat_cap={cfg['policy'].get('restatement_gain_cap',1.0)} "
               f"method={cfg['relevance'].get('method')} nil_per_q={args.nil_per_q}")
    print(f"\n=== NIL-INCLUSIVE gold scoring ({cfgline}) ===")
    print(f"units={n}  has-answer={nha}  nil={nil_n}  ({100*nil_n//n}% nil)")
    print(f"\n{'provider':16}{'metric-set':12}{'RR':>8}{'RBP':>8}{'NDCG':>8}{'AP':>8}{'nil-silence':>13}")
    for name in providers:
        ov, ha, sil, *_ = res[name]
        print(f"{name:16}{'overall':12}{ov['RR_prime']:>8.3f}{ov['RBP_prime']:>8.3f}{ov['NDCG_prime']:>8.3f}{ov['AP_prime']:>8.3f}{sil:>13.3f}")
        print(f"{'':16}{'has-answer':12}{ha['RR_prime']:>8.3f}{ha['RBP_prime']:>8.3f}{ha['NDCG_prime']:>8.3f}{ha['AP_prime']:>8.3f}")
    print("\noverall = ALL units incl nil (silence rewarded); has-answer = detection quality; "
          "nil-silence = fraction of nil days correctly silent (references always fire -> ~0).")
    if args.out:
        json.dump({"config": cfgline, "n": n, "has_answer": nha, "nil": nil_n,
                   "results": {k: {"overall": v[0], "has_answer": v[1], "nil_silence": v[2]}
                               for k, v in res.items()}}, open(args.out, "w"), indent=2)


if __name__ == "__main__":
    main()
