"""Smoke test: the standalone evaluator runs offline end-to-end."""
from pathlib import Path
import evaluate

def test_evaluate_deterministic_endtoend(tmp_path):
    ds = Path(__file__).parent.parent / "datasets" / "example_reports.json"
    rc = evaluate.main(["--dataset", str(ds), "--provider", "deterministic", "--out", str(tmp_path/"out")])
    assert rc == 0
    csv = (tmp_path/"out"/"factor_breakdown.csv").read_text()
    assert "composite" in csv and "model-a" in csv and "example_actor" in csv
    assert (tmp_path/"out"/"pairwise_standings.csv").exists()
    assert (tmp_path/"out"/"results.json").exists()
