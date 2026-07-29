"""Benchmark our metric-aware reranker baseline against the organizers' reference runs
(bm25 / bienc / colbert / bm25-colbert), scored with the M4 truncated metrics on the
proxy qrel, over the SAME dates each reference run covers.

The reference runs are naive full-retrieval (100 docs every question every day, no
silence/truncation), so this measures whether the metric-aware policy (silence + gain
ordering + truncation) actually wins under the truncated metric.

Run:
    python -m cdet2026.benchmark
"""
from __future__ import annotations

import json
from collections import defaultdict

from cdet_api.models import Document, db

from .config import ROOT, load_config, load_topics
from .metrics import score_ranking
from .policy import commit_to_memory, decide_question
from .memory import QuestionMemory
from .scorers import build_novelty_scorer, build_relevance_scorer
from .query import build_relevance_query

RUNS_DIR = ROOT / "trec2026" / "change_point" / "runs"
METRICS = ["RR_prime", "RBP_prime", "NDCG_prime", "AP_prime"]


def build_proxy_qrel(topics) -> dict:
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
    return qrel


def load_run(path):
    """-> {(tid, date): {qid: [doc_ids in order]}} and the sorted date list."""
    lines = [json.loads(l) for l in open(path)]
    out = defaultdict(dict)
    dates = set()
    for t in lines[1:]:
        for date, qs in t["results"].items():
            dates.add(date)
            for q in qs:
                out[(t["topic"], date)][q["qid"]] = [h["doc_id"] for h in q["doc_ranking"]]
    return out, sorted(dates)


def score_over_dates(provider, dates, topics, qrel):
    """provider(tid, qid, date) -> ranked doc_ids ([] = silent). Returns split metrics."""
    per_q = defaultdict(lambda: defaultdict(float)); per_q_n = defaultdict(int)
    ha = defaultdict(lambda: defaultdict(float)); ha_n = defaultdict(int)
    nil_t = nil_s = ha_t = ha_f = first_t = first_h = 0
    for t in topics:
        for q in t["questions"]:
            key = (t["tid"], q["qid"]); seen = False
            for date in dates:
                relset = qrel[key].get(date, set()); R = len(relset)
                ranking = provider(t["tid"], q["qid"], date) or []
                gains = [1.0 if d in relset else 0.0 for d in ranking]
                m = score_ranking(gains, [1.0] * R)
                for name in METRICS:
                    per_q[key][name] += m[name]
                per_q_n[key] += 1
                fired = bool(ranking)
                if R > 0:
                    for name in METRICS:
                        ha[key][name] += m[name]
                    ha_n[key] += 1; ha_t += 1; ha_f += fired
                    if not seen:
                        seen = True; first_t += 1; first_h += 1 if any(d in relset for d in ranking) else 0
                else:
                    nil_t += 1; nil_s += 0 if fired else 1
    def macro(s, n):
        return {k: sum(s[x][k] / n[x] for x in n if n[x]) / max(1, sum(1 for x in n if n[x])) for k in METRICS}
    return {"overall": macro(per_q, per_q_n), "has_answer": macro(ha, ha_n),
            "first_occ": (first_h, first_t), "silence": (nil_s, nil_t),
            "fire_recall": (ha_f, ha_t)}


def our_provider(cfg, topics, qrel, dates):
    """Run our metric-aware reranker policy over `dates`, return a provider closure."""
    rel = build_relevance_scorer(cfg); nov = build_novelty_scorer(cfg)
    db.connect(reuse_if_open=True)
    mem = {}; out = defaultdict(dict)
    daydocs = {}
    for t in topics:
        for q in t["questions"]:
            key = (t["tid"], q["qid"]); m = QuestionMemory()
            for date in dates:
                if date not in daydocs:
                    daydocs[date] = list(Document.select().where(Document.day == date))
                rq = build_relevance_query(cfg, t, q["question"])
                dec = decide_question(cfg, rel, nov, m, q["qid"], q["question"], daydocs[date], relevance_query=rq)
                out[(t["tid"], date)][q["qid"]] = [c.doc_id for c in dec.reported]
                if dec.fired:
                    commit_to_memory(m, dec)
    rel.close()
    return lambda tid, qid, date: out.get((tid, date), {}).get(qid, [])


def _fmt(name, r):
    ns, nt = r["silence"]
    h, o = r["has_answer"], r["overall"]
    return (f"{name:26} | "
            f"has-ans  RR'={h['RR_prime']:.3f} RBP'={h['RBP_prime']:.3f} "
            f"NDCG'={h['NDCG_prime']:.3f} AP'={h['AP_prime']:.3f}  || "
            f"overall  RR'={o['RR_prime']:.3f} RBP'={o['RBP_prime']:.3f} "
            f"NDCG'={o['NDCG_prime']:.3f} AP'={o['AP_prime']:.3f}  | "
            f"silence={ns/max(1,nt):.2f}")


def main():
    cfg = load_config()
    topics = load_topics("data/dev-topics-all-docs.jsonl")
    qrel = build_proxy_qrel(topics)

    groups = {
        "April 2022": ["bm25-apr22", "bienc-apr22", "colbert-apr22", "bm25-colbert-apr22"],
    }
    for label, runs in groups.items():
        _, dates = load_run(RUNS_DIR / f"{runs[0]}.jsonl")
        print(f"\n===== {label}  ({len(dates)} days: {dates[0]}..{dates[-1]}) =====")
        for rn in runs:
            run, _ = load_run(RUNS_DIR / f"{rn}.jsonl")
            r = score_over_dates(lambda tid, qid, d: run.get((tid, d), {}).get(qid, []), dates, topics, qrel)
            print("  " + _fmt(rn, r))
        prov = our_provider(cfg, topics, qrel, dates)
        r = score_over_dates(prov, dates, topics, qrel)
        print("  " + _fmt("OURS (reranker+policy)", r))


if __name__ == "__main__":
    main()
