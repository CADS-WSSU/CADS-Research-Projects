"""Combined topic-day LLM gate (leaner LLM architecture; ADDITIVE — the reranker + 3-doc
rescue path in policy.py is untouched).

Instead of K per-(question,doc) rescue calls, make ONE LLM call per (topic, day) that reviews
the day's top-M candidate documents against ALL of the topic's questions at once, given each
question's prior-knowledge summary, and returns — per question — the relevant NEW documents with
graded gain 0/1/5/10. One call therefore fuses relevance + novelty + grading + question/doc
ranking, and directly yields the question ranking (the primary metric).

Why it is cheaper (no recall loss): it amortizes the rubric and reviews each candidate doc once
for the whole topic rather than re-sending rubric+doc per question-doc pair (~3x fewer tokens on
the test collection). It does NOT skip days (triage was measured to cost recall), so coverage is
preserved. Leak-free: uses a Claude model, disjoint from the gpt gold judge.

Not wired into the default pipeline; driven by gold_testset/score_topicday.py for evaluation.
"""
from __future__ import annotations

import json

import numpy as np

from .embeddings import Embedder
from .scorers import Candidate

VALID = {0, 1, 5, 10}

RUBRIC = """You are an intelligence analyst tracking a TOPIC day by day. For ONE day, decide \
which of the analyst's QUESTIONS received relevant NEW information, and which documents support \
them. Judge NOVELTY against each question's PRIOR KNOWLEDGE: a document that only repeats what is \
already known is not an update today.

For each question that has relevant NEW information today, grade its update on the TREC scale:
  1 = on topic but minor / mostly a restatement
  5 = moderately important new information
  10 = a vital new development today
List the supporting document numbers (from CANDIDATES) for each such question, best first.
Omit questions with nothing relevant/new today (do NOT list them).

Return ONLY JSON: {"questions": [{"qid": "...", "gain": 1|5|10, "docs": [<candidate numbers>],
"new_facts": ["..."]}, ...]}  (empty list if nothing today)."""


class TopicDayGate:
    def __init__(self, cfg: dict, model: str | None = None):
        rc = cfg["relevance"]
        pc = cfg.get("topicday", {})
        self.embedder = Embedder(rc["model"], rc.get("device", "cuda"),
                                 cfg["paths"]["embeddings_cache"] + "/emb.sqlite",
                                 batch_size=int(rc.get("batch_size", 64)))
        self.model = model or pc.get("model") or rc.get("llm_rescue_model")
        self.top_m = int(pc.get("top_m", 20))            # candidate docs shown per topic-day
        self.doc_chars = int(pc.get("doc_chars", 1400))
        self.max_summary = int(pc.get("max_summary_facts", 40))
        self._client = None
        self.calls = 0
        self.summaries: dict[tuple, list] = {}           # (tid, qid) -> running facts

    # ---- one combined call per topic-day ----
    def decide(self, topic: dict, day: str, day_docs):
        tid = topic["tid"]
        qs = topic["questions"]
        if not day_docs:
            return {q["qid"]: [] for q in qs}
        ids = [d.id for d in day_docs]
        texts = [getattr(d, "text", "") for d in day_docs]
        mat = self.embedder.encode_docs(ids, texts)
        qmat = np.vstack([self.embedder.encode_query(q["question"]) for q in qs])
        # candidate pool = union of top docs by max cosine to ANY question
        peak = (mat @ qmat.T).max(axis=1)
        order = np.argsort(-peak)[: self.top_m]
        cand = [(int(i), ids[int(i)], texts[int(i)]) for i in order]

        qblock = []
        for q in qs:
            prior = "; ".join(self.summaries.get((tid, q["qid"]), [])) or "(none yet)"
            qblock.append(f'- {q["qid"]}: {q["question"]}\n    prior knowledge: {prior}')
        cblock = "\n\n".join(f"[{n}] {t[:self.doc_chars]}" for n, (_i, _did, t) in enumerate(cand))
        prompt = (f"{RUBRIC}\n\nTOPIC: {topic.get('label','')} — {topic.get('narrative','')[:500]}\n\n"
                  f"QUESTIONS (with prior knowledge):\n" + "\n".join(qblock) +
                  f"\n\nCANDIDATE DOCUMENTS (published {day}):\n{cblock}\n")
        verdict = self._call(prompt)

        idx_to_docid = {n: did for n, (_i, did, _t) in enumerate(cand)}
        out = {q["qid"]: [] for q in qs}
        for item in verdict.get("questions", []):
            qid = str(item.get("qid", ""))
            g = item.get("gain")
            if qid not in out or g not in VALID:
                continue
            docids = [idx_to_docid[n] for n in item.get("docs", []) if n in idx_to_docid]
            out[qid] = [(did, int(g)) for did in docids]
            nf = [str(x) for x in (item.get("new_facts") or [])][:8]
            if nf and len(self.summaries.get((tid, qid), [])) < self.max_summary:
                self.summaries.setdefault((tid, qid), []).extend(nf)
        return out

    def _call(self, prompt):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()
        self.calls += 1
        msgs = [{"role": "user", "content": prompt}]
        for attempt in range(4):
            try:
                try:
                    r = self._client.chat.completions.create(model=self.model, messages=msgs, temperature=0.0)
                except Exception as e:
                    if "temperature" not in str(e).lower():
                        raise
                    r = self._client.chat.completions.create(model=self.model, messages=msgs)
                raw = r.choices[0].message.content or ""
                a, b = raw.find("{"), raw.rfind("}")
                if a != -1 and b != -1:
                    return json.loads(raw[a:b + 1])
            except Exception:  # noqa: BLE001
                import time
                time.sleep(3 * (attempt + 1))
        return {"questions": []}

    def close(self):
        self.embedder.close()
