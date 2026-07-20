"""Standalone CTI report evaluator — pointwise (6 factors + composite) + pairwise.

Bring your own reports (any number of models, any names); this scores them. No
generation, no cost/efficiency. See INTEGRATION.md for the input format.

    python evaluate.py --dataset my_reports.json --provider deterministic --out reports/eval
    python evaluate.py --dataset my_reports.json --provider openai --out reports/eval
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

from exporters import render_console, write_factor_csv, write_factor_markdown, write_results_json
from exporters.csv_exporter import write_pairwise_csv
from llm import CostTracker, ResponseCache, build_client
from models.schemas import ModelAggregate, PairwiseRecord, Question, Results, Usage
from orchestrator import PairwiseRunner, QualityEvaluator, _merge_records

_DEFAULT_CONFIG = Path(__file__).parent / "config.yaml"


def load_config(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def build_infra(config: Dict[str, Any], provider: str, *, use_cache: bool):
    cache = ResponseCache(config.get("cache", {}).get("directory", ".eval_cache"), enabled=use_cache)
    tracker = CostTracker()
    client = build_client(provider, config, cache=cache, cost_tracker=tracker)
    return client, tracker


def load_questions(path: str | Path) -> List[Question]:
    with Path(path).open("r", encoding="utf-8") as fh:
        return [Question.model_validate(item) for item in json.load(fh)]


async def _run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    provider = args.provider or config.get("default_provider", "deterministic")
    client, cost_tracker = build_infra(config, provider, use_cache=not args.no_cache)

    questions = load_questions(args.dataset)
    models = sorted({r.model for q in questions for r in q.reports})
    print(
        f"Evaluating {len(questions)} actor(s) × {len(models)} model(s) "
        f"[{', '.join(models)}] with judge '{provider}'"
        f"{'' if args.pairwise else ' (pointwise only)'} ...",
        file=sys.stderr,
    )

    evaluator = QualityEvaluator(client, max_concurrency=args.max_concurrency)
    all_evals = []
    for q in questions:
        all_evals.extend(await evaluator.evaluate_question(q))

    standings: Dict[str, PairwiseRecord] = {}
    all_matches = []
    if args.pairwise:
        runner = PairwiseRunner(client, max_concurrency=args.max_concurrency)
        for q in questions:
            if len(q.reports) >= 2:
                records, matches = await runner.round_robin(q.question, q.reports, question_id=q.question_id)
                _merge_records(standings, records)
                all_matches.extend(matches)
    await client.aclose()

    aggregates = [
        ModelAggregate(model=r.model, n_questions=len(questions), win_rate=r.win_rate,
                       wins=r.wins, losses=r.losses, ties=r.ties)
        for r in standings.values()
    ]
    results = Results(
        dataset=Path(args.dataset).name, judge_provider=client.provider, n_questions=len(questions),
        evaluations=all_evals, aggregates=aggregates, pairwise_matches=all_matches,
        judge_cost_usd=cost_tracker.total_cost_usd if cost_tracker else 0.0,
        judge_usage=cost_tracker.total_usage if cost_tracker else Usage(),
    )

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    write_factor_csv(all_evals, out / "factor_breakdown.csv")
    write_factor_markdown(all_evals, out / "factor_breakdown.md")
    write_results_json(results, out / "results.json")
    if args.pairwise and aggregates:
        write_pairwise_csv(aggregates, out / "pairwise_standings.csv")

    print(render_console(all_evals))
    if args.pairwise and standings:
        print("\n=== Pairwise standings (win-rate) ===")
        for r in sorted(standings.values(), key=lambda x: x.win_rate, reverse=True):
            print(f"  {r.model:<24} {r.wins}W-{r.losses}L-{r.ties}T  win_rate={r.win_rate:.3f}")
    cost = cost_tracker.total_cost_usd if cost_tracker else 0.0
    if cost:
        print(f"\n[judge cost] ${cost:.4f}", file=sys.stderr)
    print(f"\nWrote outputs to {out}/", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="evaluate",
        description="Pointwise (6 factors + composite) and pairwise evaluation of model reports.")
    p.add_argument("--dataset", required=True, help="Reports dataset JSON (see INTEGRATION.md).")
    p.add_argument("--provider", default=None,
                   help="deterministic | openai | anthropic | gemini | ollama | vllm (default: config default_provider).")
    p.add_argument("--out", default="reports/eval", help="Output directory.")
    p.add_argument("--config", default=str(_DEFAULT_CONFIG), help="config.yaml path.")
    p.add_argument("--no-pairwise", dest="pairwise", action="store_false", help="Skip pairwise; pointwise factors only.")
    p.add_argument("--no-cache", action="store_true", help="Disable on-disk response cache.")
    p.add_argument("--max-concurrency", type=int, default=8, help="Max concurrent judge calls.")
    return p


def main(argv: List[str] | None = None) -> int:
    return asyncio.run(_run(build_parser().parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
