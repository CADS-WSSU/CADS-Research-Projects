"""Build the query string fed to the relevance reranker.

The bare analytic questions are terse ("Who is Macron?"), which the cross-encoder
under-scores against topically-relevant news docs. Enriching the query with the topic
narrative (and, when available, the question's acceptable answers) gives the reranker
enough context to recognize relevant docs, without affecting silence (nil-day docs still
don't match the enriched query). Controlled by [relevance].query_enrich in config.
"""
from __future__ import annotations


def build_relevance_query(cfg: dict, topic: dict, question_text: str) -> str:
    mode = cfg.get("relevance", {}).get("query_enrich", "none")
    if mode == "none":
        return question_text
    narrative = (topic or {}).get("narrative", "") or ""
    parts = []
    if narrative:
        parts.append(narrative.strip())
    parts.append(f"Question: {question_text}")
    return "\n".join(parts)
