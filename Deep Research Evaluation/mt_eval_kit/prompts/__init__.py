"""Prompt template loader.

Prompts are plain ``.md`` files so analysts can edit them without touching Python.
Templates use ``str.format`` placeholders (``{question}``, ``{report}``, ...).
:func:`render` loads by name and substitutes; templates are cached after first read.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROMPT_DIR = Path(__file__).parent


@lru_cache(maxsize=None)
def _load_raw(name: str) -> str:
    path = _PROMPT_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def render(name: str, **variables: object) -> str:
    """Return prompt ``name`` with ``{placeholders}`` filled from ``variables``."""
    template = _load_raw(name)

    class _SafeDict(dict):
        def __missing__(self, key: str) -> str:  # pragma: no cover - defensive
            raise KeyError(f"Prompt '{name}' references {{{key}}} but it was not provided.")

    return template.format_map(_SafeDict(variables))
