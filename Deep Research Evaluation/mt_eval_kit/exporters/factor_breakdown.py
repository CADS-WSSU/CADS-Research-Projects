"""Per-actor factor breakdown: the 6 quality factors + composite, per model.

Pivots the flat list of :class:`ModelEvaluation` into a per-actor view so you can
see, for each actor (question), every model's score on each of the six quality
factors alongside the weighted composite — plus an "all actors" mean table.

Three renderings, all driven by the same data:
* :func:`render_console` — aligned text tables (one block per actor) for stdout.
* :func:`write_factor_csv` — long/wide CSV (one row per actor×model) for Excel.
* :func:`write_factor_markdown` — per-actor Markdown tables for reports.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Sequence

from models.schemas import METRIC_NAMES, ModelEvaluation

#: Column order for every rendering: the six factors then the composite.
FACTORS: tuple[str, ...] = (*METRIC_NAMES, "composite")


def _by_actor(evaluations: Sequence[ModelEvaluation]) -> Dict[str, List[ModelEvaluation]]:
    """Group evaluations by question_id, preserving first-seen model order."""
    out: Dict[str, List[ModelEvaluation]] = {}
    for ev in evaluations:
        out.setdefault(ev.question_id, []).append(ev)
    return out


def _factor_value(ev: ModelEvaluation, factor: str) -> float:
    """Score for one factor (``composite`` maps to the weighted quality_score)."""
    if factor == "composite":
        return ev.quality_score
    return ev.scores.get(factor, float("nan"))


# ---------------------------------------------------------------------------
# Console
# ---------------------------------------------------------------------------
def render_console(evaluations: Sequence[ModelEvaluation]) -> str:
    """Return aligned per-actor tables (factors as rows, models as columns)."""
    by_actor = _by_actor(evaluations)
    lines: List[str] = []
    for qid, evs in by_actor.items():
        models = [ev.model for ev in evs]
        colw = max(12, *(len(m) for m in models))
        header = "Metric".ljust(26) + "".join(m.rjust(colw + 2) for m in models)
        lines.append(f"\nActor: {qid}")
        lines.append(header)
        lines.append("-" * len(header))
        for factor in FACTORS:
            row = ("  " + factor).ljust(26)
            for ev in evs:
                row += f"{_factor_value(ev, factor):>{colw + 2}.2f}"
            lines.append(row)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CSV  (one row per actor × model; one column per factor + composite)
# ---------------------------------------------------------------------------
def write_factor_csv(evaluations: Sequence[ModelEvaluation], out_path: Path) -> Path:
    """Write a tidy CSV: question_id, model, <6 factors>, composite."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["question_id", "model", *FACTORS])
        for qid, evs in _by_actor(evaluations).items():
            for ev in evs:
                w.writerow([qid, ev.model, *(f"{_factor_value(ev, f):.4f}" for f in FACTORS)])
    return out_path


# ---------------------------------------------------------------------------
# Markdown  (per-actor tables + an all-actors mean table)
# ---------------------------------------------------------------------------
def _md_table(models: Sequence[str], cell) -> List[str]:
    head = "| Metric | " + " | ".join(models) + " |"
    sep = "|" + "---|" * (len(models) + 1)
    rows = [head, sep]
    for factor in FACTORS:
        rows.append("| " + factor + " | " + " | ".join(cell(factor, m) for m in models) + " |")
    return rows


def write_factor_markdown(evaluations: Sequence[ModelEvaluation], out_path: Path) -> Path:
    """Write per-actor factor tables plus a mean-across-actors summary table."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    by_actor = _by_actor(evaluations)
    lines: List[str] = ["# Quality factor breakdown", ""]

    # Per-actor tables.
    for qid, evs in by_actor.items():
        models = [ev.model for ev in evs]
        by_model = {ev.model: ev for ev in evs}
        lines.append(f"## {qid}")
        lines.append("")
        lines += _md_table(models, lambda f, m: f"{_factor_value(by_model[m], f):.2f}")
        lines.append("")

    # Mean across all actors, per model.
    all_models: List[str] = []
    for evs in by_actor.values():
        for ev in evs:
            if ev.model not in all_models:
                all_models.append(ev.model)
    sums: Dict[str, Dict[str, float]] = {m: {f: 0.0 for f in FACTORS} for m in all_models}
    counts: Dict[str, int] = {m: 0 for m in all_models}
    for evs in by_actor.values():
        for ev in evs:
            counts[ev.model] += 1
            for f in FACTORS:
                sums[ev.model][f] += _factor_value(ev, f)

    def mean_cell(f: str, m: str) -> str:
        n = counts[m] or 1
        return f"{sums[m][f] / n:.2f}"

    lines.append("## Mean across all actors")
    lines.append("")
    lines += _md_table(all_models, mean_cell)
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
