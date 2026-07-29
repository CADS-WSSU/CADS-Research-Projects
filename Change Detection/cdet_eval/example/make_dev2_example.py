"""Generate the dev2 worked example for cdet_eval: a real cdet-format run of the LOCAL
(LLM-free) system over the 2 official dev2 topics, plus the matching qrels and a universe
file. Produces (in this directory):
    dev2_qrels.jsonl     — binary organizer relevance (gain 1 per relevant doc)
    dev2_run.jsonl       — cdet submission run of the local system (both eval levels)
    dev2_universe.jsonl  — every (topic, question, day) decided (credits correct silence)

This generator uses the full cdet2026 pipeline and is NOT needed to USE the scorer — it
just produces the shipped example files. Colleagues score their OWN runs with only
evaluate.py + truncated.py (pure standard library). Run from the repo root:

    python cdet_eval/example/make_dev2_example.py --device cuda   # or mps / cpu
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTDIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default=None, help="override config device (cuda/mps/cpu)")
    ap.add_argument("--nil-per-topic", type=int, default=40)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    from cdet_api.models import Document, db
    from cdet2026.config import load_config
    from cdet2026.memory import QuestionMemory
    from cdet2026.policy import commit_to_memory, decide_question, order_questions
    from cdet2026.query import build_relevance_query
    from cdet2026.scorers import build_novelty_scorer, build_relevance_scorer

    cfg = load_config()
    # force the plain LOCAL system so the example is fully reproducible (no API):
    cfg["relevance"]["method"] = "reranker"
    cfg["relevance"]["llm_rescue"] = False
    cfg["relevance"]["llm_grade_reported"] = False
    cfg["policy"]["question_zscore_rank"] = False
    cfg["policy"]["question_zscore_gate"] = False
    cfg["policy"]["corroboration_boost"] = False
    cfg["policy"]["corroboration_gate"] = False
    if args.device:
        cfg["relevance"]["device"] = args.device

    ds = ROOT / "gold_testset" / "dataset_dev2"
    gold = defaultdict(dict)
    for l in (ds / "qrels_graded.jsonl").read_text().splitlines():
        if l.strip():
            r = json.loads(l)
            gold[(r["topic"], r["qid"], r["day"])][r["doc_id"]] = float(r["gain"])
    topics = [json.loads(l) for l in (ds / "topics.jsonl").read_text().splitlines() if l.strip()]
    tmap = {t["tid"]: t for t in topics}

    con = sqlite3.connect(str(ROOT / "docs.db"))
    alldays = sorted(x[0] for x in con.execute("SELECT day FROM days"))
    rng = random.Random(args.seed)
    topic_days = {}
    for t in topics:
        tid = t["tid"]
        gdays = sorted({d for (tt, _q, d) in gold if tt == tid})
        if not gdays:
            continue
        span_nil = [d for d in alldays if gdays[0] <= d <= gdays[-1] and d not in set(gdays)]
        nils = rng.sample(span_nil, min(args.nil_per_topic, len(span_nil)))
        topic_days[tid] = sorted(set(gdays) | set(nils))

    db.connect(reuse_if_open=True)
    daydocs = {}

    def docs_for(day):
        if day not in daydocs:
            daydocs[day] = list(Document.select().where(Document.day == day))
        return daydocs[day]

    rel = build_relevance_scorer(cfg)
    nov = build_novelty_scorer(cfg)

    run_by_topic = {}          # tid -> {day: [ {qid, question_rank, question_text, doc_ranking} ]}
    universe = []              # (tid, qid, day)
    for tid, days in topic_days.items():
        t = tmap[tid]
        mems = {q["qid"]: QuestionMemory() for q in t["questions"]}
        by_day = {}
        for day in days:
            docs = docs_for(day)
            decisions = []
            for q in t["questions"]:
                universe.append((tid, q["qid"], day))
                rq = build_relevance_query(cfg, t, q["question"])
                dec = decide_question(cfg, rel, nov, mems[q["qid"]], q["qid"], q["question"], docs,
                                      relevance_query=rq)
                decisions.append(dec)
            fired = order_questions(decisions)
            if fired:
                results = []
                for rank, d in enumerate(fired):
                    n = len(d.reported)
                    results.append({
                        "qid": d.qid, "question_rank": rank, "question_text": d.question_text,
                        "doc_ranking": [{"doc_id": c.doc_id, "score": round(1.0 - i / max(n, 1), 6)}
                                        for i, c in enumerate(d.reported)],
                    })
                by_day[day] = {"results": results}
            for d in fired:
                commit_to_memory(mems[d.qid], d)
        run_by_topic[tid] = by_day
    rel.close()

    # write run.jsonl (metadata line + per-topic lines)
    with open(OUTDIR / "dev2_run.jsonl", "w") as f:
        f.write(json.dumps({"runtag": "local-dev2-example", "run_type": "automatic",
                            "description": "LLM-free local system, dev2 worked example",
                            "models": ["bge-small-en-v1.5", "bge-reranker-v2-m3", "spaCy en_core_web_sm"],
                            "extern": "local models only"}) + "\n")
        for tid, by_day in run_by_topic.items():
            f.write(json.dumps({"topic": tid, "results": by_day}) + "\n")
    with open(OUTDIR / "dev2_universe.jsonl", "w") as f:
        for tid, qid, day in universe:
            f.write(json.dumps({"topic": tid, "qid": qid, "day": day}) + "\n")
    # ship the qrels too (binary organizer relevance)
    with open(OUTDIR / "dev2_qrels.jsonl", "w") as f:
        for (tid, qid, day), docmap in gold.items():
            for doc, g in docmap.items():
                f.write(json.dumps({"topic": tid, "qid": qid, "day": day, "doc_id": doc, "gain": g}) + "\n")

    fired_days = sum(len(v) for v in run_by_topic.values())
    print(f"wrote dev2 example: {len(topic_days)} topics, {len(universe)} decided units, "
          f"{fired_days} fired topic-days -> {OUTDIR}")


if __name__ == "__main__":
    main()
