"""Local sentence-embedding model (bge-small-en-v1.5 on MPS) with a disk-backed
cache keyed by document id, so a re-run never re-embeds a document. Only the current
day's documents are ever embedded inside the loop (plan: M2 constraint).

Cache is a single SQLite file (id TEXT PRIMARY KEY -> float32 blob); keying by doc id
keeps it idempotent and resumable regardless of which day a doc shows up on.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np

from .config import ROOT

# bge-v1.5 retrieval convention: prepend an instruction to the *query* only.
BGE_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class EmbeddingCache:
    def __init__(self, path: str | Path, dim: int):
        p = Path(path)
        if not p.is_absolute():
            p = ROOT / p
        p.parent.mkdir(parents=True, exist_ok=True)
        self.dim = dim
        self.conn = sqlite3.connect(str(p))
        self.conn.execute("CREATE TABLE IF NOT EXISTS emb (id TEXT PRIMARY KEY, vec BLOB)")
        self.conn.commit()

    def get_many(self, ids: list[str]) -> dict[str, np.ndarray]:
        out: dict[str, np.ndarray] = {}
        # chunk to stay under SQLite's variable limit
        for i in range(0, len(ids), 900):
            chunk = ids[i : i + 900]
            q = f"SELECT id, vec FROM emb WHERE id IN ({','.join('?' * len(chunk))})"
            for did, blob in self.conn.execute(q, chunk):
                out[did] = np.frombuffer(blob, dtype=np.float32)
        return out

    def put_many(self, items: dict[str, np.ndarray]) -> None:
        self.conn.executemany(
            "INSERT OR REPLACE INTO emb (id, vec) VALUES (?, ?)",
            [(did, vec.astype(np.float32).tobytes()) for did, vec in items.items()],
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


def _l2_normalize(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=-1, keepdims=True)
    norms[norms == 0] = 1.0
    return m / norms


class Embedder:
    """Wraps a SentenceTransformer; returns L2-normalized vectors so cosine == dot."""

    def __init__(self, model_name: str, device: str, cache_path: str | Path, batch_size: int = 64):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name, device=device)
        self.device = device
        self.batch_size = batch_size
        self.dim = (
            self.model.get_embedding_dimension()
            if hasattr(self.model, "get_embedding_dimension")
            else self.model.get_sentence_embedding_dimension()
        )
        self.cache = EmbeddingCache(cache_path, self.dim)

    def encode_query(self, text: str) -> np.ndarray:
        v = self.model.encode(
            [BGE_QUERY_INSTRUCTION + text],
            batch_size=1,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        return v.astype(np.float32)

    def encode_docs(self, ids: list[str], texts: list[str]) -> np.ndarray:
        """Return an (n, dim) matrix aligned with `ids`. Cached docs are read from disk;
        only uncached docs are embedded, then written back."""
        cached = self.cache.get_many(ids)
        missing_idx = [i for i, did in enumerate(ids) if did not in cached]
        if missing_idx:
            new_vecs = self.model.encode(
                [texts[i] for i in missing_idx],
                batch_size=self.batch_size,
                normalize_embeddings=True,
                show_progress_bar=False,
            ).astype(np.float32)
            to_store = {ids[i]: new_vecs[j] for j, i in enumerate(missing_idx)}
            self.cache.put_many(to_store)
            cached.update(to_store)
        return np.vstack([cached[did] for did in ids])

    def close(self) -> None:
        self.cache.close()
