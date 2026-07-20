"""CSV exporters for the leaderboards, pairwise results, and Pareto frontier.

Produces the files named in the spec:

* ``leaderboard_quality.csv``            — Model, Quality
* ``leaderboard_cost.csv``               — Model, Cost
* ``leaderboard_quality_per_dollar.csv`` — Model, Q/$  (free/local flagged)
* ``leaderboard_quality_per_token.csv``  — Model, Q/1K Tokens
* ``leaderboard_quality_per_minute.csv`` — Model, Q/Minute
* ``pairwise_results.csv``               — Model, Wins, Losses, Ties, WinRate
* ``pareto_frontier.csv``                — Model (Pareto-optimal only)
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Dict, List, Sequence

from models.schemas import LeaderboardRow, ModelAggregate

# Maps the internal leaderboard key -> (filename, value-column header).
_LEADERBOARD_FILES: Dict[str, tuple[str, str]] = {
    "quality": ("leaderboard_quality.csv", "Quality"),
    "cost": ("leaderboard_cost.csv", "Cost"),
    "quality_per_dollar": ("leaderboard_quality_per_dollar.csv", "Q/$"),
    "quality_per_token": ("leaderboard_quality_per_token.csv", "Q/1K Tokens"),
    "quality_per_minute": ("leaderboard_quality_per_minute.csv", "Q/Minute"),
    "win_rate": ("pairwise_winrate.csv", "Win Rate"),
}


def _fmt(value: float) -> str:
    """Format a metric value; render infinity as the literal 'inf'."""
    if math.isinf(value):
        return "inf"
    return f"{value:.4f}"


def write_leaderboard_csv(
    rows: Sequence[LeaderboardRow], out_path: str | Path, value_header: str
) -> Path:
    """Write one leaderboard (already sorted) to CSV: Model, <value_header>, Note."""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Model", value_header, "Note"])
        for row in rows:
            writer.writerow([row.model, _fmt(row.value), row.note])
    return path


def write_all_leaderboards(
    leaderboards: Dict[str, List[LeaderboardRow]], out_dir: str | Path
) -> List[Path]:
    """Write each known leaderboard to its spec-named CSV; return paths written."""
    out = Path(out_dir)
    written: List[Path] = []
    for key, (filename, header) in _LEADERBOARD_FILES.items():
        if key in leaderboards:
            written.append(write_leaderboard_csv(leaderboards[key], out / filename, header))
    return written


def write_pairwise_csv(aggregates: Sequence[ModelAggregate], out_path: str | Path) -> Path:
    """Write the pairwise win/loss/tie/win-rate table, ranked by win rate."""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ranked = sorted(aggregates, key=lambda a: a.win_rate, reverse=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Model", "Wins", "Losses", "Ties", "WinRate"])
        for a in ranked:
            writer.writerow([a.model, a.wins, a.losses, a.ties, f"{a.win_rate:.4f}"])
    return path


def write_pareto_csv(
    frontier: Sequence[str], aggregates: Sequence[ModelAggregate], out_path: str | Path
) -> Path:
    """Write the Pareto-optimal models with their quality/cost/latency vectors."""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    by_model = {a.model: a for a in aggregates}
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Model", "Quality", "MeanCost", "MeanLatencySeconds"])
        for model in frontier:
            a = by_model.get(model)
            if a is None:
                continue
            writer.writerow(
                [a.model, f"{a.mean_quality:.4f}", f"{a.mean_cost:.6f}", f"{a.mean_latency_seconds:.4f}"]
            )
    return path
