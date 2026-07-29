"""LLM new-question proposal (TREC Change Detection, optional; LLM-run only).

The track lets a system propose NEW analytic questions and add them to a topic's question
ranking from the day they are proposed (their qid must start with the runtag). This module
implements a CONSERVATIVE proposer:

  1. Find the day's documents that are on-topic for the TOPIC (bi-encoder cosine to the
     topic narrative) but are NOT covered by any existing question that day.
  2. Cluster them (embedding cosine); require a corroborated cluster (>= min_cluster
     distinct documents) — a single stray document never triggers a proposal.
  3. Require novelty vs. already-proposed questions (don't re-propose the same emerging
     theme on later days).
  4. Ask a leak-free LLM whether the cluster raises ONE new analytic question that is
     genuinely distinct from the existing questions, and to phrase it (or abstain).

It is generative, so it lives only in the LLM run. It is off by default ([propose].enable).
Because proposed questions have no ground truth locally, this component is validated
qualitatively (see gold_testset/demo_propose.py) and scored by NIST post-hoc.
"""
from __future__ import annotations

import json

import numpy as np

from .embeddings import Embedder

_PROMPT = """You are helping an intelligence analyst track a TOPIC over time. Below are \
several NEWS DOCUMENTS from a single day that are on-topic but are NOT answered by any of \
the analyst's EXISTING QUESTIONS. Decide whether they collectively raise ONE new analytic \
question about the topic that is genuinely DISTINCT from the existing questions (not a \
rephrasing or a sub-case of one).

Return ONLY JSON: {{"propose": true/false, "question": "<one concise analytic question, or empty>"}}.
Propose only if the documents clearly warrant a new standing question; otherwise propose false.

TOPIC: {topic}

EXISTING QUESTIONS:
{existing}

DOCUMENTS (excerpts):
{docs}
"""


class QuestionProposer:
    """One instance per run; holds an embedder and per-topic proposed-question state."""

    def __init__(self, cfg: dict):
        pc = cfg.get("propose", {})
        rc = cfg["relevance"]
        self.enable = bool(pc.get("enable", False))
        self.topic_cos = float(pc.get("topic_cos_thr", 0.35))
        self.cluster_cos = float(pc.get("cluster_cos_thr", 0.75))
        self.min_cluster = int(pc.get("min_cluster", 3))
        self.dedup_cos = float(pc.get("dedup_cos_thr", 0.85))
        self.max_per_day = int(pc.get("max_per_topic_per_day", 1))
        self.doc_chars = int(pc.get("doc_chars", 700))
        self.n_docs_shown = int(pc.get("n_docs_shown", 6))
        self.model = pc.get("model") or rc.get("llm_rescue_model")
        self.embedder = None
        if self.enable:
            self.embedder = Embedder(rc["model"], rc.get("device", "cuda"),
                                     cfg["paths"]["embeddings_cache"] + "/emb.sqlite",
                                     batch_size=int(rc.get("batch_size", 64)))
        self._client = None
        self.proposed: dict[str, list] = {}   # tid -> [{qid, question, centroid}]
        self.calls = 0

    def topic_query(self, topic: dict) -> str:
        return (topic.get("narrative") or topic.get("label")
                or " ".join(q["question"] for q in topic.get("questions", [])))

    def propose(self, topic: dict, day: str, day_docs, claimed_ids: set, runtag: str) -> list[dict]:
        """Return newly proposed questions for (topic, day): [{qid, question, doc_ids}]."""
        if not self.enable or not day_docs:
            return []
        tid = topic["tid"]
        ids = [d.id for d in day_docs]
        texts = [d.text for d in day_docs]
        mat = self.embedder.encode_docs(ids, texts)                 # cached
        qv = self.embedder.encode_query(self.topic_query(topic))
        cos = mat @ qv
        # on-topic AND unclaimed by existing questions
        idx = [i for i in range(len(ids))
               if cos[i] >= self.topic_cos and ids[i] not in claimed_ids]
        if len(idx) < self.min_cluster:
            return []
        sub = mat[idx]
        S = sub @ sub.T
        sizes = (S >= self.cluster_cos).sum(axis=1)
        out = []
        used = set()
        for _ in range(self.max_per_day):
            seed = int(np.argmax([s if i not in used else -1 for i, s in enumerate(sizes)]))
            if sizes[seed] < self.min_cluster or seed in used:
                break
            members = [j for j in range(len(idx)) if S[seed][j] >= self.cluster_cos and j not in used]
            if len(members) < self.min_cluster:
                break
            used.update(members)
            centroid = sub[members].mean(axis=0)
            centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
            # novelty vs already-proposed questions for this topic
            prev = self.proposed.get(tid, [])
            if any(float(centroid @ p["centroid"]) >= self.dedup_cos for p in prev):
                continue
            cluster_docs = [day_docs[idx[j]] for j in members]
            q = self._ask_llm(topic, cluster_docs)
            if not q:
                continue
            seq = len(self.proposed.get(tid, [])) + 1
            qid = f"{runtag}_{tid}_{seq}"
            self.proposed.setdefault(tid, []).append({"qid": qid, "question": q, "centroid": centroid})
            out.append({"qid": qid, "question": q,
                        "doc_ids": [d.id for d in cluster_docs]})
        return out

    def _ask_llm(self, topic: dict, cluster_docs) -> str | None:
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()
        existing = "\n".join(f"- {q['question']}" for q in topic.get("questions", [])) or "(none)"
        docs = "\n\n".join(f"[{i+1}] {d.text[:self.doc_chars]}" for i, d in enumerate(cluster_docs[:self.n_docs_shown]))
        prompt = _PROMPT.format(topic=self.topic_query(topic)[:600], existing=existing, docs=docs)
        self.calls += 1
        try:
            r = self._client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": prompt}], temperature=0.0)
            raw = r.choices[0].message.content or ""
            a, b = raw.find("{"), raw.rfind("}")
            if a != -1 and b != -1:
                obj = json.loads(raw[a:b + 1])
                if obj.get("propose") and obj.get("question", "").strip():
                    return obj["question"].strip()
        except Exception:  # noqa: BLE001 — conservative: no proposal on any failure
            pass
        return None

    def close(self):
        if self.embedder is not None:
            self.embedder.close()
