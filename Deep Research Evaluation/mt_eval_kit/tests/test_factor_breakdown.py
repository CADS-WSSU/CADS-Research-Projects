"""Tests for the per-actor factor-breakdown exporter."""

from __future__ import annotations

import csv

from exporters.factor_breakdown import FACTORS, render_console, write_factor_csv, write_factor_markdown
from models.schemas import METRIC_NAMES, ModelEvaluation


def _ev(qid, model, base):
    scores = {m: base for m in METRIC_NAMES}
    return ModelEvaluation(question_id=qid, model=model, quality_score=base, scores=scores)


def _evals():
    return [
        _ev("actorA", "model-x", 8.0),
        _ev("actorA", "model-y", 5.0),
        _ev("actorB", "model-x", 6.0),
        _ev("actorB", "model-y", 7.0),
    ]


def test_factors_are_six_plus_composite():
    assert FACTORS == (*METRIC_NAMES, "composite")
    assert len(FACTORS) == 7


def test_console_has_per_actor_blocks_and_all_factors():
    out = render_console(_evals())
    assert "Actor: actorA" in out and "Actor: actorB" in out
    for f in FACTORS:
        assert f in out
    assert "model-x" in out and "model-y" in out


def test_csv_one_row_per_actor_model_with_all_columns(tmp_path):
    p = write_factor_csv(_evals(), tmp_path / "fb.csv")
    rows = list(csv.DictReader(p.open()))
    assert len(rows) == 4  # 2 actors x 2 models
    assert rows[0]["question_id"] == "actorA" and rows[0]["model"] == "model-x"
    for f in FACTORS:
        assert f in rows[0]
    assert float(rows[0]["composite"]) == 8.0


def test_markdown_has_per_actor_and_mean_tables(tmp_path):
    p = write_factor_markdown(_evals(), tmp_path / "fb.md")
    text = p.read_text()
    assert "## actorA" in text and "## actorB" in text
    assert "Mean across all actors" in text
    # model-x mean composite across the two actors = (8+6)/2 = 7.00
    assert "7.00" in text


def test_arbitrary_model_count(tmp_path):
    # three models on one actor — exporter must not assume a fixed lineup
    evals = [_ev("a", "m1", 1.0), _ev("a", "m2", 2.0), _ev("a", "m3", 3.0)]
    out = render_console(evals)
    assert "m1" in out and "m2" in out and "m3" in out
    rows = list(csv.DictReader(write_factor_csv(evals, tmp_path / "c.csv").open()))
    assert {r["model"] for r in rows} == {"m1", "m2", "m3"}
