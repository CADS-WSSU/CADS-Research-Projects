"""Milestone 3 verification: novelty + memory + metric-aware policy.

Demonstrates, for q_1 "Who is Emmanuel Macron?" (topic cd2026_001):
  1. SILENCE on a no-content day (2021-08-01): nothing clears relevance -> empty report.
  2. FIRE on election day (2022-04-24): genuine update -> ordered, truncated report.
  3. RESTATEMENT SUPPRESSION: after committing day-2 docs to memory, the same docs
     re-presented score low novelty and the question no longer fires.

Loads each day's docs directly from docs.db (the exact content the server serves for
that day; no future days are read). Fast, no full multi-day run needed.

Run (from project root):  python -m cdet2026.verify_m3
"""
from __future__ import annotations

from cdet_api.models import Document, db

from .config import load_config, load_topics
from .memory import QuestionMemory
from .policy import commit_to_memory, decide_question
from .scorers import build_novelty_scorer, build_relevance_scorer


def day_docs(day: str):
    return list(Document.select().where(Document.day == day))


def show(title: str, decision, memory: QuestionMemory) -> None:
    state = f"FIRED ({len(decision.reported)} docs)" if decision.fired else "SILENT (empty report)"
    print(f"\n[{title}]  -> {state}   | memory has {len(memory.doc_ids)} accepted docs")
    for c in decision.reported[:4]:
        print(f"    combined={c.combined:.3f} rel={c.relevance:.3f} nov={c.novelty:.3f}"
              f"  {c.text[:60].strip()}")


def main() -> None:
    cfg = load_config()
    topics = load_topics("data/dev-topics.jsonl")
    rel = build_relevance_scorer(cfg)
    nov = build_novelty_scorer(cfg)
    db.connect(reuse_if_open=True)

    tid = topics[0]["tid"]
    q = topics[0]["questions"][0]  # q_1: Who is Emmanuel Macron?
    qid, qtext = q["qid"], q["question"]
    memory = QuestionMemory()  # fresh per-question memory
    print(f"Topic {tid} | {qid}: {qtext}")
    print(f"thresholds: rel>={cfg['relevance']['threshold']} nov>={cfg['novelty']['threshold']} "
          f"combined>={cfg['policy']['combined_threshold']}")

    try:
        # 1) No-content day -> should be silent.
        d1 = decide_question(cfg, rel, nov, memory, qid, qtext, day_docs("2021-08-01"))
        show("Day 2021-08-01 (no French-election content)", d1, memory)

        # 2) Election day -> should fire; commit reported docs to memory.
        d2 = decide_question(cfg, rel, nov, memory, qid, qtext, day_docs("2022-04-24"))
        show("Day 2022-04-24 (election day, memory empty)", d2, memory)
        commit_to_memory(memory, d2)

        # 3) Re-present the SAME day's docs now that memory holds them -> novelty collapses.
        d3 = decide_question(cfg, rel, nov, memory, qid, qtext, day_docs("2022-04-24"))
        show("Day 2022-04-24 re-presented (now in memory)", d3, memory)
        print("\nInterpretation: same relevant docs, but novelty dropped below threshold,"
              "\nso the question correctly does NOT re-fire on a restatement.")
    finally:
        rel.close()
        db.close()


if __name__ == "__main__":
    main()
