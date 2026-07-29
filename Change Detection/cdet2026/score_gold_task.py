"""TASK-FAITHFUL gold scoring — BOTH official evaluation types:

  (a) QUESTION-RANKING eval: per (topic, day), the ranking of questions (by
      question_rank) is scored with the truncated metrics using QUESTION-level gains.
      Question gain for (topic, q, day) = max doc gain in the gold that day (per the
      guidelines: a question gains relevance if relevant documents inform it that day);
      0 if none. Empty question ranking on a day where no question has gain -> 1.0.
  (b) DOC-RANKING eval: per (topic, question, day), as before (graded gains, terminal doc).

Protocol change vs score_gold_full: we decide EVERY question of a topic on EVERY evaluated
day (has-answer-day union + sampled nil days per topic), which is what the real day-loop
does — so the per-day question ranking is well-defined. Memory advances in day order.

References (BM25 / bi-encoder) fire every question every day: doc ranking = top-N by score,
question ranking = questions ordered by their best doc score (no silence).

Run on the VM:
  python -m cdet2026.score_gold_task --dataset gold_testset/dataset_v2 --nil-per-topic 40
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
from .policy import commit_to_memory, decide_question, order_questions
from .query import build_relevance_query
from .scorers import build_novelty_scorer, build_relevance_scorer
from .text_utils import tokenize

METRICS = ["RR_prime", "RBP_prime", "NDCG_prime", "AP_prime"]


def load_gold(ds: Path):
    gold = defaultdict(dict)                      # (tid,qid,day) -> {doc: gain}
    for l in (ds / "qrels_graded.jsonl").read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            gold[(r["topic"], r["qid"], r["day"])][r["doc_id"]] = float(r["gain"])
    topics = [json.loads(l) for l in (ds / "topics.jsonl").read_text().splitlines() if l.strip()]
    return gold, topics


def collection_days():
    con = sqlite3.connect(str(ROOT / "docs.db"))
    days = sorted(r[0] for r in con.execute("SELECT day FROM days"))
    con.close()
    return days


def macro(acc, n):
    return {k: acc[k] / n for k in METRICS} if n else {k: float("nan") for k in METRICS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=str(ROOT / "gold_testset" / "dataset_v2"))
    ap.add_argument("--nil-per-topic", type=int, default=40)
    ap.add_argument("--ref-topn", type=int, default=10)
    ap.add_argument("--skip-refs", action="store_true")
    ap.add_argument("--skip-ours", action="store_true",
                    help="skip our (reranker) model; score references only over the same universe")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=None)
    ap.add_argument("--question-qrels", default=None,
                    help="independent question gold {topic,qid,day,qgain}; if set, the question-ranking "
                         "eval uses these instead of the max-doc-gain proxy")
    ap.add_argument("--universe", default=None,
                    help="universe JSONL {topic,qid,day}; if set, evaluate over EXACTLY these days per "
                         "topic (full timeline, no nil sampling) — for shared-bundle scoring")
    ap.add_argument("--per-topic-out", default=None,
                    help="dump per-topic metric vectors {provider:{doc|question:{tid:{metric:val}}}} "
                         "(overall/all-days averaging per topic) for paired significance testing")
    ap.add_argument("--dump-rankings", default=None,
                    help="dump each provider's rankings (JSON) so a run can be re-scored per-topic "
                         "later without re-running the model")
    args = ap.parse_args()

    cfg = load_config()
    ds = Path(args.dataset)
    gold, topics = load_gold(ds)
    db.connect(reuse_if_open=True)
    alldays = collection_days()
    rng = random.Random(args.seed)
    tmap = {t["tid"]: t for t in topics}

    # question gain per (tid, qid, day): independent gold if provided, else max-doc-gain proxy
    if args.question_qrels:
        qgain = {}
        for l in open(args.question_qrels):
            if l.strip():
                r = json.loads(l)
                qgain[(r["topic"], r["qid"], r["day"])] = float(r.get("qgain", r.get("gain")))
        print(f"question eval: INDEPENDENT question gold ({len(qgain)} rows)", flush=True)
    else:
        qgain = {k: max(v.values()) for k, v in gold.items()}

    # per-topic evaluated days. Default: union of gold days + sampled nils in the active span.
    # With --universe: use EXACTLY the day set the universe file lists per topic (honest silence
    # over the full timeline, no sampling) — for scoring against a shared universe bundle.
    topic_days = {}
    if args.universe:
        uday = defaultdict(set)
        for l in open(args.universe):
            if l.strip():
                r = json.loads(l)
                uday[str(r.get("topic", r.get("tid")))].add(str(r.get("day", r.get("date"))))
        for t in topics:
            if t["tid"] in uday:
                topic_days[t["tid"]] = sorted(uday[t["tid"]])
    else:
        for t in topics:
            tid = t["tid"]
            gdays = sorted({d for (tt, _q, d) in gold if tt == tid})
            if not gdays:
                continue
            span_nil = [d for d in alldays if gdays[0] <= d <= gdays[-1] and d not in set(gdays)]
            nils = rng.sample(span_nil, min(args.nil_per_topic, len(span_nil)))
            topic_days[tid] = sorted(set(gdays) | set(nils))
    total_qd = sum(len(days) * len(tmap[tid]["questions"]) for tid, days in topic_days.items())
    print(f"evaluating {len(topic_days)} topics; question-day decisions = {total_qd}", flush=True)

    daydocs = {}
    def docs_for(day):
        if day not in daydocs:
            daydocs[day] = list(Document.select().where(Document.day == day))
        return daydocs[day]

    # ---------- OUR MODEL: full protocol (every question, every evaluated day) ----------
    model_doc = {}                                   # (tid,qid,day) -> [doc ids]
    model_qrank = {}                                 # (tid,day)     -> [qid in rank order]
    if not args.skip_ours:
      rel = build_relevance_scorer(cfg)
      nov = build_novelty_scorer(cfg)
      done = 0
      top_k = int(cfg["policy"].get("question_top_k", 0))   # idea C: truncate question ranking (0 = off)
      for tid, days in topic_days.items():
        t = tmap[tid]
        mems = {q["qid"]: QuestionMemory() for q in t["questions"]}
        for day in days:
            docs = docs_for(day)
            decisions = []
            for q in t["questions"]:
                rq = build_relevance_query(cfg, t, q["question"])
                dec = decide_question(cfg, rel, nov, mems[q["qid"]], q["qid"], q["question"],
                                      docs, relevance_query=rq)
                decisions.append(dec)
                done += 1
            fired = order_questions(decisions)
            if top_k > 0:
                fired = fired[:top_k]              # keep only the top-K most-confident questions
            kept = {d.qid for d in fired}
            # a truncated (or non-fired) question is not reported -> its doc unit is silent too
            for dec in decisions:
                model_doc[(tid, dec.qid, day)] = [c.doc_id for c in dec.reported] if dec.qid in kept else []
            model_qrank[(tid, day)] = [d.qid for d in fired]
            for d in fired:
                commit_to_memory(mems[d.qid], d)
            if done % 500 < len(t["questions"]):
                print(f"  progress ~{done}/{total_qd}", flush=True)
      rel.close()

    # ---------- REFERENCES (always-fire) ----------
    refs = {}
    if not args.skip_refs:
        from rank_bm25 import BM25Okapi
        emb = Embedder(cfg["relevance"]["model"], cfg["relevance"]["device"],
                       cfg["paths"]["embeddings_cache"] + "/emb.sqlite",
                       batch_size=int(cfg["relevance"].get("batch_size", 64)))
        for name in ("ref_bm25", "ref_biencoder"):
            refs[name] = {"doc": {}, "qrank": {}}
        dcache = {}
        for tid, days in topic_days.items():
            t = tmap[tid]
            qvs = {q["qid"]: emb.encode_query(q["question"]) for q in t["questions"]}
            qtoks = {q["qid"]: tokenize(q["question"]) for q in t["questions"]}
            for day in days:
                docs = docs_for(day)
                if day not in dcache:
                    ids = [d.id for d in docs]
                    embs = emb.encode_docs(ids, [d.text for d in docs])
                    dcache[day] = (embs, BM25Okapi([tokenize(d.text) for d in docs]), ids)
                embs, bm, ids = dcache[day]
                best = {"ref_bm25": [], "ref_biencoder": []}
                for q in t["questions"]:
                    cos = embs @ qvs[q["qid"]]
                    order = np.argsort(-cos)[: args.ref_topn]
                    refs["ref_biencoder"]["doc"][(tid, q["qid"], day)] = [ids[i] for i in order]
                    best["ref_biencoder"].append((float(cos[order[0]]), q["qid"]))
                    bs = np.asarray(bm.get_scores(qtoks[q["qid"]]))
                    border = np.argsort(-bs)[: args.ref_topn]
                    refs["ref_bm25"]["doc"][(tid, q["qid"], day)] = [ids[i] for i in border]
                    best["ref_bm25"].append((float(bs[border[0]]), q["qid"]))
                for name in best:
                    refs[name]["qrank"][(tid, day)] = [q for _s, q in sorted(best[name], reverse=True)]
        emb.close()

    # ---------- SCORING ----------
    def score_docs(doc_ranks):
        ov, ha = defaultdict(float), defaultdict(float)
        n = nha = nil_n = nil_silent = 0
        for tid, days in topic_days.items():
            for q in tmap[tid]["questions"]:
                for day in days:
                    unit = (tid, q["qid"], day)
                    gmap = gold.get(unit, {})
                    ranking = doc_ranks.get(unit, [])
                    m = score_ranking([gmap.get(d, 0.0) for d in ranking], list(gmap.values()))
                    for k in METRICS:
                        ov[k] += m[k]
                    n += 1
                    if gmap:
                        for k in METRICS:
                            ha[k] += m[k]
                        nha += 1
                    else:
                        nil_n += 1
                        nil_silent += 0 if ranking else 1
        return macro(ov, n), macro(ha, nha), (nil_silent / nil_n if nil_n else float("nan")), n, nha

    def score_questions(qranks):
        ov, ha = defaultdict(float), defaultdict(float)
        n = nha = nil_n = nil_silent = 0
        for tid, days in topic_days.items():
            qids = [q["qid"] for q in tmap[tid]["questions"]]
            for day in days:
                ranking = qranks.get((tid, day), [])
                gains = [qgain.get((tid, q, day), 0.0) for q in ranking]
                pool = [qgain[(tid, q, day)] for q in qids if (tid, q, day) in qgain]
                m = score_ranking(gains, pool)
                for k in METRICS:
                    ov[k] += m[k]
                n += 1
                if pool:
                    for k in METRICS:
                        ha[k] += m[k]
                    nha += 1
                else:
                    nil_n += 1
                    nil_silent += 0 if ranking else 1
        return macro(ov, n), macro(ha, nha), (nil_silent / nil_n if nil_n else float("nan")), n, nha

    # per-topic metric vectors (overall/all-days averaging per topic) — for paired significance tests
    def per_topic_docs(doc_ranks):
        out = {}
        for tid, days in topic_days.items():
            acc, n = defaultdict(float), 0
            for q in tmap[tid]["questions"]:
                for day in days:
                    gmap = gold.get((tid, q["qid"], day), {})
                    ranking = doc_ranks.get((tid, q["qid"], day), [])
                    m = score_ranking([gmap.get(d, 0.0) for d in ranking], list(gmap.values()))
                    for k in METRICS:
                        acc[k] += m[k]
                    n += 1
            out[tid] = macro(acc, n)
        return out

    def per_topic_questions(qranks):
        out = {}
        for tid, days in topic_days.items():
            acc, n = defaultdict(float), 0
            qids = [q["qid"] for q in tmap[tid]["questions"]]
            for day in days:
                ranking = qranks.get((tid, day), [])
                gains = [qgain.get((tid, q, day), 0.0) for q in ranking]
                pool = [qgain[(tid, q, day)] for q in qids if (tid, q, day) in qgain]
                m = score_ranking(gains, pool)
                for k in METRICS:
                    acc[k] += m[k]
                n += 1
            out[tid] = macro(acc, n)
        return out

    providers = {} if args.skip_ours else {"our_model": (model_doc, model_qrank)}
    for name, r in refs.items():
        providers[name] = (r["doc"], r["qrank"])

    if args.dump_rankings:
        def _enc(d):
            return {"\x1f".join(map(str, k)): v for k, v in d.items()}
        json.dump({name: {"doc": _enc(dr), "qrank": _enc(qr)} for name, (dr, qr) in providers.items()},
                  open(args.dump_rankings, "w"))
        print(f"rankings -> {args.dump_rankings}")

    report = {}
    print(f"\n=== TASK-FAITHFUL gold scoring ({ds.name}; nil-per-topic={args.nil_per_topic}; "
          f"method={cfg['relevance'].get('method')}) ===")
    for label, fn, idx in (("DOC-RANKING eval (per question, day)", score_docs, 0),
                           ("QUESTION-RANKING eval (per topic, day)", score_questions, 1)):
        print(f"\n--- {label} ---")
        print(f"{'provider':16}{'metric-set':12}{'RR':>8}{'RBP':>8}{'NDCG':>8}{'AP':>8}{'nil-silence':>13}")
        for name, (dr, qr) in providers.items():
            ov, ha, sil, n, nha = fn(dr if idx == 0 else qr)
            report.setdefault(name, {})[("doc" if idx == 0 else "question")] = {
                "overall": ov, "has_answer": ha, "nil_silence": sil, "n": n, "n_has": nha}
            print(f"{name:16}{'overall':12}{ov['RR_prime']:>8.3f}{ov['RBP_prime']:>8.3f}"
                  f"{ov['NDCG_prime']:>8.3f}{ov['AP_prime']:>8.3f}{sil:>13.3f}")
            print(f"{'':16}{'has-answer':12}{ha['RR_prime']:>8.3f}{ha['RBP_prime']:>8.3f}"
                  f"{ha['NDCG_prime']:>8.3f}{ha['AP_prime']:>8.3f}")
    if args.per_topic_out:
        pt = {name: {"doc": per_topic_docs(dr), "question": per_topic_questions(qr)}
              for name, (dr, qr) in providers.items()}
        json.dump(pt, open(args.per_topic_out, "w"), indent=2)
        print(f"per-topic -> {args.per_topic_out}")

    if args.out:
        json.dump(report, open(args.out, "w"), indent=2)
        print(f"\nreport -> {args.out}")


if __name__ == "__main__":
    main()
