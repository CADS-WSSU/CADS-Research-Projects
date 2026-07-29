"""Offline feature pre-cache (content terms + named entities) for fast dev tuning.

Same rationale as precompute_embeddings: per-document features are content-only and
independent of threshold/memory, so computing them once (spaCy NER batched across CPU
cores) makes every M6 sweep combo a cache hit instead of re-running NER. Offline-only;
does not affect the temporal constraint.

Key: spaCy worker processes are spawned ONCE by a single nlp.pipe() pass over the whole
stream (using as_tuples to carry doc ids), then results are written to the cache in
chunks. Already-cached docs are skipped so the job is resumable.

Run:
    python -m cdet2026.precompute_features
"""
from __future__ import annotations

import spacy
from cdet_api.models import Document, db

from .config import load_config
from .scorers.local_novelty import DocFeatureCache
from .text_utils import content_terms

N_PROCESS = 10
WRITE_EVERY = 5000


def main() -> None:
    cfg = load_config()
    nlp = spacy.load(cfg["novelty"]["spacy_model"],
                     disable=["lemmatizer", "tagger", "attribute_ruler", "parser"])
    cache = DocFeatureCache(cfg["paths"]["embeddings_cache"] + "/docfeat.sqlite")

    db.connect(reuse_if_open=True)
    total = Document.select().count()
    have = {row[0] for row in cache.conn.execute("SELECT id FROM feat")}
    print(f"{total} docs; {len(have)} already cached; computing the rest.", flush=True)

    def stream():
        for row in Document.select(Document.id, Document.text).iterator():
            if row.id not in have:
                yield (row.text[:4000], row.id)

    buf: dict = {}
    done = 0
    for doc, did in nlp.pipe(stream(), as_tuples=True, n_process=N_PROCESS, batch_size=128):
        buf[did] = (content_terms(doc.text), {ent.text.lower() for ent in doc.ents})
        done += 1
        if len(buf) >= WRITE_EVERY:
            cache.put_many(buf)
            buf = {}
            print(f"  {done} computed (cache {len(have) + done})", flush=True)
    if buf:
        cache.put_many(buf)

    n = cache.conn.execute("SELECT COUNT(*) FROM feat").fetchone()[0]
    print(f"Done. Newly computed {done}; feature cache holds {n} docs.", flush=True)


if __name__ == "__main__":
    main()
