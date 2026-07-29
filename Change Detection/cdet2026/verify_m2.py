"""Milestone 2 verification: per-question, per-day hybrid retrieval.

Two checks:
  (A) Server-driven loop on day 1 — pull the day's docs via next_day, rank a topic's
      questions, print the top candidates. Proves the loop + hybrid scorer run.
  (B) Known-doc surfacing — for a question with a known relevant doc, load THAT doc's
      day directly from docs.db (the same content the server would serve for that day;
      no future days are read) and report where the known doc lands in the ranking.

Run (server up, from project root):
    python -m cdet2026.verify_m2
"""
from __future__ import annotations

from cdet_api.client import CDetClient
from cdet_api.models import Document, db
from cdet_api.types import RunMetadata

from .config import load_config, load_topics
from .scorers import Candidate, build_relevance_scorer


def rank(scorer, question_text: str, candidates: list[Candidate]) -> list[Candidate]:
    scorer.score_day(question_text, candidates)
    candidates.sort(key=lambda c: c.relevance, reverse=True)
    return candidates


def docs_to_candidates(rows) -> list[Candidate]:
    return [Candidate(doc_id=r.id, text=r.text) for r in rows]


def check_a_server_loop(cfg, scorer, topics) -> None:
    print("=" * 70)
    print("(A) Server-driven loop — day 1")
    print("=" * 70)
    client = CDetClient(base_url=cfg["server"]["base_url"])
    meta = RunMetadata(
        runtag=cfg["run"]["runtag"], description=cfg["run"]["description"],
        run_type=cfg["run"]["run_type"], extern=cfg["run"]["extern"], models=[],
    )
    token = client.start_run(api_key=cfg["server"]["api_key"], metadata=meta)
    docs = client.next_day(token)
    print(f"Pulled {len(docs)} docs for day {docs[0].day}.")

    topic = topics[0]
    thr = cfg["relevance"]["threshold"]
    for q in topic["questions"][:2]:
        cands = [Candidate(doc_id=d.id, text=d.text) for d in docs]
        ranked = rank(scorer, q["question"], cands)
        n_over = sum(1 for c in ranked if c.relevance >= thr)
        print(f"\n  {q['qid']}: {q['question']}")
        print(f"    candidates >= threshold({thr}): {n_over} of {len(ranked)}")
        for c in ranked[:3]:
            print(f"      rel={c.relevance:.3f} (cos={c.extra['dense_cos']:.3f} "
                  f"bm25={c.extra['bm25_norm']:.3f})  {c.text[:70].strip()}")


def check_b_known_doc(cfg, scorer, topics) -> None:
    print("\n" + "=" * 70)
    print("(B) Known-doc surfacing")
    print("=" * 70)
    db.connect(reuse_if_open=True)
    topic = topics[0]
    q = topic["questions"][0]  # q_1: Who is Emmanuel Macron?
    target_doc = q["rel_docs"][0]
    day = Document.get(Document.id == target_doc).day
    rows = list(Document.select().where(Document.day == day))
    print(f"Question {q['qid']}: {q['question']}")
    print(f"Known relevant doc {target_doc} is on day {day} ({len(rows)} docs).")

    cands = docs_to_candidates(rows)
    ranked = rank(scorer, q["question"], cands)
    pos = next(i for i, c in enumerate(ranked) if c.doc_id == target_doc)
    tc = ranked[pos]
    print(f"  -> known doc ranked #{pos + 1} of {len(ranked)}  "
          f"rel={tc.relevance:.3f} (cos={tc.extra['dense_cos']:.3f} bm25={tc.extra['bm25_norm']:.3f})")
    print("  top-3 for this question/day:")
    for c in ranked[:3]:
        mark = " <== known" if c.doc_id == target_doc else ""
        print(f"     rel={c.relevance:.3f}  {c.text[:65].strip()}{mark}")
    db.close()


def main() -> None:
    cfg = load_config()
    topics = load_topics("data/dev-topics.jsonl")
    scorer = build_relevance_scorer(cfg)
    try:
        check_a_server_loop(cfg, scorer, topics)
        check_b_known_doc(cfg, scorer, topics)
    finally:
        scorer.close()


if __name__ == "__main__":
    main()
