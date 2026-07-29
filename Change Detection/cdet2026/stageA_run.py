"""Full four truncated metrics (RR'/RBP'/NDCG'/AP') on the 30 RAGTIME-2025 gold topics,
using the live metric-aware policy (reranker gate + novelty order) and GRADED gains.

Per question, evaluated over its gold relevant days + a small nil-day sample (bounded so it
finishes; reuses cached reranker scores). Graded gains map RAGTIME grade 1/2/3 -> 1/5/10
(the track's emphasis); pass --binary for gain-1 relevance.

Run: python -m cdet2026.stageA_run --nil-per-q 2
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict

from cdet_api.models import Day, Document, db

from .config import ROOT, load_config
from .memory import QuestionMemory
from .metrics import score_ranking
from .policy import commit_to_memory, decide_question
from .scorers import build_novelty_scorer, build_relevance_scorer

DATA = ROOT / "ragtime25_english"
METRICS = ["RR_prime", "RBP_prime", "NDCG_prime", "AP_prime"]
GRADE_MAP = {1: 1.0, 2: 5.0, 3: 10.0}


def _cap(c, lim=40):
    while len(c) > lim:
        c.pop(next(iter(c)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nil-per-q", type=int, default=2)
    ap.add_argument("--binary", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    rel = build_relevance_scorer(cfg); nov = build_novelty_scorer(cfg)
    db.connect(reuse_if_open=True)

    doc_day, doc_grade = {}, {}
    for l in open(DATA / "qrels.jsonl"):
        d = json.loads(l); doc_day[d["doc_id"]] = d["day"]; doc_grade[d["doc_id"]] = d["rel_grade"]
    topics = [json.loads(l) for l in open(DATA / "topics.jsonl")]
    all_days = [d.day for d in Day.select().order_by(Day.seq_day)]
    rng = random.Random(7)

    def gain(did):
        return 1.0 if args.binary else GRADE_MAP.get(doc_grade.get(did, 1), 1.0)

    per_q = defaultdict(lambda: defaultdict(float)); per_q_n = defaultdict(int)
    ha = defaultdict(lambda: defaultdict(float)); ha_n = defaultdict(int)
    nil_t = nil_s = ha_t = ha_f = first_t = first_h = 0
    daydocs = {}
    n_done = 0

    for t in topics:
        for q in t["questions"]:
            qid, qtext = q["qid"], q["question"]
            reldays = defaultdict(dict)  # day -> {docid: gain}
            for did in q.get("rel_docs", []):
                if did in doc_day:
                    reldays[doc_day[did]][did] = gain(did)
            if not reldays:
                continue
            nil_days = [d for d in all_days if d not in reldays]
            eval_days = sorted(set(reldays) | set(rng.sample(nil_days, min(args.nil_per_q, len(nil_days)))))
            key = (t["tid"], qid); mem = QuestionMemory(); seen = False
            for day in eval_days:
                if day not in daydocs:
                    daydocs[day] = list(Document.select().where(Document.day == day)); _cap(daydocs)
                dec = decide_question(cfg, rel, nov, mem, qid, qtext, daydocs[day])
                relset = reldays.get(day, {}); R = len(relset)
                reported = [c.doc_id for c in dec.reported]
                gains = [relset.get(d, 0.0) for d in reported]
                rel_gains = list(relset.values())
                m = score_ranking(gains, rel_gains)
                for nm in METRICS:
                    per_q[key][nm] += m[nm]
                per_q_n[key] += 1
                if R > 0:
                    for nm in METRICS:
                        ha[key][nm] += m[nm]
                    ha_n[key] += 1; ha_t += 1; ha_f += bool(reported)
                    if not seen:
                        seen = True; first_t += 1; first_h += 1 if any(d in relset for d in reported) else 0
                else:
                    nil_t += 1; nil_s += 0 if reported else 1
                if dec.fired:
                    commit_to_memory(mem, dec)
            n_done += 1
            if n_done % 25 == 0:
                print(f"  ...{n_done} questions", flush=True)
    rel.close()

    def macro(s, n):
        return {k: sum(s[x][k] / n[x] for x in n if n[x]) / max(1, sum(1 for x in n if n[x])) for k in METRICS}
    o = macro(per_q, per_q_n); h = macro(ha, ha_n)
    print("\n=== RAGTIME-2025 (30 topics) — four truncated metrics ===")
    print(f"gains: {'binary' if args.binary else 'graded 1/5/10'} | nil-per-q={args.nil_per_q}")
    print(f"has-ans  RR'={h['RR_prime']:.3f} RBP'={h['RBP_prime']:.3f} NDCG'={h['NDCG_prime']:.3f} AP'={h['AP_prime']:.3f}")
    print(f"overall  RR'={o['RR_prime']:.3f} RBP'={o['RBP_prime']:.3f} NDCG'={o['NDCG_prime']:.3f} AP'={o['AP_prime']:.3f}")
    print(f"silence={nil_s}/{nil_t}={nil_s/max(1,nil_t):.3f}  fire-recall={ha_f}/{ha_t}={ha_f/max(1,ha_t):.3f}  "
          f"first-occ={first_h}/{first_t}={first_h/max(1,first_t):.3f}", flush=True)


if __name__ == "__main__":
    main()
