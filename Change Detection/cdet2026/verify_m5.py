"""Milestone 5 verification: validate a produced run file against the toolkit's OWN
types (Run_adapter) and confirm every processed collection date is present for each
topic with at least an empty list.

Run (server up):
    python -m cdet2026.day_loop --topics data/dev-topics.jsonl --max-days 10
    python -m cdet2026.verify_m5 ncsu-local-base.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from cdet_api.types import DayString, QuestionResults, RunMetadata
from pydantic import BaseModel

from .config import ROOT


class FinalizedTopic(BaseModel):
    """The shape `finalize_run` actually writes (and that the guidelines specify):
    `results` maps each date to a LIST of QuestionResults (DayResults is flattened
    away at finalize). Reuses the toolkit's own DayString + QuestionResults types."""

    topic: str
    results: dict[DayString, list[QuestionResults]]
    extra: dict | None = None


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "ncsu-local-base.json")
    if not path.is_absolute():
        path = ROOT / path
    lines = [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]
    print(f"Run file: {path}  ({len(lines)} lines)")

    # 1) Validate using the toolkit's own types: line 0 = RunMetadata; each subsequent
    #    line = a finalized topic (date -> list[QuestionResults]).
    meta = RunMetadata.model_validate(lines[0])
    topics = [FinalizedTopic.model_validate(ln) for ln in lines[1:]]
    print("\n[schema] RunMetadata + FinalizedTopic (toolkit types): PASSED")
    print(f"  metadata: runtag={meta.runtag!r} run_type={meta.run_type!r} "
          f"models={len(meta.models)} listed")
    print(f"  topics in run: {len(topics)}")

    # 2) Date-coverage + empty-list check, per topic.
    all_dates = sorted({d for t in topics for d in t.results})
    print(f"\n[coverage] distinct dates across run: {len(all_dates)} "
          f"({all_dates[0]} .. {all_dates[-1]})")
    ok = True
    for t in topics:
        missing = [d for d in all_dates if d not in t.results]
        n_fired_days = sum(1 for qlist in t.results.values() if qlist)
        n_reported_q = sum(len(qlist) for qlist in t.results.values())
        status = "OK" if not missing else f"MISSING {len(missing)} dates"
        print(f"  {t.topic}: dates={len(t.results)} fired-days={n_fired_days} "
              f"reported-questions={n_reported_q}  [{status}]")
        if missing:
            ok = False

    # 3) Spot-check question_rank is a 0-based contiguous int sequence on fired days,
    #    and no doc_ranking exceeds 100.
    for t in topics:
        for date, qlist in t.results.items():
            ranks = [q.question_rank for q in qlist]
            if ranks and sorted(ranks) != list(range(len(ranks))):
                print(f"  !! {t.topic} {date}: question_rank not 0-based contiguous: {ranks}")
                ok = False
            for q in qlist:
                if len(q.doc_ranking) > 100:
                    print(f"  !! {t.topic} {date} {q.qid}: doc_ranking {len(q.doc_ranking)} > 100")
                    ok = False

    print("\nRESULT:", "ALL CHECKS PASSED" if ok else "PROBLEMS FOUND")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
