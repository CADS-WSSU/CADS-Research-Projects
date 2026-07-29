"""Lightweight boilerplate stripper for the corpus documents (A3).

The corpus `text` is already extracted from HTML but still carries site chrome —
navigation menus, "Skip to content", cookie/subscribe banners, "Related"/"Most read"
link lists — typically at the top, which then dominates the first reranker chunk. This
removes short nav-like lines and keeps prose, so the cross-encoder reads article content.
Heuristic and conservative: if cleaning would remove almost everything, it returns the
original text (never strips a doc to nothing).
"""
from __future__ import annotations

import re

_BOILER = re.compile(
    r"^(skip to|menu$|search$|subscribe|sign in|log ?in|register$|advertisement|"
    r"share (this|on)|newsletter|follow us|cookie|we use cookies|accept all|"
    r"read more|related stories|related articles|most read|most popular|trending|"
    r"home$|sections?$|more from|sponsored|©|all rights reserved)",
    re.IGNORECASE,
)
_MIN_WORDS = 7          # prose lines have >= this many words; shorter lines are nav-like
_MIN_KEPT_CHARS = 150   # if cleaning leaves less than this, fall back to the original


def clean_text(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines()]
    kept: list[str] = []
    for ln in lines:
        if not ln or _BOILER.match(ln):
            continue
        words = ln.split()
        # keep sentences (>= MIN_WORDS) or anything ending in sentence punctuation
        if len(words) >= _MIN_WORDS or ln[-1:] in ".?!":
            kept.append(ln)
    out = "\n".join(kept).strip()
    return out if len(out) >= _MIN_KEPT_CHARS else text
