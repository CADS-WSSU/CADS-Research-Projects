"""Stage-A relevance tuning on the ragtime25_english dataset (30 gold topics).

Stage A is treated as solid ground truth (every per-question relevant doc is a NIST-gold
topic-relevant doc; only the question routing is inferred). Stage B/C are directional
and not used here.

Efficient design (no slow temporal capture): the reranker score of (question, doc) is
day-independent, so we measure the recall/silence tradeoff directly:
  RECALL  — reranker probability of every gold (question, relevant-doc) pair, plus the
            doc's cosine rank on its day (to confirm the top-N pre-filter doesn't drop it).
  SILENCE — for a sample of (question, nil-day) pairs, the max reranker probability over
            the day's top-N cosine candidates (the false-fire risk).

Pick the reranker threshold from recall(thr) vs false-fire(thr) across 30 topics.

Run:
    python -m cdet2026.tune_stageA --recall          # fast
    python -m cdet2026.tune_stageA --silence --nil-per-q 4
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict

import numpy as np
from cdet_api.models import Day, Document, db

from .config import ROOT, load_config
from .embeddings import Embedder
from .scorers.reranker_relevance import RerankScoreCache, _chunks, _qhash

DATA = ROOT / "ragtime25_english"
THRESHOLDS = [0.05, 0.10, 0.20, 0.30, 0.50]


def load_dataset():
    topics = [json.loads(l) for l in open(DATA / "topics.jsonl")]
    doc_day = {}
    for l in open(DATA / "qrels.jsonl"):
        d = json.loads(l)
        doc_day[d["doc_id"]] = d["day"]
    return topics, doc_day


def _cap(cache: dict, limit: int = 40):
    """Evict oldest entries so the per-day doc/embedding cache can't balloon memory."""
    while len(cache) > limit:
        cache.pop(next(iter(cache)))


def _ce_prob(ce, cfg, question, text):
    rc = cfg["relevance"]
    chunks = _chunks(text, int(rc["chunk_chars"]), int(rc["chunk_overlap"]), int(rc["max_chunks"]))
    return float(np.max(ce.predict([(question, c) for c in chunks], show_progress_bar=False)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recall", action="store_true")
    ap.add_argument("--silence", action="store_true")
    ap.add_argument("--nil-per-q", type=int, default=2)
    args = ap.parse_args()
    if not (args.recall or args.silence):
        args.recall = args.silence = True

    cfg = load_config(); rc = cfg["relevance"]
    from sentence_transformers import CrossEncoder
    ce = CrossEncoder(rc["reranker_model"], device=rc["device"], max_length=512)
    emb = Embedder(rc["model"], rc["device"], cfg["paths"]["embeddings_cache"] + "/emb.sqlite")
    cache = RerankScoreCache(cfg["paths"]["embeddings_cache"] + "/rerank.sqlite")
    topics, doc_day = load_dataset()
    db.connect(reuse_if_open=True)
    print(f"dataset: {len(topics)} topics, "
          f"{sum(len(t['questions']) for t in topics)} questions")

    if args.recall:
        probs, ranks, missing = [], [], 0
        daycache = {}
        for t in topics:
            for q in t["questions"]:
                qh = _qhash(q["question"])
                for did in q.get("rel_docs", []):
                    row = Document.get_or_none(Document.id == did)
                    if row is None:
                        missing += 1; continue
                    cached = cache.get_many(qh, [did])
                    if did in cached:
                        p = cached[did]
                    else:
                        p = _ce_prob(ce, cfg, q["question"], row.text)
                        cache.put_many(qh, {did: p})
                    probs.append(p)
                    # cosine rank of this doc among its day's docs (prefilter survival)
                    day = row.day
                    if day not in daycache:
                        rows = list(Document.select().where(Document.day == day))
                        daycache[day] = ([r.id for r in rows],
                                         emb.encode_docs([r.id for r in rows], [r.text for r in rows]))
                        _cap(daycache)
                    ids, mat = daycache[day]
                    qv = emb.encode_query(q["question"])
                    cos = mat @ qv
                    ranks.append(int((cos > cos[ids.index(did)]).sum()) + 1)
        probs = np.array(probs); ranks = np.array(ranks)
        print(f"\nRECALL side — {len(probs)} gold (question,relevant-doc) pairs ({missing} docs missing)")
        print(f"  reranker prob: p25={np.percentile(probs,25):.3f} median={np.percentile(probs,50):.3f} p75={np.percentile(probs,75):.3f}")
        n = int(rc["prefilter_n"])
        print(f"  cosine-rank of gold doc on its day: median={int(np.median(ranks))}  "
              f"in top-{n}: {(ranks<=n).mean():.3f}  in top-10: {(ranks<=10).mean():.3f}")
        print("  recall @ reranker-threshold (gate-pass on gold docs):")
        for thr in THRESHOLDS:
            print(f"    >={thr}: {(probs>=thr).mean():.3f}", flush=True)

    if args.silence:
        rng = random.Random(13)
        all_days = [d.day for d in Day.select().order_by(Day.seq_day)]
        daycache = {}
        maxprobs = []
        for t in topics:
            reld = set()
            for q in t["questions"]:
                for did in q.get("rel_docs", []):
                    if did in doc_day:
                        reld.add(doc_day[did])
            nil_days = [d for d in all_days if d not in reld]
            for q in t["questions"]:
                qh = _qhash(q["question"]); qv = emb.encode_query(q["question"])
                for day in rng.sample(nil_days, min(args.nil_per_q, len(nil_days))):
                    if day not in daycache:
                        rows = list(Document.select().where(Document.day == day))
                        daycache[day] = ([r.id for r in rows], [r.text for r in rows],
                                         emb.encode_docs([r.id for r in rows], [r.text for r in rows]))
                        _cap(daycache)
                    ids, texts, mat = daycache[day]
                    cos = mat @ qv
                    top = np.argsort(-cos)[: int(rc["prefilter_n"])]
                    cached = cache.get_many(qh, [ids[i] for i in top])
                    best = max(cached.values()) if cached else 0.0
                    for i in top:
                        if ids[i] not in cached:
                            p = _ce_prob(ce, cfg, q["question"], texts[i])
                            cache.put_many(qh, {ids[i]: p}); best = max(best, p)
                    maxprobs.append(best)
        mp = np.array(maxprobs)
        print(f"\nSILENCE side — {len(mp)} sampled (question,nil-day) pairs (~{args.nil_per_q}/question)")
        print(f"  max reranker prob on nil day: median={np.percentile(mp,50):.3f} p90={np.percentile(mp,90):.3f} p95={np.percentile(mp,95):.3f}")
        print("  false-fire @ reranker-threshold:")
        for thr in THRESHOLDS:
            print(f"    >={thr}: {(mp>=thr).mean():.3f}", flush=True)
    emb.close()


if __name__ == "__main__":
    main()
