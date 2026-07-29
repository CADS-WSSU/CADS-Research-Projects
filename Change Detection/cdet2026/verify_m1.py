"""Milestone 1 verification: confirm we can pull one day of documents from the
running cdet-api server and parse them, and that the dev topics load.

Run (with the server already up, from the project root):
    python -m cdet2026.verify_m1
"""
import json
import tomllib
from pathlib import Path

from cdet_api.client import CDetClient
from cdet_api.types import RunMetadata

ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def load_topics(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    cfg = load_config()
    topics = load_topics(ROOT / "data" / "dev-topics.jsonl")
    print(f"Loaded {len(topics)} dev topics:")
    for t in topics:
        print(f"  - {t['tid']} ({t['label']}): {len(t['questions'])} questions")

    client = CDetClient(base_url=cfg["server"]["base_url"])
    meta = RunMetadata(
        runtag=cfg["run"]["runtag"],
        description=cfg["run"]["description"],
        run_type=cfg["run"]["run_type"],
        extern=cfg["run"]["extern"],
        models=[],
    )
    token = client.start_run(api_key=cfg["server"]["api_key"], metadata=meta)
    assert token, "start_run returned no token — is the server running with api_key 'abc123'?"
    print(f"\nStarted run, token={token[:12]}...")

    docs = client.next_day(token)
    days = sorted({d.day for d in docs})
    print(f"\nDay 1 (next_day) returned {len(docs)} documents.")
    print(f"  distinct day value(s) in batch: {days}")
    print("  sample documents:")
    for d in docs[:3]:
        snippet = d.text[:90].replace("\n", " ")
        print(f"    id={d.id}  date={d.date}  url={d.url[:50]}")
        print(f"       text: {snippet}...")


if __name__ == "__main__":
    main()
