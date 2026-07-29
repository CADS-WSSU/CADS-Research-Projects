"""Central config + small shared loaders. Everything tunable lives in config.toml;
nothing in the code hard-codes a threshold or model name (plan: cross-cutting rule)."""
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    with open(__import__("os").environ.get("CDET_CONFIG") or (ROOT / "config.toml"), "rb") as f:
        return tomllib.load(f)


def load_topics(path: str | Path) -> list[dict]:
    """Load a topics .jsonl file (dev-topics.jsonl or dev-topics-all-docs.jsonl)."""
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    with open(p) as f:
        return [json.loads(line) for line in f if line.strip()]
