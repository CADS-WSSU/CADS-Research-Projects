# cdet_eval — standalone scorer for TREC Change Detection

Scores a change-detection system's output with the **truncated ranking metrics** from
Liu, Moffat, Baldwin & Zhang, *"Quit While Ahead: Evaluating Truncated Rankings"* (SIGIR
2016) — the official TREC 2026 Change Detection scoring. It evaluates **both** official
levels:

- **Document ranking** — per `(topic, question, day)`: how well the reported documents for
  a question are ranked, on graded gains `0/1/5/10`.
- **Question ranking** — per `(topic, day)`: how well the *questions that changed* are
  ranked. A question's gain on a day is the **maximum gain of its relevant documents that
  day** (0 if none); the system's question order is taken from the `question_rank` field.

**Zero dependencies.** Pure Python 3 standard library (`evaluate.py` + `truncated.py`).
No install, no packages. Copy the two files anywhere and run.

```bash
python evaluate.py --run YOUR_RUN.jsonl --qrels QRELS.jsonl [--universe UNIVERSE.jsonl]
```

---

## Why these metrics (and why silence matters)

Each metric appends a nominal **terminal document** to the system's ranking. Its gain is
`1.0` when the unit has **no** relevant items, and otherwise the fraction of the total
available gain accrued so far. Two consequences define the task:

- **Silence is rewarded.** On a no-change unit (no relevant doc/question that day), the
  *correct* answer is an **empty** ranking, which scores a perfect `1.0`. Returning
  anything is strictly worse.
- **Padding is penalized.** Trailing non-relevant items push the terminal reward down the
  ranking, lowering the score. Stop after the last good item; never pad to a fixed length.

The four metrics emphasize different things (all higher-is-better):

| Metric | Emphasis |
|---|---|
| `RR'`   | reciprocal rank of the first relevant hit (in `[0,1]`) |
| `RBP'`  | top-heavy rank-biased gain rate, persistence `p=0.5` |
| `NDCG'` | graded, position-discounted, ideal-normalized (in `[0,1]`) |
| `AP'`   | average precision over the ranking, ideal-normalized (in `[0,1]`) |

> **Note on `RBP'`.** It is a raw *gain rate*. With graded gains (up to 10) the
> question-level `RBP'` can **exceed 1** — it is comparable across systems, not a `[0,1]`
> fraction. Use `--binary` if you want an `RBP'` bounded to `[0,1]`.

## Reported views

For each level the scorer prints three views:

- **overall** — averaged over **all** units, *including no-change days*. This is the
  decisive, silence-aware number.
- **has-answer** — averaged over only the days that genuinely have a relevant item
  (recall-oriented; ignores silence).
- **nil-silence** — fraction of no-change units on which the system correctly stayed
  silent. `1.0` = perfect restraint, `0.0` = fires on every empty day.

> Question-level nil-silence is measured at **topic-day** granularity: a topic-day counts
> as correctly silent only if *every* question in that topic stays silent, so one firing
> question breaks it.

---

## Input formats

### Run (`--run`)
Either the **cdet submission format** (one metadata line, then one object per topic):

```json
{"runtag":"my-run","run_type":"automatic","description":"...","models":["..."],"extern":"..."}
{"topic":"1001","results":{"2023-05-02":{"results":[
   {"qid":"q_1","question_rank":0,"doc_ranking":[{"doc_id":"docA","score":0.9},{"doc_id":"docB","score":0.7}]},
   {"qid":"q_2","question_rank":1,"doc_ranking":[{"doc_id":"docX","score":0.5}]}
]}}}
```

…or a **simple per-line format** (one line per fired question-day):

```json
{"topic":"1001","qid":"q_1","day":"2023-05-02","doc_ranking":["docA","docB"],"question_rank":0}
```

`question_rank` (ascending = more confident) drives the question-ranking evaluation. A
question a system does **not** report on a day is treated as silent for that question. Doc
`score` values are ignored — only the order matters.

### Qrels (`--qrels`)
One relevant document per line:

```json
{"topic":"1001","qid":"q_1","day":"2023-05-02","doc_id":"docA","gain":10}
```

Accepted aliases: `tid`/`topic_id`; `date`; `question_id`; `rel_grade`/`relevance`/`rel`
for `gain`. Use `--gain-map "1:1,2:5,3:10"` to remap grades, or `--binary` to treat any
relevant doc as gain 1.

### Universe (`--universe`, optional but recommended)
JSONL of every `(topic, qid, day)` the system was asked to decide:

```json
{"topic":"1001","qid":"q_1","day":"2023-05-02"}
```

Supplying it credits **correct silence on no-change days**. Without it, scope is only the
units that appear in the qrels or the run, so silence is under-counted.

---

## Worked example: dev2

The `example/` directory ships a complete, runnable example on the **2 official dev2
topics** (24 questions): the binary organizer qrels (`dev2_qrels.jsonl`), a real run of
the LLM-free **local** system in cdet format (`dev2_run.jsonl`), and the decision universe
(`dev2_universe.jsonl`). From this directory:

```bash
python evaluate.py --run example/dev2_run.jsonl \
                   --qrels example/dev2_qrels.jsonl \
                   --universe example/dev2_universe.jsonl
```

Expected output:

```
=== DOCUMENT ranking ===
  units: 2493  (345 has-answer, 2148 nil)
  nil-silence (correct silence on no-change units): 0.826
  metric        overall   has-answer
  RR_prime       0.8319       0.3785
  RBP_prime      0.8262       0.3617
  NDCG_prime     0.8550       0.3928
  AP_prime       0.8313       0.3736

=== QUESTION ranking ===
  units: 203  (123 has-answer, 80 nil)
  nil-silence (correct silence on no-change units): 0.362
  metric        overall   has-answer
  RR_prime       0.5326       0.4805
  RBP_prime      0.4301       0.3331
  NDCG_prime     0.5397       0.4289
  AP_prime       0.4214       0.2970
```

(These match the project's internal harness exactly, cross-validating the scorer.) The
tiny `example/run.jsonl` + `example/qrels.jsonl` are a 2-day toy showing the minimal format.

`example/make_dev2_example.py` regenerates the dev2 files from the full pipeline. **You do
not need it to use the scorer** — it depends on the whole system; scoring your own run
needs only `evaluate.py` + `truncated.py`.

---

## Using it on your own project

1. Emit your system's output as a run file (cdet or simple format above).
2. Emit a `universe.jsonl` listing every `(topic, qid, day)` you decided (so your silence
   is scored). This is just your evaluation loop's full set of question-days.
3. Score:
   ```bash
   python evaluate.py --run my_run.jsonl --qrels qrels.jsonl --universe universe.jsonl \
                      [--level both|doc|question] [--gain-map "1:1,2:5,3:10"] [--binary] \
                      [--out report.json]
   ```

`--out` writes the full JSON report (both levels, all metrics, all views) for tables.

## Files

| File | Purpose |
|---|---|
| `evaluate.py`   | CLI scorer (document + question levels). Standard library only. |
| `truncated.py`  | The four truncated metrics (`RR'`, `RBP'`, `NDCG'`, `AP'`). |
| `test_metrics.py` | Reproduces the paper's Table 1 to 3 decimals — run `python test_metrics.py`. |
| `example/`      | dev2 worked example + a minimal toy, and the dev2 generator. |

## Reference

Fei Liu, Alistair Moffat, Timothy Baldwin, Xiuzhen Zhang. *Quit While Ahead: Evaluating
Truncated Rankings.* SIGIR 2016.
