"""Write the complete :class:`Results` artifact to ``results.json``.

``math.inf`` is not valid JSON. Pydantic's ``model_dump`` leaves floats as Python
``inf``; we serialise with ``json.dump(..., allow_nan=False)`` would raise, so we
instead convert non-finite floats to the string ``"Infinity"`` recursively before
dumping. This keeps the file strictly valid JSON while preserving the meaning for
free/local models.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from models.schemas import Results


def _sanitize(obj: Any) -> Any:
    """Recursively replace non-finite floats with JSON-safe string sentinels."""
    if isinstance(obj, float):
        if math.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        if math.isnan(obj):
            return "NaN"
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


def write_results_json(results: Results, out_path: str | Path) -> Path:
    """Serialise the full results bundle to a strictly-valid JSON file."""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _sanitize(results.model_dump())
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, allow_nan=False)
    return path
