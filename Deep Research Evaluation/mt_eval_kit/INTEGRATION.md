# mt-eval-kit — standalone CTI report evaluator

Pointwise (**6 quality factors + composite**) and pairwise (**head-to-head win-rate**)
evaluation of CTI deep-research reports from **any** set of LLMs — any number of models,
any names. You bring the reports; this scores them. No generation, no cost/efficiency.

This folder is self-contained: copy it anywhere and run.

---

## 1. Install

```bash
cd mt_eval_kit
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt              # core: pydantic, pyyaml, tenacity
pip install openai                            # + the judge SDK you'll use (or anthropic / google-generativeai / httpx)
```

Python 3.10+. The offline `deterministic` judge needs no SDK and no key — use it first to
confirm the pipeline runs before wiring a real judge.

(Optional: `pip install -e .` to get the `mt-evaluate` and `mt-adapt` shell commands.)

---

## 2. Put your reports in the input format

A JSON **list of actors**; each actor has the research prompt and one entry per model:

```json
[
  {
    "question_id": "arcanedoor_storm1849",
    "question": "Produce a full hunt-ready dossier on actor \"Storm-1849\" ...",
    "reports": [
      { "model": "gemma3:12b",  "answer": "<full report text>" },
      { "model": "qwen2.5:14b", "answer": "<full report text>" },
      { "model": "llama3.1:8b", "answer": "<full report text>" }
    ]
  }
]
```

- **`question_id`** — short unique slug per actor (row label in the output).
- **`question`** — the exact prompt the models answered (judges read it for relevance).
- **`reports[].model`** — any label; lineup and count are arbitrary.
- **`reports[].answer`** — full report text (markdown fine). Other fields are ignored.

Same `question_id` across models → they're compared head-to-head. One model per actor is fine
(pointwise still runs; pairwise is skipped for that actor).

See `datasets/example_reports.json` for a minimal working example.

> Have raw MIGHTYTOASTER `.md`/`.json` exports? Convert them:
> `python3 mightytoaster_adapter.py export1.json export2.json --out my_reports.json`

---

## 3. Pick a judge

Set the judge model in `config.yaml` under the matching provider, then pass `--provider`.

| Provider | Use for | Auth |
|---|---|---|
| `deterministic` | offline smoke test (no LLM) | none |
| `openai` | OpenAI API **or any OpenAI-compatible gateway** (LiteLLM, vLLM, Ollama `/v1`) | `OPENAI_API_KEY` (+ `OPENAI_BASE_URL` for a gateway) |
| `anthropic` | Claude | `ANTHROPIC_API_KEY` |
| `gemini` | Gemini | `GOOGLE_API_KEY` |
| `ollama` | local Ollama (native API) | none (`base_url` in config) |

To keep evaluation on-prem, point `--provider openai` at your internal gateway (`OPENAI_BASE_URL`)
and set `providers.openai.model` to the served model id.

---

## 4. Run

```bash
# offline smoke test (no keys)
python3 evaluate.py --dataset datasets/example_reports.json --provider deterministic --out reports/eval

# real judge
export OPENAI_API_KEY=...          # and OPENAI_BASE_URL=... for a gateway
python3 evaluate.py --dataset my_reports.json --provider openai --out reports/eval

# pointwise only (skip the head-to-head tournament)
python3 evaluate.py --dataset my_reports.json --provider openai --no-pairwise --out reports/eval
```

Flags: `--no-pairwise`, `--no-cache`, `--max-concurrency N`, `--config path`.

---

## 5. What you get

Console: a per-actor table — the **6 factors + composite**, one column per model:

```
Actor: arcanedoor_storm1849
Metric                      gemma3:12b   qwen2.5:14b   llama3.1:8b
------------------------------------------------------------------
  evidence_support               7.33          8.40          6.10
  coverage                      10.00         10.00          9.20
  utility                        9.33          8.67          7.80
  uncertainty                    6.67          7.33          4.50
  corpus_awareness               4.00          6.00          3.10
  cti_quality                   10.00         10.00          9.40
  composite                      7.96          8.43          6.78
```

Files in `--out/`:
- **`factor_breakdown.csv`** — one row per actor×model; columns = 6 factors + composite (Excel-ready).
- **`factor_breakdown.md`** — per-actor tables + a mean-across-actors table.
- **`pairwise_standings.csv`** — win/loss/tie + win-rate per model (omitted with `--no-pairwise`).
- **`results.json`** — full detail: every per-factor score with strengths/weaknesses/rationale, and all pairwise verdicts.

### The 6 quality factors (weights → composite)

| Factor | Weight | Asks |
|---|---|---|
| evidence_support | 0.30 | claims backed by cited evidence / sound reasoning? |
| coverage | 0.20 | answers the whole question (TTPs, IOCs, timeline…)? |
| utility | 0.15 | actionable — hunt, block, investigate? |
| cti_quality | 0.15 | tradecraft: ATT&CK, IOC handling, estimative language |
| uncertainty | 0.10 | honest confidence + explicit intelligence gaps? |
| corpus_awareness | 0.10 | grounded in the reporting, not invented? |

`composite = Σ weightᵢ × factorᵢ` (0–10). Scoring is **reference-free** (no gold answer), so it
measures plausibility/tradecraft, not verified factual correctness. Pairwise win-rate =
`(wins + ½·ties)/games`; every pair is judged in **both orders** to cancel position bias.

To change weights or judge wording: `models/schemas.py` (`METRIC_WEIGHTS`) and `prompts/*.md`.

---

## 6. Notes

- **Judge choice matters.** Judges agree on *ranking* more than on absolute *scores* — compare
  models within one judge run; treat composites as ordinal.
- **Reproducibility.** `deterministic` is fully repeatable; LLM judges vary run-to-run. Responses
  cache to `.eval_cache/` (keyed by provider+model+prompt); `--no-cache` forces fresh calls.
- **Tests:** `pip install pytest pytest-asyncio && python3 -m pytest -q`.

## What's in the box
`evaluate.py` (entry point) · `orchestrator.py` (QualityEvaluator + PairwiseRunner) ·
`judges/` (6 metric judges + pairwise) · `prompts/` (editable rubric templates) ·
`llm/` (judge clients: deterministic/openai/anthropic/gemini/ollama/vllm + cache/cost) ·
`models/schemas.py` · `exporters/` · `mightytoaster_adapter.py` (optional input converter) ·
`config.yaml` · `datasets/example_reports.json` · `tests/`.
