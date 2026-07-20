"""Slim orchestration — pointwise quality + pairwise round-robin only.

Extracted verbatim from the full evaluator (QualityEvaluator, PairwiseRunner,
_merge_records). No efficiency/Pareto/benchmark aggregation.
"""
from __future__ import annotations

import asyncio
import itertools
from typing import Dict, List, Sequence, Tuple

from judges import JUDGE_CLASSES, PairwiseJudge
from llm.base import LLMClient
from models.schemas import (
    JudgeResult,
    ModelEvaluation,
    ModelReport,
    PairwiseMatch,
    PairwiseRecord,
    PairwiseVerdict,
    Question,
    compute_quality_score,
)


class QualityEvaluator:
    """Run the six-judge quality pipeline for individual reports."""

    def __init__(self, client: LLMClient, *, max_concurrency: int = 8) -> None:
        self.client = client
        self._sem = asyncio.Semaphore(max_concurrency)
        self.judges = [cls(client) for cls in JUDGE_CLASSES]

    async def _run_judge(self, judge, *, question: str, report: str) -> JudgeResult:
        async with self._sem:
            return await judge.evaluate(question=question, report=report)

    async def evaluate_report(
        self, *, question_id: str, question: str, report: ModelReport
    ) -> ModelEvaluation:
        """Evaluate one model's report; return a :class:`ModelEvaluation`."""
        results: List[JudgeResult] = await asyncio.gather(
            *(self._run_judge(j, question=question, report=report.answer) for j in self.judges)
        )
        scores: Dict[str, float] = {r.metric: r.score for r in results}
        quality = compute_quality_score(scores)
        return ModelEvaluation(
            question_id=question_id,
            model=report.model,
            quality_score=quality,
            scores=scores,
            judge_results=results,
            cost=report.cost,
            latency_seconds=report.latency_seconds,
            input_tokens=report.input_tokens,
            output_tokens=report.output_tokens,
        )

    async def evaluate_question(self, question: Question) -> List[ModelEvaluation]:
        """Evaluate every model report for one question, concurrently."""
        return await asyncio.gather(
            *(
                self.evaluate_report(question_id=question.question_id, question=question.question, report=r)
                for r in question.reports
            )
        )


# ---------------------------------------------------------------------------
# Pairwise
# ---------------------------------------------------------------------------
class PairwiseRunner:
    """Round-robin pairwise comparison and standings aggregation."""

    def __init__(self, client: LLMClient, *, max_concurrency: int = 8, balance_order: bool = True) -> None:
        self.judge = PairwiseJudge(client)
        self._sem = asyncio.Semaphore(max_concurrency)
        self.balance_order = balance_order

    async def _compare(
        self, *, question: str, name_a: str, report_a: str, name_b: str, report_b: str
    ) -> Tuple[str, str, PairwiseVerdict]:
        async with self._sem:
            verdict = await self.judge.compare(question=question, report_a=report_a, report_b=report_b)
        return name_a, name_b, verdict

    async def round_robin(
        self, question: str, reports: Sequence[ModelReport], *, question_id: str = ""
    ) -> Tuple[Dict[str, PairwiseRecord], List[PairwiseMatch]]:
        """Run all model pairings for one question; return (records, match details)."""
        records: Dict[str, PairwiseRecord] = {r.model: PairwiseRecord(model=r.model) for r in reports}

        pairs: List[Tuple[ModelReport, ModelReport]] = []
        for a, b in itertools.combinations(reports, 2):
            pairs.append((a, b))
            if self.balance_order:
                pairs.append((b, a))

        outcomes = await asyncio.gather(
            *(
                self._compare(question=question, name_a=a.model, report_a=a.answer, name_b=b.model, report_b=b.answer)
                for a, b in pairs
            )
        )

        matches: List[PairwiseMatch] = []
        for name_a, name_b, verdict in outcomes:
            self._apply(records, name_a, name_b, verdict)
            matches.append(
                PairwiseMatch(
                    question_id=question_id,
                    model_a=name_a,
                    model_b=name_b,
                    winner=verdict.winner,
                    confidence=verdict.confidence,
                    rationale=verdict.rationale,
                )
            )
        return records, matches

    @staticmethod
    def _apply(records: Dict[str, PairwiseRecord], name_a: str, name_b: str, verdict: PairwiseVerdict) -> None:
        if verdict.winner == "system_a":
            records[name_a].wins += 1
            records[name_b].losses += 1
        elif verdict.winner == "system_b":
            records[name_b].wins += 1
            records[name_a].losses += 1
        else:
            records[name_a].ties += 1
            records[name_b].ties += 1


def _merge_records(dst: Dict[str, PairwiseRecord], src: Dict[str, PairwiseRecord]) -> None:
    """Accumulate per-question pairwise records into running standings."""
    for name, rec in src.items():
        if name not in dst:
            dst[name] = PairwiseRecord(model=name)
        dst[name].wins += rec.wins
        dst[name].losses += rec.losses
        dst[name].ties += rec.ties
