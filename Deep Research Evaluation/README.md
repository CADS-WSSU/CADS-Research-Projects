# Deep Research Evaluation

A **reference-free evaluation framework for long-form cyber threat intelligence (CTI)
deep-research reports**. You bring the reports (from any set of LLMs); the tool scores them
two complementary ways:

- **Pointwise** — six quality factors (0–10) combined into a weighted **composite**.
- **Pairwise** — an order-balanced head-to-head **tournament** (win-rate).

Both are administered by a configurable panel of judges (offline heuristic, or any
OpenAI-compatible / Anthropic / Gemini / local Ollama·vLLM model). No gold answers required,
which is what makes it usable on live threat actors that have no single "correct" dossier.

It was built for the MIGHTYTOASTER deep-research workflow but is **model- and
source-agnostic**: any number of models, any names, any report text.

---

## Why this exists

Cybersecurity LLM benchmarks are almost all short-form (multiple-choice, classification,
extraction). General long-form / deep-research evaluators are not adapted to CTI. To our
knowledge nothing evaluates the open-ended, multi-section **hunt-ready dossier** a CTI
deep-research workflow produces — so we built a framework that does, and can compare
self-hosted open-source models against proprietary baselines on report quality.

---

## Contents

- **`mt_eval_kit/`** — the self-contained evaluator (copy it anywhere and run).
- **`examples/`** — a minimal input plus the exact output the offline judge produces from it.
- **`deep_research_reports/`** — the **16-report study corpus** (4 actors × 4 models) with a
  ready-to-run `dataset.json`, so you can reproduce the scores. See its README.
- **`LICENSE`** — MIT.

## Quick start (offline, no API key)

```bash
cd "Deep Research Evaluation/mt_eval_kit"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # pydantic, pyyaml, tenacity

# offline deterministic judge — confirms the pipeline runs with no LLM and no key
python3 evaluate.py --dataset datasets/example_reports.json --provider deterministic --out reports/eval
```

Then wire a real judge:

```bash
pip install openai                       # or: anthropic / google-generativeai / httpx
export OPENAI_API_KEY=...                 # + OPENAI_BASE_URL=... to point at an on-prem gateway
python3 evaluate.py --dataset my_reports.json --provider openai --out reports/eval
```

To keep evaluation **on-premise**, point `--provider openai` at your internal
OpenAI-compatible gateway (LiteLLM / vLLM / Ollama `/v1`) via `OPENAI_BASE_URL` and set the
served model id in `mt_eval_kit/config.yaml`.

---

## Input format

A JSON list of actors; each has the prompt and one entry per model. Same `question_id`
across models means they are compared head-to-head.

```json
[
  {
    "question_id": "arcanedoor_storm1849",
    "question": "Produce a full hunt-ready dossier on actor \"Storm-1849\" ...",
    "reports": [
      { "model": "gemma3:12b",  "answer": "<full report text>" },
      { "model": "qwen2.5:14b", "answer": "<full report text>" }
    ]
  }
]
```

See [`examples/example_reports.json`](examples/example_reports.json) for a minimal working
input, and [`examples/`](examples/) for the exact console/CSV/Markdown output the offline
judge produces from it.

---

## What you get

- `factor_breakdown.csv` / `.md` — per-actor **6 factors + composite**, one column per model.
- `pairwise_standings.csv` — win/loss/tie and win-rate per model.
- `results.json` — full detail: every factor score with strengths/weaknesses/rationale, and
  all pairwise verdicts.

### The six factors (weights → composite)

| Factor | Weight | Asks |
|---|---|---|
| evidence_support | 0.30 | claims backed by cited evidence / sound reasoning? |
| coverage | 0.20 | answers the whole question (TTPs, IOCs, timeline…)? |
| utility | 0.15 | actionable — hunt, block, investigate? |
| cti_quality | 0.15 | tradecraft: ATT&CK, IOC handling, estimative language |
| uncertainty | 0.10 | honest confidence + explicit intelligence gaps? |
| corpus_awareness | 0.10 | grounded in the reporting, not invented? |

`composite = Σ weightᵢ × factorᵢ` (0–10). Pairwise win-rate = `(wins + ½·ties)/games`; every
pair is judged in **both** presentation orders to cancel position bias. Weights and rubric
wording are editable (`mt_eval_kit/models/schemas.py` and `mt_eval_kit/prompts/*.md`).

---

## How to adopt it for your own project

1. Copy the `mt_eval_kit/` folder anywhere (it is self-contained).
2. Put your reports in the input format above (or convert raw exports with
   `mt_eval_kit/mightytoaster_adapter.py`).
3. Start with `--provider deterministic` to validate the pipeline, then switch to a real judge.
4. Adjust factors/weights/prompts to your domain if needed — the CTI rubric is not hard-coded
   into the engine, only into the prompt templates and the weight table.

Full details, judge options, and flags are in
[`mt_eval_kit/INTEGRATION.md`](mt_eval_kit/INTEGRATION.md).

---

## Caveats (read before trusting a number)

- Scoring is **reference-free**: it measures plausibility and tradecraft, not verified factual
  correctness — a confident hallucination can still score well.
- Judges agree on **ranking** more than on absolute **scores**; compare models within one judge
  run and treat composites as ordinal.
- Longer, more comprehensive reports tend to win pairwise; watch for a length/verbosity effect.

---

## Requirements

Python 3.10+. Core deps: `pydantic`, `pyyaml`, `tenacity` (in `mt_eval_kit/requirements.txt`).
A judge SDK (`openai` / `anthropic` / `google-generativeai` / `httpx`) only if you use that
judge; the `deterministic` judge needs none. Tests: `pip install pytest pytest-asyncio &&
python3 -m pytest -q` inside `mt_eval_kit/`.
