"""Offline embedding pre-cache for fast dev tuning.

Embeds every document once into the doc-id-keyed cache (embeddings_cache/emb.sqlite),
so M6 sweeps are pure cache hits instead of re-embedding ~1M docs per pass.

This is OFFLINE TUNING infrastructure only and does not affect the temporal constraint:
embeddings are per-document and order-independent, and the production day loop
(day_loop.py) still embeds only the current day's docs and only ever compares
within-day. Pre-caching does not leak future-document information into any day's
decision — it just memoizes content vectors.

Run:
    python -m cdet2026.precompute_embeddings
"""
from __future__ import annotations

from cdet_api.models import Document, db

from .config import load_config
from .embeddings import Embedder

BATCH = 512


def main() -> None:
    cfg = load_config()
    rc = cfg["relevance"]
    embedder = Embedder(
        model_name=rc["model"],
        device=rc["device"],
        cache_path=cfg["paths"]["embeddings_cache"] + "/emb.sqlite",
        batch_size=256,
    )
    db.connect(reuse_if_open=True)
    total = Document.select().count()
    already = embedder.cache.conn.execute("SELECT COUNT(*) FROM emb").fetchone()[0]
    print(f"{total} docs in db; {already} already cached.")

    ids: list[str] = []
    texts: list[str] = []
    done = 0
    # Stream all docs; encode_docs skips those already cached and stores the rest.
    for row in Document.select(Document.id, Document.text).iterator():
        ids.append(row.id)
        texts.append(row.text)
        if len(ids) >= BATCH:
            embedder.encode_docs(ids, texts)
            done += len(ids)
            ids, texts = [], []
            if done % (BATCH * 20) == 0:
                cached = embedder.cache.conn.execute("SELECT COUNT(*) FROM emb").fetchone()[0]
                print(f"  processed {done}/{total}  (cache size {cached})")
    if ids:
        embedder.encode_docs(ids, texts)
        done += len(ids)

    cached = embedder.cache.conn.execute("SELECT COUNT(*) FROM emb").fetchone()[0]
    print(f"Done. Processed {done}; cache now holds {cached} vectors.")
    embedder.close()


if __name__ == "__main__":
    main()
