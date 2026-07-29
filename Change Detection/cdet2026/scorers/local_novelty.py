"""Default novelty scorer (LLM-free): a blend of three local signals measured against
a question's memory of already-accepted docs:

    novelty = w_cos * (1 - max_cosine_to_memory)
            + w_terms * fraction_of_terms_new_to_this_question
            + w_ents  * fraction_of_named_entities_new_to_this_question

Named entities come from local spaCy (en_core_web_sm). When the memory is empty
(nothing accepted yet for the question), every candidate is fully novel -> 1.0.

Per-document features (content terms + entity set) are content-only and independent of
threshold/memory, so they are cached on disk keyed by doc id and computed at most once
across the whole run/sweep, with spaCy batched via nlp.pipe. The term/entity sets are
also stashed on each Candidate so the policy can hand them to MemoryStore.add.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from ..config import ROOT
from ..text_utils import content_terms
from .base import Candidate, NoveltyScorer

_SEP = ""


class DocFeatureCache:
    """doc id -> (content-term set, named-entity set), persisted in SQLite."""

    def __init__(self, path: str | Path):
        p = Path(path)
        if not p.is_absolute():
            p = ROOT / p
        p.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(p))
        self.conn.execute("CREATE TABLE IF NOT EXISTS feat (id TEXT PRIMARY KEY, terms TEXT, ents TEXT)")
        self.conn.commit()

    def get_many(self, ids: list[str]) -> dict[str, tuple[set, set]]:
        out: dict[str, tuple[set, set]] = {}
        for i in range(0, len(ids), 900):
            chunk = ids[i : i + 900]
            q = f"SELECT id, terms, ents FROM feat WHERE id IN ({','.join('?' * len(chunk))})"
            for did, terms, ents in self.conn.execute(q, chunk):
                out[did] = (
                    set(terms.split(_SEP)) if terms else set(),
                    set(ents.split(_SEP)) if ents else set(),
                )
        return out

    def put_many(self, items: dict[str, tuple[set, set]]) -> None:
        self.conn.executemany(
            "INSERT OR REPLACE INTO feat (id, terms, ents) VALUES (?, ?, ?)",
            [(did, _SEP.join(t), _SEP.join(e)) for did, (t, e) in items.items()],
        )
        self.conn.commit()


class LocalNoveltyScorer(NoveltyScorer):
    def __init__(self, cfg: dict):
        import spacy

        nc = cfg["novelty"]
        self.w_cos = float(nc["w_cos"])
        self.w_terms = float(nc["w_terms"])
        self.w_ents = float(nc["w_ents"])
        self.nlp = spacy.load(nc["spacy_model"], disable=["lemmatizer", "tagger", "attribute_ruler"])
        self.cache = DocFeatureCache(cfg["paths"]["embeddings_cache"] + "/docfeat.sqlite")

    def _features(self, candidates: list[Candidate]) -> dict[str, tuple[set, set]]:
        """Return {doc_id: (terms, ents)} for the candidates, using the disk cache and
        computing only the missing ones (spaCy batched)."""
        ids = [c.doc_id for c in candidates]
        cached = self.cache.get_many(ids)
        missing = [c for c in candidates if c.doc_id not in cached]
        if missing:
            texts = [c.text[:4000] for c in missing]
            new: dict[str, tuple[set, set]] = {}
            for c, doc in zip(missing, self.nlp.pipe(texts, batch_size=64)):
                terms = content_terms(c.text)
                ents = {ent.text.lower() for ent in doc.ents}
                new[c.doc_id] = (terms, ents)
            self.cache.put_many(new)
            cached.update(new)
        return cached

    def attach_features(self, candidates: list[Candidate]) -> None:
        """Populate c.extra['terms'] and c.extra['entities'] (cache-backed, spaCy batched)."""
        feats = self._features(candidates)
        for c in candidates:
            c.extra["terms"], c.extra["entities"] = feats[c.doc_id]

    def novelty_against(self, emb, terms, ents, mem_embs, mem_terms, mem_ents) -> float:
        """Novelty blend of a candidate vs an arbitrary working memory (embeddings list +
        term/entity sets). Empty memory -> 1.0. Used for incremental within-day dedup."""
        if not mem_embs:
            return 1.0
        import numpy as np
        cos_nov = 1.0 - float(np.max(np.vstack(mem_embs) @ emb))
        t_new = len(terms - mem_terms) / len(terms) if terms else 0.0
        e_new = len(ents - mem_ents) / len(ents) if ents else 0.0
        return self.w_cos * cos_nov + self.w_terms * t_new + self.w_ents * e_new

    def score_day(self, question_memory, candidates: list[Candidate]) -> None:
        feats = self._features(candidates)
        for c in candidates:
            terms, ents = feats[c.doc_id]
            c.extra["terms"] = terms
            c.extra["entities"] = ents

            if question_memory.is_empty:
                cos_nov, t_new, e_new = 1.0, 1.0, 1.0
            else:
                cos_nov = 1.0 - question_memory.max_cosine(c.embedding)
                t_new = len(terms - question_memory.terms) / len(terms) if terms else 0.0
                e_new = len(ents - question_memory.entities) / len(ents) if ents else 0.0

            c.novelty = self.w_cos * cos_nov + self.w_terms * t_new + self.w_ents * e_new
            c.extra["nov_cos"] = cos_nov
            c.extra["nov_terms"] = t_new
            c.extra["nov_ents"] = e_new
