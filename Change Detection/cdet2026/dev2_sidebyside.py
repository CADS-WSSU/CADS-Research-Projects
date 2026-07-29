"""Diagnose the dev2 has-answer score: run OUR model on exactly the has-answer
(topic, question, day) units and lay the ground truth next to what the model produced.

For each has-answer unit we show: the GT relevant doc(s) that day, our model's ranking,
whether it stayed silent (miss), fired but missed the GT doc, or found it (and at what
rank), plus the per-unit AP'. Then a summary that explains the has-answer average.

Restricting to has-answer days is exact for the has-answer metric: nil days contribute
nothing to per-question memory, so novelty/ordering is identical.

Run on the VM:  python -m cdet2026.dev2_sidebyside
"""
from __future__ import annotations

from collections import defaultdict

from cdet_api.models import Document, db

from .config import load_config, load_topics
from .memory import QuestionMemory
from .metrics import score_ranking
from .policy import commit_to_memory, decide_question
from .query import build_relevance_query
from .scorers import build_novelty_scorer, build_relevance_scorer

TOPICS_FILE = "data/dev-topics-all-docs.jsonl"


def main():
    cfg = load_config()
    topics = load_topics(TOPICS_FILE)
    db.connect(reuse_if_open=True)

    # ground truth: (tid,qid) -> {day: set(rel docs)}
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

    rows = []
    aps = []
    silent = found = fired_miss = 0
    ranks = []
    for t in topics:
        for q in t["questions"]:
            key = (t["tid"], q["qid"])
            mem = QuestionMemory()
            for day in sorted(qrel[key]):                 # this question's has-answer days, in order
                relset = qrel[key][day]
                if day not in daydocs:
                    daydocs[day] = list(Document.select().where(Document.day == day))
                rq = build_relevance_query(cfg, t, q["question"])
                dec = decide_question(cfg, rel, nov, mem, q["qid"], q["question"], daydocs[day], relevance_query=rq)
                ranking = [c.doc_id for c in dec.reported]
                gains = [1.0 if d in relset else 0.0 for d in ranking]
                m = score_ranking(gains, [1.0] * len(relset))
                aps.append(m["AP_prime"])
                gt_rank = next((i + 1 for i, d in enumerate(ranking) if d in relset), None)
                if not ranking:
                    silent += 1; status = "SILENT (miss)"
                elif gt_rank:
                    found += 1; ranks.append(gt_rank); status = f"found@{gt_rank}"
                else:
                    fired_miss += 1; status = f"fired {len(ranking)} docs, GT not among them"
                rows.append((t["tid"], q["qid"], day, len(relset), len(ranking), status, round(m["AP_prime"], 3), q["question"]))
                if dec.fired:
                    commit_to_memory(mem, dec)
    rel.close()

    n = len(rows)
    print(f"\n=== dev2 has-answer diagnosis — {n} (topic,question,day) units with a relevant doc ===")
    print(f"mean has-answer AP' = {sum(aps)/n:.3f}\n")
    print(f"  SILENT (model reported nothing)        : {silent:>4}  ({100*silent/n:.0f}%)  -> AP'=0")
    print(f"  FIRED but GT doc not retrieved         : {fired_miss:>4}  ({100*fired_miss/n:.0f}%)  -> AP'=0")
    print(f"  FOUND the GT doc                        : {found:>4}  ({100*found/n:.0f}%)")
    if ranks:
        at1 = sum(1 for r in ranks if r == 1)
        print(f"      of those, ranked #1: {at1}/{found} ({100*at1/found:.0f}%); mean rank {sum(ranks)/len(ranks):.2f}")
    print("\n--- sample side-by-side (first 30 units) ---")
    print(f"{'topic':11} {'qid':5} {'day':11} {'GTn':>3} {'outN':>4}  {'result':30} {'AP':>5}")
    for r in rows[:30]:
        print(f"{r[0]:11} {r[1]:5} {r[2]:11} {r[3]:>3} {r[4]:>4}  {r[5]:30} {r[6]:>5}")

    # write full side-by-side
    import json
    with open("dev2_sidebyside.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps({"tid": r[0], "qid": r[1], "day": r[2], "gt_n": r[3],
                                "out_n": r[4], "result": r[5], "ap_prime": r[6], "question": r[7]}) + "\n")
    print(f"\nfull table -> dev2_sidebyside.jsonl ({n} rows)")


if __name__ == "__main__":
    main()
