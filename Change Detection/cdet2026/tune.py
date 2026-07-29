"""Milestone 6 (redesigned): development tuning, decoupled and split-objective.

Two phases, so threshold sweeps are instant:
  BUILD (once, slow): run the reranker relevance scorer over each question's relevant
    days plus a sample of nil days, capturing per-(question,day) the top candidates with
    their reranker probability, embedding, and cached term/entity features. Persisted to
    state/scored.pkl (reranker scores are also cached on disk, so it is resumable).
  SWEEP (instant): replay the gate + novelty + policy over the captured candidates for
    any threshold combo, scoring against the proxy qrel. No model calls.

Objective is split (the proxy qrel rewards firing on every relevant day, which conflicts
with the novelty design that suppresses restatements):
  - first-occurrence recall: did we fire on the FIRST day a question has any relevant doc
    (memory empty, so this isolates the relevance gate)?
  - precision: of fired (question,day) pairs, how many actually had a relevant doc?
  - silence: of nil (question,day) pairs, how many did we correctly stay silent on?
  - truncated metrics (RR'/RBP'/NDCG'/AP') overall and on has-answer days.

Proxy qrel is rough (dev-topics-all-docs labels gathered during topic development), and
nil days are SAMPLED, so treat absolute numbers as directional, not official.

Run:
    python -m cdet2026.tune --build        # one-time capture (slow)
    python -m cdet2026.tune --sweep        # instant, after build
"""
from __future__ import annotations

import argparse
import pickle
from collections import defaultdict

import numpy as np
from cdet_api.models import Day, Document, db

from .config import ROOT, load_config, load_topics
from .metrics import score_ranking
from .scorers import build_relevance_scorer
from .scorers.base import Candidate
from .scorers.local_novelty import DocFeatureCache

METRICS = ["RR_prime", "RBP_prime", "NDCG_prime", "AP_prime"]
SCORED_PATH = ROOT / "state" / "scored.pkl"
NIL_EVERY = 15          # sample every Nth day as a nil-day for silence estimation
TOP_N = 20              # candidates captured per (question, day)


def build_proxy_qrel(topics) -> dict:
    db.connect(reuse_if_open=True)
    qrel: dict = {}
    for t in topics:
        for q in t["questions"]:
            per_day: dict[str, set] = defaultdict(set)
            for did in q["rel_docs"]:
                row = Document.get_or_none(Document.id == did)
                if row is not None:
                    per_day[row.day].add(did)
            qrel[(t["tid"], q["qid"])] = dict(per_day)
    return qrel


def build_scored(cfg, topics, qrel) -> dict:
    """Capture top candidates per (question, day) over relevant + sampled nil days."""
    rel = build_relevance_scorer(cfg)
    feat = DocFeatureCache(cfg["paths"]["embeddings_cache"] + "/docfeat.sqlite")
    db.connect(reuse_if_open=True)
    all_days = [d.day for d in Day.select().order_by(Day.seq_day)]
    nil_sample = set(all_days[::NIL_EVERY])
    daydocs: dict = {}

    def docs_for(day):
        if day not in daydocs:
            daydocs[day] = list(Document.select().where(Document.day == day))
        return daydocs[day]

    scored: dict = {}
    qkeys = [(t["tid"], q["qid"], q["question"]) for t in topics for q in t["questions"]]
    for n, (tid, qid, qtext) in enumerate(qkeys, 1):
        reldays = set(qrel[(tid, qid)].keys())
        eval_days = sorted(reldays | nil_sample)
        series = []
        for day in eval_days:
            docs = docs_for(day)
            cands = [Candidate(doc_id=d.id, text=d.text) for d in docs]
            rel.score_day(qtext, cands)
            cands.sort(key=lambda c: c.relevance, reverse=True)
            top = [c for c in cands[:TOP_N] if c.relevance > 0.0]
            feats = feat.get_many([c.doc_id for c in top])
            caps = [(c.doc_id, float(c.relevance), c.embedding.astype(np.float32),
                     *feats.get(c.doc_id, (set(), set()))) for c in top]
            series.append((day, set(qrel[(tid, qid)].get(day, set())), caps))
        scored[(tid, qid)] = series
        print(f"  built {n}/{len(qkeys)}  {tid}/{qid}  days={len(eval_days)}", flush=True)
    rel.close()
    SCORED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SCORED_PATH, "wb") as f:
        pickle.dump(scored, f)
    return scored


def _novelty(emb, terms, ents, mem_embs, mem_terms, mem_ents, w):
    if not mem_embs:
        return 1.0
    mat = np.vstack(mem_embs)
    cos_nov = 1.0 - float(np.max(mat @ emb))
    t_new = len(terms - mem_terms) / len(terms) if terms else 0.0
    e_new = len(ents - mem_ents) / len(ents) if ents else 0.0
    return w[0] * cos_nov + w[1] * t_new + w[2] * e_new


def evaluate(scored, rel_thr, nov_thr, comb_thr, w_rel=0.5, w_nov=0.5,
             w_nov_blend=(0.5, 0.25, 0.25)) -> dict:
    per_q_sum = defaultdict(lambda: defaultdict(float)); per_q_n = defaultdict(int)
    ha_sum = defaultdict(lambda: defaultdict(float)); ha_n = defaultdict(int)
    nil_total = nil_silent = ha_total = ha_fired = 0
    first_total = first_hit = 0
    fire_days = tp_days = 0

    for key, series in scored.items():
        mem_embs, mem_terms, mem_ents = [], set(), set()
        first_rel_seen = False
        for day, relset, caps in series:
            R = len(relset)
            # relevance gate + novelty fire-gate, then order by predicted GAIN
            # (combined = w_rel*relevance + w_nov*novelty): most novel/vital first.
            rep = []
            for did, prob, emb, terms, ents in caps:
                if prob < rel_thr:
                    continue
                nov = _novelty(emb, terms, ents, mem_embs, mem_terms, mem_ents, w_nov_blend)
                if nov < nov_thr:
                    continue
                rep.append((w_rel * prob + w_nov * nov, did, emb, terms, ents))  # order = gain
            rep.sort(reverse=True, key=lambda x: x[0])
            fired = bool(rep)

            reported_ids = [r[1] for r in rep]
            gains = [1.0 if d in relset else 0.0 for d in reported_ids]
            m = score_ranking(gains, [1.0] * R)
            for name in METRICS:
                per_q_sum[key][name] += m[name]
            per_q_n[key] += 1
            if R > 0:
                for name in METRICS:
                    ha_sum[key][name] += m[name]
                ha_n[key] += 1; ha_total += 1
                if fired:
                    ha_fired += 1
                if not first_rel_seen:
                    first_rel_seen = True; first_total += 1
                    if fired:
                        first_hit += 1
            else:
                nil_total += 1
                if not fired:
                    nil_silent += 1
            if fired:
                fire_days += 1
                if any(d in relset for d in reported_ids):
                    tp_days += 1
                for _, _, emb, terms, ents in rep:
                    mem_embs.append(emb); mem_terms |= terms; mem_ents |= ents

    def macro(sums, ns):
        return {name: (sum(sums[k][name] / ns[k] for k in ns if ns[k]) / max(1, sum(1 for k in ns if ns[k])))
                for name in METRICS}

    return {
        "overall": macro(per_q_sum, per_q_n),
        "has_answer": macro(ha_sum, ha_n),
        "first_occ_recall": first_hit / first_total if first_total else 0.0,
        "first": (first_hit, first_total),
        "precision": tp_days / fire_days if fire_days else 1.0,
        "prec": (tp_days, fire_days),
        "silence_rate": nil_silent / nil_total if nil_total else 1.0,
        "nil": (nil_silent, nil_total),
        "fire_recall": ha_fired / ha_total if ha_total else 0.0,
    }


def _fmt(r):
    o, h = r["overall"], r["has_answer"]
    return (f"firstRecall={r['first_occ_recall']:.2f}{r['first']} "
            f"prec={r['precision']:.2f}{r['prec']} "
            f"silence={r['silence_rate']:.3f}{r['nil']} | "
            f"has-ans AP={h['AP_prime']:.3f} NDCG={h['NDCG_prime']:.3f} | overall AP={o['AP_prime']:.3f}")


def main() -> None:
    ap = argparse.ArgumentParser("cdet-2026 tuning (decoupled)")
    ap.add_argument("--topics", default="data/dev-topics-all-docs.jsonl")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    topics = load_topics(args.topics)
    qrel = build_proxy_qrel(topics)

    if args.build or not SCORED_PATH.exists():
        print("BUILD: capturing reranked candidates (one-time, slow)...", flush=True)
        scored = build_scored(cfg, topics, qrel)
    else:
        with open(SCORED_PATH, "rb") as f:
            scored = pickle.load(f)
    print(f"scored questions: {len(scored)}; total (q,day) pairs: {sum(len(v) for v in scored.values())}\n")

    if args.sweep or not args.build:
        print(f"Sweep (reranker threshold), nov>=0.5, combined>=0.5:\n  {'rel':>5} | results")
        for rt in (0.05, 0.10, 0.20, 0.30, 0.50):
            r = evaluate(scored, rt, 0.50, 0.50)
            print(f"  {rt:>5} | {_fmt(r)}", flush=True)


if __name__ == "__main__":
    main()
