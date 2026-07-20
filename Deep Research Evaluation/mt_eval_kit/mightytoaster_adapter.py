"""Adapter: convert MIGHTYTOASTER export files into the evaluator's input dataset.

The evaluator consumes a JSON list of questions, each with one report per model:

    [{"question_id", "question", "category", "reports": [
        {"model", "answer", "cost", "latency_seconds", "input_tokens", "output_tokens"}]}]

MIGHTYTOASTER emits at least two shapes, both handled here:

1. **"queries" export** — ``{"queries": [{"query", "model", "result": {...}, "created_at",
   "completed_at", ...}]}``. The ``result`` is a structured CTI dossier (summary,
   identity, sections, timeline, IOCs, MITRE techniques, mitigations, gaps,
   sources, hunting queries). We flatten it into a faithful markdown report for
   the judges, and derive ``latency_seconds`` from the timestamps.

2. **"graph" export** — a D3FEND CAD graph ``{"meta", "nodes", "edges"}`` with no
   model/question. We synthesise a question from ``meta`` and render the graph
   (actors, artifacts/IOCs, events, countermeasures, relationships) into markdown.

Honesty notes (see README / the run output):
* These exports do NOT carry generation cost or token counts, so ``cost`` /
  ``input_tokens`` / ``output_tokens`` default to 0. Efficiency leaderboards
  (quality-per-$/token) are therefore only meaningful once you populate those
  from MIGHTYTOASTER's real run metrics. ``latency_seconds`` is filled from
  timestamps when present.
* The graph export records no model; its report is labelled ``unknown`` unless
  you pass ``--default-model``.

Usage
-----
    python mightytoaster_adapter.py FILE [FILE ...] --out datasets/mightytoaster_reports.json
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------
def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    """Parse a Postgres/ISO-ish timestamp like '2026-05-11 15:36:35.59+00'."""
    if not value:
        return None
    s = value.strip().replace(" ", "T")
    # Normalise a bare numeric tz offset like '+00' -> '+00:00'.
    if re.search(r"[+-]\d{2}$", s):
        s += ":00"
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None


def _latency_seconds(created: Optional[str], completed: Optional[str]) -> float:
    """Return generation wall-clock seconds from two timestamps (0.0 if unknown)."""
    a, b = _parse_ts(created), _parse_ts(completed)
    if a and b:
        return round((b - a).total_seconds(), 3)
    return 0.0


# ---------------------------------------------------------------------------
# Dossier ("queries") flattening
# ---------------------------------------------------------------------------
def _md_list(items: Optional[List[Any]], bullet: str = "- ") -> str:
    if not items:
        return ""
    return "\n".join(f"{bullet}{x}" for x in items)


def flatten_dossier(result: Dict[str, Any], question: str) -> str:
    """Render a structured CTI dossier ``result`` into a markdown report.

    Preserves the substance the quality judges care about: citations, confidence
    language, ATT&CK technique IDs, IOCs, intelligence gaps, structure and sources.
    """
    if not isinstance(result, dict):
        return str(result)

    identity = result.get("identity") or {}
    attribution = identity.get("attribution") or {}
    primary = identity.get("primary_name") or "Unknown"

    out: List[str] = [f"# Threat Intelligence Dossier: {primary}", ""]

    if result.get("summary"):
        out += ["## Executive Summary", result["summary"], ""]

    # Identity & attribution
    out += ["## Identity & Attribution"]
    out += [f"- **Primary name:** {primary}"]
    if identity.get("aliases"):
        out += [f"- **Aliases:** {', '.join(identity['aliases'])}"]
    if attribution.get("suspected_origin"):
        out += [f"- **Suspected origin:** {attribution['suspected_origin']}"]
    if attribution.get("confidence"):
        out += [f"- **Attribution confidence:** {attribution['confidence']}"]
    if attribution.get("rationale"):
        out += [f"- **Rationale:** {attribution['rationale']}"]
    out += [""]

    if result.get("key_findings"):
        out += ["## Key Findings", _md_list(result["key_findings"]), ""]

    for section in result.get("sections") or []:
        title = section.get("title", "Section")
        out += [f"## {title}", section.get("content", ""), ""]

    if result.get("timeline"):
        out += ["## Timeline"]
        for ev in result["timeline"]:
            out += [f"- **{ev.get('date', '?')}:** {ev.get('event', '')}"]
        out += [""]

    if result.get("mitre_techniques"):
        out += ["## MITRE ATT&CK Techniques"]
        for t in result["mitre_techniques"]:
            out += [f"- **{t.get('id', '')} {t.get('name', '')}** — {t.get('rationale', '')}"]
        out += [""]

    if result.get("iocs"):
        out += ["## Indicators of Compromise"]
        for ioc in result["iocs"]:
            cat = ioc.get("category", "")
            conf = ioc.get("confidence", "")
            out += [
                f"- `[{cat}]` **{ioc.get('type', '')}**: {ioc.get('value', '')} "
                f"(confidence: {conf}) — {ioc.get('rationale', '')}"
            ]
        out += [""]

    if result.get("mitigations"):
        out += ["## Mitigations", _md_list(result["mitigations"]), ""]

    if result.get("pivot_points"):
        out += ["## Pivot Points", _md_list(result["pivot_points"]), ""]

    # Hunting queries (Sigma/KQL/Splunk/YARA/Snort) — include as fenced blocks.
    if result.get("hunting_recommendations"):
        out += ["## Hunting Recommendations"]
        for h in result["hunting_recommendations"]:
            out += [f"### {h.get('title', 'Query')} ({h.get('query_type', '')})"]
            if h.get("description"):
                out += [h["description"]]
            if h.get("query"):
                out += ["```", h["query"], "```"]
            out += [""]

    if result.get("gaps"):
        out += ["## Intelligence Gaps", _md_list(result["gaps"]), ""]

    if result.get("sources"):
        out += ["## Sources"]
        for src in result["sources"]:
            sid = src.get("id", "?")
            out += [f"[{sid}] {src.get('title', '')} — {src.get('url', '')}"]
        out += [""]

    return "\n".join(out).strip()


def convert_queries_file(data: Dict[str, Any], default_model: str) -> List[Dict[str, Any]]:
    """Convert a 'queries' export into a list of evaluator question objects."""
    questions: List[Dict[str, Any]] = []
    for i, q in enumerate(data.get("queries", [])):
        result = q.get("result") or {}
        question_text = q.get("query", "").strip()
        identity = (result.get("identity") or {})
        primary = identity.get("primary_name") or q.get("entity_id") or f"query-{i+1}"
        qid = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(primary).lower()).strip("-") or f"q{i+1}"
        answer = flatten_dossier(result, question_text)
        report = {
            "model": q.get("model") or default_model,
            "answer": answer,
            "cost": 0.0,  # not present in export — populate from real run metrics
            "latency_seconds": _latency_seconds(q.get("created_at"), q.get("completed_at")),
            "input_tokens": 0,  # not present in export
            "output_tokens": 0,  # not present in export
        }
        questions.append(
            {
                "question_id": qid,
                "question": question_text,
                "category": "actor_profile",
                "reports": [report],
            }
        )
    return questions


# ---------------------------------------------------------------------------
# Graph (D3FEND CAD) flattening
# ---------------------------------------------------------------------------
def _props_to_dict(user_properties: Any) -> Dict[str, str]:
    """Convert a list of [key, value] pairs into a dict."""
    out: Dict[str, str] = {}
    if isinstance(user_properties, list):
        for pair in user_properties:
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                out[str(pair[0])] = str(pair[1])
    return out


def flatten_graph(data: Dict[str, Any]) -> str:
    """Render a D3FEND CAD graph (nodes/edges) into a markdown CTI report."""
    meta = data.get("meta") or {}
    nodes = data.get("nodes") or []
    edges = data.get("edges") or []

    by_id: Dict[str, Dict[str, Any]] = {n.get("id"): n for n in nodes}

    def label(node_id: str) -> str:
        n = by_id.get(node_id)
        return (n.get("data", {}).get("label") if n else None) or node_id

    # Group nodes by type.
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for n in nodes:
        groups.setdefault(n.get("type", "other"), []).append(n)

    out: List[str] = [f"# {meta.get('title', 'Threat Intelligence Graph')}", ""]
    if meta.get("description"):
        out += ["## Overview", meta["description"], ""]

    def render_group(node_type: str, heading: str) -> None:
        items = groups.get(node_type, [])
        if not items:
            return
        out.append(f"## {heading}")
        for n in items:
            d = n.get("data", {})
            props = _props_to_dict(d.get("user_properties"))
            line = f"- **{d.get('label', n.get('id'))}**"
            if d.get("d3f_class"):
                line += f" ({d['d3f_class']})"
            out.append(line)
            for k, v in props.items():
                out.append(f"    - {k}: {v}")
        out.append("")

    render_group("agent-node", "Threat Actors")
    render_group("event-node", "Attack Lifecycle Events")
    render_group("vulnerability-node", "Vulnerabilities / Weaknesses")
    render_group("artifact-node", "Indicators & Artifacts (IOCs)")
    render_group("countermeasure-node", "Countermeasures / Detections")
    render_group("note-node", "Analyst Notes")

    # Relationships
    if edges:
        out += ["## Relationships"]
        for e in edges:
            rel = (e.get("data", {}) or {}).get("label", "related to")
            out.append(f"- {label(e.get('source'))} —{rel}→ {label(e.get('target'))}")
        out += [""]

    # References
    refs = [r for r in (meta.get("references") or []) if r]
    if refs:
        out += ["## References"]
        for r in refs:
            out.append(f"- {r}")
        out += [""]

    return "\n".join(out).strip()


def convert_graph_file(data: Dict[str, Any], default_model: str, source_name: str) -> List[Dict[str, Any]]:
    """Convert a graph export into a single evaluator question object."""
    meta = data.get("meta") or {}
    title = meta.get("title") or source_name
    # Synthesise a research question from the graph's description/title.
    question = (
        f"Produce a hunt-ready intelligence profile covering: {title}. "
        "Include attribution, aliases, TTPs mapped to MITRE ATT&CK, IOCs, "
        "infrastructure, timeline, detections/countermeasures, and intelligence gaps."
    )
    qid = re.sub(r"[^a-zA-Z0-9_-]+", "-", source_name.lower()).strip("-") or "graph"
    return [
        {
            "question_id": qid,
            "question": question,
            "category": "actor_profile",
            "reports": [
                {
                    "model": default_model,  # graph export records no model
                    "answer": flatten_graph(data),
                    "cost": 0.0,
                    "latency_seconds": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                }
            ],
        }
    ]


# ---------------------------------------------------------------------------
# Markdown export parsing (carries real cost + token counts in its footer)
# ---------------------------------------------------------------------------
def _parse_md_metrics(md_text: str) -> Dict[str, Any]:
    """Extract cost / prompt / completion tokens from a MIGHTYTOASTER .md export.

    The MD footer looks like:
        _20 articles · 1 entities · 7,349 prompt tokens · 3,050 completion tokens · $0.0641 cost_
    and the header carries `Cost $0.0641`. We read whichever is present.
    """
    metrics: Dict[str, Any] = {}
    tok = re.search(r"([\d,]+)\s+prompt tokens.*?([\d,]+)\s+completion tokens", md_text, re.I | re.S)
    if tok:
        metrics["input_tokens"] = int(tok.group(1).replace(",", ""))
        metrics["output_tokens"] = int(tok.group(2).replace(",", ""))
    cost = re.search(r"\$([0-9]+(?:\.[0-9]+)?)\s+cost", md_text, re.I) or re.search(
        r"Cost\s+\$([0-9]+(?:\.[0-9]+)?)", md_text, re.I
    )
    if cost:
        metrics["cost"] = float(cost.group(1))
    return metrics


def _parse_md_report(text: str) -> tuple[str, Optional[str], str, Dict[str, Any]]:
    """Parse a standalone .md export into (question, model, answer_body, metrics)."""
    question = ""
    for ln in text.splitlines():
        if ln.startswith("# "):
            question = ln[2:].strip()
            break
    model_match = re.search(r"Model\s+([A-Za-z0-9._-]+)", text)
    model = model_match.group(1) if model_match else None

    body = text
    body = re.sub(r"^_Tier .*?_\s*$", "", body, count=1, flags=re.M)  # drop metadata line
    # Drop the trailing footer block (after the last '---') if it carries cost/tokens.
    parts = body.rsplit("\n---\n", 1)
    if len(parts) == 2 and ("cost" in parts[1].lower() or "tokens" in parts[1].lower()):
        body = parts[0]
    body = re.sub(r"^#\s+.*?\n", "", body, count=1)  # drop the H1 (question) line
    return question, model, body.strip(), _parse_md_metrics(text)


def convert_md_file(path: Path, default_model: str) -> List[Dict[str, Any]]:
    """Convert a standalone .md export (no JSON sibling) into a question object."""
    text = path.read_text(encoding="utf-8")
    question, model, answer, metrics = _parse_md_report(text)
    return [
        {
            "question_id": _clean_qid(path.stem),
            "question": question,
            "category": "actor_profile",
            "reports": [
                {
                    "model": model or default_model,
                    "answer": answer,
                    "cost": metrics.get("cost", 0.0),
                    "latency_seconds": 0.0,  # not present in MD alone
                    "input_tokens": metrics.get("input_tokens", 0),
                    "output_tokens": metrics.get("output_tokens", 0),
                }
            ],
        }
    ]


def _clean_qid(stem: str) -> str:
    """Derive a clean question_id from a filename stem.

    Strips a trailing '-research-YYYY-MM-DD' suffix and a stray '.json' so
    'storm-1849-research-2026-06-09' -> 'storm-1849'.
    """
    s = re.sub(r"\.json$", "", stem)
    s = re.sub(r"-research-\d{4}-\d{2}-\d{2}$", "", s)
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", s).strip("-").lower()
    return s or "q"


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
def convert_file(path: Path, default_model: str) -> List[Dict[str, Any]]:
    """Detect the export format and convert one file."""
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "queries" in data:
        return convert_queries_file(data, default_model)
    if isinstance(data, dict) and "nodes" in data and "edges" in data:
        return convert_graph_file(data, default_model, source_name=path.stem)
    raise ValueError(f"Unrecognised MIGHTYTOASTER export format: {path.name}")


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="mightytoaster_adapter",
        description="Convert MIGHTYTOASTER export files into the evaluator dataset format.",
    )
    p.add_argument("files", nargs="+", help="MIGHTYTOASTER export files (.json and/or .md).")
    p.add_argument("--out", required=True, help="Output dataset JSON path.")
    p.add_argument(
        "--default-model",
        default="unknown",
        help="Model label to use when an export does not record one (e.g. graph exports).",
    )
    args = p.parse_args(argv)

    files = [Path(f) for f in args.files]
    # Pair .md exports (which carry real cost/token footers) with their .json
    # siblings (which carry the structured result + timestamps) by filename stem.
    md_by_stem = {f.stem: f for f in files if f.suffix.lower() == ".md"}

    questions: List[Dict[str, Any]] = []
    consumed_md: set[str] = set()

    # Pass 1: JSON / graph exports (preferred source for content + latency).
    for path in files:
        if path.suffix.lower() == ".md":
            continue
        converted = convert_file(path, args.default_model)
        if len(converted) == 1:
            converted[0]["question_id"] = _clean_qid(path.stem)
        sibling = md_by_stem.get(path.stem)
        if sibling is not None:
            metrics = _parse_md_metrics(sibling.read_text(encoding="utf-8"))
            for q in converted:
                for r in q["reports"]:
                    r.update(metrics)  # real cost / input_tokens / output_tokens
            consumed_md.add(path.stem)
        questions.extend(converted)
        for q in converted:
            r = q["reports"][0]
            print(
                f"  {path.name}: q='{q['question_id']}' model='{r['model']}' "
                f"answer={len(r['answer'])} chars latency={r['latency_seconds']}s "
                f"cost=${r['cost']} tokens={r['input_tokens']}+{r['output_tokens']}"
            )

    # Pass 2: standalone .md exports that had no JSON sibling.
    for stem, md in md_by_stem.items():
        if stem in consumed_md:
            continue
        converted = convert_md_file(md, args.default_model)
        questions.extend(converted)
        r = converted[0]["reports"][0]
        print(
            f"  {md.name} (md-only): q='{converted[0]['question_id']}' model='{r['model']}' "
            f"answer={len(r['answer'])} chars cost=${r['cost']} tokens={r['input_tokens']}+{r['output_tokens']}"
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(questions, fh, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(questions)} question(s) to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
