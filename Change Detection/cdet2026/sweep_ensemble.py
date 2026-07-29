"""Sweep the rank-aware ensemble-gate knobs (ensemble_cos_rank K, ensemble_min_prob)
on the cd2026 April benchmark. Reranker scores are cached, so each combo just re-applies
the gate — fast. Reports has-answer AP'/RR' and silence per combo.

Run:  python -m cdet2026.sweep_ensemble
"""
from __future__ import annotations

import copy
from collections import defaultdict

from cdet_api.models import Document, db

from .benchmark import RUNS_DIR, build_proxy_qrel, load_run, score_over_dates
from .config import load_config, load_topics
from .memory import QuestionMemory
from .policy import commit_to_memory, decide_question
from .scorers import build_novelty_scorer, build_relevance_scorer


def main():
    cfg = load_config()
    topics = load_topics("data/dev-topics-all-docs.jsonl")
    qrel = build_proxy_qrel(topics)
    _, dates = load_run(RUNS_DIR / "bm25-apr22.jsonl")
    rel = build_relevance_scorer(cfg); nov = build_novelty_scorer(cfg)
    db.connect(reuse_if_open=True)
    daydocs = {d: list(Document.select().where(Document.day == d)) for d in dates}

    def run_combo(K, mp):
        c = copy.deepcopy(cfg)
        c["relevance"]["ensemble_cos_rank"] = K
        c["relevance"]["ensemble_min_prob"] = mp
        out = defaultdict(dict)
        for t in topics:
            for q in t["questions"]:
                m = QuestionMemory()
                for date in dates:
                    dec = decide_question(c, rel, nov, m, q["qid"], q["question"], daydocs[date])
                    out[(t["tid"], date)][q["qid"]] = [x.doc_id for x in dec.reported]
                    if dec.fired:
                        commit_to_memory(m, dec)
        return score_over_dates(lambda tid, qid, d: out.get((tid, d), {}).get(qid, []), dates, topics, qrel)

    print(f"primary reranker threshold = {cfg['relevance']['threshold']}  (K=0 => ensemble OFF = baseline)")
    print(f"  {'K':>3} {'min_prob':>9} | has-ans AP'  RR'   | silence | overall AP'")
    for K, mp in [(0, 0.05), (3, 0.05), (5, 0.08), (5, 0.05), (5, 0.03), (10, 0.05), (10, 0.03)]:
        r = run_combo(K, mp)
        ns, nt = r["silence"]
        print(f"  {K:>3} {mp:>9} | {r['has_answer']['AP_prime']:.3f}      {r['has_answer']['RR_prime']:.3f} "
              f"|  {ns/max(1,nt):.3f}  | {r['overall']['AP_prime']:.3f}", flush=True)
    rel.close()


if __name__ == "__main__":
    main()
