# 30-topic evaluation

Results of scoring each system against the TREC-faithful gpt-graded gold benchmark over 30 RAGTIME
topics (1,093 days; 297,296 document decision-points, 32,790 question decision-points). Metrics are
the truncated/primed ranking metrics (`RR′ / RBP′ / NDCG′ / AP′`) with a terminal-doc sentinel;
`nil_silence` is the fraction of no-change days handled correctly. Reported under three views:
`overall` (all days), `has_answer` (change days only), and `nil_silence`.

**No RAGTIME document text is included here** — the `*_rankings.json` files contain only document
*ids* and scores keyed by `topic⟟qid⟟day`.

| File | Contents |
|---|---|
| `g30_local.json` | Local (LLM-free) system — aggregate metrics. |
| `g30_local_per_topic.json` | Same, broken out per topic. |
| `g30_local_rankings.json` | Local system output (doc-id rankings per question-day). |
| `g30_local_rescored.json` | Local system re-scored at an alternate truncation/policy setting. |
| `g30_llm.json` / `g30_llm_pertopic.json` | LLM-rescue system (Haiku, whole-document, admit≥5). |
| `g30_llm_rankings.json` | LLM-rescue system output rankings. |
| `g30_refs.json` | Reference retrieval baselines: BM25 and bi-encoder. |
| `g30_refs_per_topic.json` / `g30_refs_rescored.json` | Per-topic / alternate-setting reference scores. |
| `g30_splade.json` / `g30_splade_per_topic.json` | Reference SPLADE baseline. |

See the folder [README](../../README.md) for the headline results table and how to reproduce.
