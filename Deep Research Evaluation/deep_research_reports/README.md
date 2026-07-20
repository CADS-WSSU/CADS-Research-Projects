# Deep-research reports (evaluation corpus)

The **16 CTI deep-research reports** scored in the accompanying study: **4 threat
actors × 4 report-generating models**, all produced through the same MIGHTYTOASTER
research engine so the generating model is the only variable.

| | gpt-5.4-mini *(proprietary)* | grok-4.5 *(proprietary)* | nemotron-super-3-120b *(open)* | gpt-oss-120b *(open)* |
|---|---|---|---|---|
| **MuddyWater** | ✓ | ✓ | ✓ | ✓ |
| **Forest Blizzard** (APT28) | ✓ | ✓ | ✓ | ✓ |
| **Storm-1849** (ArcaneDoor) | ✓ | ✓ | ✓ | ✓ |
| **Ababil of Minab** | ✓ | ✓ | ✓ | ✓ |

Each report answers the same fixed hunt-ready dossier prompt for its actor:

> Produce a full hunt-ready dossier on actor "&lt;ACTOR&gt;". I need everything we know:
> identity & aliases, attribution, observed TTPs mapped to MITRE ATT&CK, IOCs classified
> as block / hunt / forensics-only, infrastructure patterns, timeline, hunting queries
> (Sigma/KQL/Splunk where applicable), mitigations, pivot points, and intelligence gaps.

## Files

- **`<actor>__<model>.md`** — the 16 full reports as generated (with their source lists),
  human-readable.
- **`dataset.json`** — the exact evaluator input used for the study: the same 16 reports with
  model-identifying metadata stripped so the judges score them **blind** (`question_id`,
  `question`, and `reports[].model` / `reports[].answer`). This is the file to feed the tool.

## Reproduce the scores

```bash
cd ../mt_eval_kit
pip install -r requirements.txt
# offline smoke test (no key):
python3 evaluate.py --dataset ../deep_research_reports/dataset.json --provider deterministic --out reports/eval
# with a real judge (see ../README.md and mt_eval_kit/INTEGRATION.md):
export OPENAI_API_KEY=...   # + OPENAI_BASE_URL=... for an on-prem gateway
python3 evaluate.py --dataset ../deep_research_reports/dataset.json --provider openai --out reports/eval
```

## Notes

- The `.md` files carry each report's full text and citations; `dataset.json` is the
  metadata-stripped form actually scored (so re-running on `dataset.json` reproduces the
  paper's blind evaluation).
- These are **LLM-generated** dossiers on publicly reported threat actors, provided as a
  research/evaluation corpus. They have not been fact-verified; scoring is reference-free and
  measures plausibility and tradecraft, not confirmed accuracy. Do not treat any single report
  as authoritative intelligence.
