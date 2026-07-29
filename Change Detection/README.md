# Change Detection (TREC 2026)

Silence-aware **streaming change detection** on the TREC 2026 RAGTIME corpus. The collection is
streamed one day at a time; for each topic's questions the system reports the **new + relevant**
documents (and ranks the **changed questions**) — or **stays silent**. On a realistic multi-year
news stream ~98% of question-days carry no change, so *knowing when to say nothing* is the core of
the task and is scored explicitly.

Two systems are provided:

- **Local (LLM-free)** — a fully local pipeline (no paid API, no generative LLM anywhere):
  bge-small cosine prefilter → bge-reranker-v2-m3 cross-encoder relevance gate + rank-aware
  ensemble → memory-based novelty (embedding + lexical + named-entity) → metric-aware silence policy
  with per-question z-score ranking.
- **LLM rescue** — an optional second pass (Claude Haiku 4.5, whole-document, `admit ≥ τ`) that
  trades a little overall score for higher has-answer recall. It is **leak-free**: the rescue model
  is disjoint from the LLM used to build the evaluation gold.

```
day stream ──> per question:
  1. RELEVANCE GATE   bge-small cosine top-k  →  bge-reranker-v2-m3 cross-encoder  →  ensemble gate
  2. NOVELTY          0.5·(1−cos to memory) + 0.25·new terms + 0.25·new entities (spaCy NER)
  3. POLICY           fire only if relevant AND novel; order by gain; truncate; else SILENT
  4. OUTPUT           cdet submission JSON  →  scored by RR'/RBP'/NDCG'/AP' (terminal-doc truncated)
```

Everything tunable lives in [`config.toml`](config.toml) — no thresholds or model names are
hard-coded.

## Layout

| Path | What |
|---|---|
| `cdet2026/` | The streaming pipeline: day loop, scorers (relevance / novelty / hybrid / LLM), policy, memory, metrics. |
| `cdet_eval/` | Standalone evaluator (`evaluate.py`) implementing the truncated primed metrics + a worked example. |
| `config.toml` | All tunable knobs (models, thresholds, policy, truncation). |
| `requirements.txt`, `setup_gpu.sh` | Environment setup (Python 3.11+; cu121 torch on GPU, MPS on Mac). |
| `evaluation/30topic/` | **30-topic evaluation results** — metrics + per-topic breakdowns + system output rankings. See its README. |

## 30-topic evaluation (headline)

Evaluated against a TREC-faithful, gpt-graded gold benchmark over **30 RAGTIME topics / 1,093 days**
(297,296 document decision-points, 32,790 question decision-points). Metrics are truncated/primed
`AP′` (terminal-doc sentinel); `nil-silence` is the fraction of no-change days scored correctly.

**Documents**

| System | overall AP′ | has-answer AP′ | nil-silence |
|---|--:|--:|--:|
| **Local (LLM-free)** | **0.973** | 0.439 | 0.966 |
| **+ LLM rescue** (admit≥5) | 0.957 | **0.577** | 0.931 |
| ref: BM25 | 0.098 | 0.523 | 0.00 |
| ref: bi-encoder | 0.099 | 0.557 | 0.00 |
| ref: SPLADE | 0.099 | 0.565 | 0.00 |

**Questions** (primary metric — independently graded)

| System | overall AP′ | has-answer AP′ | nil-silence |
|---|--:|--:|--:|
| **Local (LLM-free)** | **0.881** | 0.394 | 0.817 |
| **+ LLM rescue** (admit≥5) | 0.794 | **0.544** | 0.670 |
| ref: BM25 | 0.117 | 0.463 | 0.00 |
| ref: bi-encoder | 0.120 | 0.587 | 0.00 |
| ref: SPLADE | 0.119 | 0.555 | 0.00 |

**Reading it:** the retrieval baselines score near-zero *overall* because they never stay silent —
on a ~98%-silent stream, firing every day is catastrophic. Silence-awareness is what separates the
two systems from off-the-shelf retrieval. The LLM rescue is a tunable frontier: at `admit≥5` it
lifts has-answer AP′ by +0.14 (doc) / +0.15 (question) at a modest overall cost; at `admit≥10` the
gain is near-free (see `*_rescored.json`).

## Reproduce

```bash
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
pip install --ignore-requires-python "git+https://github.com/trec-changedet/cdet-api"
# run the day-stream pipeline (see config.toml for corpus/model paths), then score:
python -m cdet_eval.evaluate --help
```

## Data & licensing

The underlying **RAGTIME corpus document text is registration-gated and not redistributed here**.
This folder ships **code + evaluation results only** (metrics and system-output rankings, which
contain document *ids* and scores but no document text). Obtain the corpus through the official
TREC/NIST RAGTIME channel to rebuild the graded pool and re-run evaluation. The derived gold
benchmark (labels-by-reference) is available separately, pending confirmation of redistribution
terms with the RAGTIME organizers.
