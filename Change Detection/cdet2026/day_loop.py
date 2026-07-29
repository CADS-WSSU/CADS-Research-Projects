"""Server-driven day loop: pull each day via the toolkit, decide per question with the
metric-aware policy, report results for EVERY topic every day (empty list when nothing
fires, so every collection date is present), commit accepted docs to memory, and
finalize a well-formed run file.

Idempotent & resumable: the expensive work (document embeddings) is cached on disk by
doc id, so a re-run is cheap and deterministic. Per-question memory is rebuilt
deterministically during the pass and saved after each day. A fresh run uses a new
server token and replays from day 0; because embeddings are cached, restarting after an
interruption is fast and yields identical output.

Run:
    python -m cdet2026.day_loop --topics data/dev-topics.jsonl --max-days 10
    python -m cdet2026.day_loop --topics data/dev-topics.jsonl          # full collection
"""
from __future__ import annotations

import argparse

from cdet_api.client import CDetClient, NoMoreDaysException
from cdet_api.types import DayResults, Hit, QuestionResults, RunMetadata

from .config import ROOT, load_config, load_topics
from .db_stats import log_startup_stats
from .memory import MemoryStore
from .policy import commit_to_memory, decide_question, order_questions
from .query import build_relevance_query
from .scorers import build_novelty_scorer, build_relevance_scorer

# Real components of the baseline. No generative model is used (stated explicitly).
BASELINE_MODELS = [
    "BAAI/bge-small-en-v1.5 (sentence-transformers dense embeddings, MPS)",
    "rank-bm25 Okapi BM25 (day-local lexical scoring)",
    "spaCy en_core_web_sm (named-entity novelty signal)",
    "NOTE: no generative LLM is used in this baseline run",
]


def build_metadata(cfg: dict) -> RunMetadata:
    return RunMetadata(
        runtag=cfg["run"]["runtag"],
        description=cfg["run"]["description"],
        run_type=cfg["run"]["run_type"],
        models=BASELINE_MODELS,
        extern=cfg["run"]["extern"],
    )


def run(topics_path: str, max_days: int | None = None, out_path: str | None = None) -> str:
    cfg = load_config()
    # Empirical sanity check on docs.db (date range + per-day counts; never assumed).
    log_startup_stats()
    topics = load_topics(topics_path)
    rel = build_relevance_scorer(cfg)
    nov = build_novelty_scorer(cfg)
    memory = MemoryStore(cfg["paths"]["state_dir"] + "/memory.pkl")  # fresh pass

    client = CDetClient(base_url=cfg["server"]["base_url"])
    token = client.start_run(api_key=cfg["server"]["api_key"], metadata=build_metadata(cfg))
    if not token:
        raise RuntimeError("start_run returned no token — is the server up with the configured api_key?")

    out_path = out_path or str(ROOT / f"{cfg['run']['runtag']}.json")
    day_count = 0
    fired_total = 0
    try:
        while max_days is None or day_count < max_days:
            try:
                docs = client.next_day(token)
            except NoMoreDaysException:
                break
            if docs is None:
                raise RuntimeError("next_day returned no documents (server/validation error)")
            day = docs[0].day if docs else "(empty)"
            day_count += 1

            for topic in topics:
                tid = topic["tid"]
                decisions = []
                for q in topic["questions"]:
                    qmem = memory.get(tid, q["qid"])
                    rq = build_relevance_query(cfg, topic, q["question"])
                    dec = decide_question(cfg, rel, nov, qmem, q["qid"], q["question"], docs, relevance_query=rq)
                    decisions.append(dec)

                fired = order_questions(decisions)  # only fired, ranked by best score
                qresults = [
                    QuestionResults(
                        qid=dec.qid,
                        question_rank=rank,  # 0-based
                        question_text=dec.question_text,
                        doc_ranking=[Hit(doc_id=c.doc_id, score=round(c.combined, 6)) for c in dec.reported],
                    )
                    for rank, dec in enumerate(fired)
                ]
                # Report for EVERY topic every day (empty list keeps the date key present).
                client.retrieval(token=token, topic=tid, retrieval_results=DayResults(results=qresults))

                # Commit accepted docs into each fired question's memory.
                for dec in decisions:
                    if dec.fired:
                        commit_to_memory(memory.get(tid, dec.qid), dec)
                fired_total += len(fired)

            memory.save()
            if day_count % 25 == 0 or fired:
                print(f"  day {day_count} ({day}): fired-so-far={fired_total}")

        result = client.finalize_run(token, output_filename=out_path)
        print(f"Processed {day_count} day(s). Fired question-days: {fired_total}.")
        print(f"Run file: {out_path}" + (f" (server returned: {result})" if isinstance(result, dict) else ""))
        return out_path
    finally:
        rel.close()


def main() -> None:
    ap = argparse.ArgumentParser("cdet-2026 day loop")
    ap.add_argument("--topics", default="data/dev-topics.jsonl")
    ap.add_argument("--max-days", type=int, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    run(args.topics, max_days=args.max_days, out_path=args.out)


if __name__ == "__main__":
    main()
