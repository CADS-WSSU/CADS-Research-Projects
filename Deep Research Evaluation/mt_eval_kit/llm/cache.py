"""On-disk JSON response cache for judge calls.

Deterministic evaluation depends on this: identical requests (temperature 0, fixed
seed) are served byte-for-byte from disk on re-runs, so benchmarks are reproducible
and repeat runs cost nothing. One JSON file per entry, named by the SHA-256 of the
request key — human-inspectable and dependency-free.
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Any, Dict, Optional


class ResponseCache:
    """Persist judge responses keyed by a hash of the request."""

    def __init__(self, directory: str | Path, *, enabled: bool = True) -> None:
        self.directory = Path(directory)
        self.enabled = enabled
        self._lock = threading.Lock()
        if self.enabled:
            self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _hash(key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _path_for(self, key: str) -> Path:
        return self.directory / f"{self._hash(key)}.json"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Return the cached object for ``key`` or ``None`` on a miss."""
        if not self.enabled:
            return None
        path = self._path_for(key)
        if not path.exists():
            return None
        with self._lock:
            try:
                with path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError):
                return None  # corrupt entry behaves as a miss

    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Store ``value`` under ``key`` (atomic temp-file rename)."""
        if not self.enabled:
            return
        path = self._path_for(key)
        tmp = path.with_suffix(".json.tmp")
        with self._lock:
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(value, fh, ensure_ascii=False, indent=2)
            tmp.replace(path)

    def clear(self) -> int:
        """Delete all entries; return count removed."""
        if not self.directory.exists():
            return 0
        count = 0
        with self._lock:
            for path in self.directory.glob("*.json"):
                path.unlink()
                count += 1
        return count
