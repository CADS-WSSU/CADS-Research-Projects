#!/usr/bin/env python3
"""Standalone scorer for TREC Change Detection runs (truncated ranking metrics).

Scores a system's output at BOTH official evaluation levels, using RR' / RBP' / NDCG' /
AP' with the terminal document (Liu et al., SIGIR 2016):

  * DOCUMENT ranking   — per (topic, question, day): how well the reported documents for
                         a question are ranked (graded gains 0/1/5/10).
  * QUESTION ranking   — per (topic, day): how well the questions that changed are ranked.
                         A question's gain on a day is the MAX gain of its relevant docs
                         that day (0 if none); the system's question order comes from the
                         `question_rank` field of the run.

Pure Python 3 standard library — no dependencies, no install:

    python evaluate.py --run RUN.jsonl --qrels QRELS.jsonl [--universe UNIVERSE.jsonl] [options]

INPUT FORMATS (see README.md for detail):
  RUN    cdet submission JSONL: a metadata line, then one object per topic
         {"topic", "results": {day: {"results": [ {"qid","question_rank",
                                                    "doc_ranking":[{"doc_id","score"}...]} ]}}}
         (a simple per-line format {"topic","qid","day","doc_ranking",["question_rank"]} also works)
  QRELS  JSONL, one relevant doc per line:
         {"topic","qid","day":"YYYY-MM-DD","doc_id","gain":<number>}
         (aliases: tid/topic_id; date; question_id; rel_grade/relevance for gain)
  UNIVERSE (optional but recommended) JSONL of {"topic","qid","day"} listing EVERY
         (topic, question, day) the system was asked to decide. Supplying it credits
         correct silence on nil days (days with no relevant doc) at both levels; without
         it, scope = the units appearing in the qrels or the run.

Terminal-document semantics: an empty ranking on a unit with no relevant items scores 1.0
(correct silence); padding non-relevant items lowers the score.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict

from truncated import score_ranking

METRICS = ["RR_prime", "RBP_prime", "NDCG_prime", "AP_prime"]


# ----------------------------- input parsing --------------------------------------
def _first(d: dict, *keys, default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def load_qrels(path: str, gain_map: dict[int, float] | None, binary: bool):
    """-> {(topic, qid, day): {doc_id: gain}}."""
    qrel: dict[tuple, dict] = defaultdict(dict)
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        topic = str(_first(r, "topic", "tid", "topic_id"))
        qid = str(_first(r, "qid", "question_id", default=""))
        day = str(_first(r, "day", "date"))
        doc = str(_first(r, "doc_id", "docid", "id"))
        grade = _first(r, "gain", "rel_grade", "relevance", "rel", default=1)
        try:
            grade = float(grade)
        except (TypeError, ValueError):
            grade = 1.0
        if binary:
            gain = 1.0 if grade > 0 else 0.0
        elif gain_map is not None:
            gain = float(gain_map.get(int(grade), grade))
        else:
            gain = grade
        if gain > 0:
            qrel[(topic, qid, day)][doc] = gain
    return qrel


def _norm_ranking(ranking):
    """Accept [doc_id, ...] or [{"doc_id","score"}, ...] -> [doc_id, ...] in order."""
    out = []
    for h in ranking:
        if isinstance(h, str):
            out.append(h)
        elif isinstance(h, dict):
            out.append(str(_first(h, "doc_id", "docid", "id")))
    return out


def load_run(path: str):
    """Parse a run once into both views:
      docs      -> {(topic, qid, day): [doc_id, ...]}           (document ranking)
      questions -> {(topic, day): [qid, ...] by question_rank}  (question ranking)
    Handles the cdet submission format and the simple per-line format."""
    docs: dict[tuple, list] = {}
    q_fired: dict[tuple, list] = defaultdict(list)   # (topic, day) -> [(rank, qid)]
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if not isinstance(obj, dict) or "runtag" in obj or "run_type" in obj:
            continue  # metadata line
        # simple per-line format
        if "qid" in obj and ("doc_ranking" in obj or "doc_ids" in obj) and "results" not in obj:
            topic = str(_first(obj, "topic", "tid", "topic_id"))
            day = str(_first(obj, "day", "date"))
            qid = str(obj["qid"])
            docs[(topic, qid, day)] = _norm_ranking(_first(obj, "doc_ranking", "doc_ids", default=[]))
            rank = _first(obj, "question_rank", "q_rank", default=len(q_fired[(topic, day)]))
            q_fired[(topic, day)].append((float(rank), qid))
            continue
        # cdet submission format
        if "topic" in obj and "results" in obj and isinstance(obj["results"], dict):
            topic = str(obj["topic"])
            for day, dayres in obj["results"].items():
                qlist = dayres.get("results", dayres) if isinstance(dayres, dict) else dayres
                for i, q in enumerate(qlist or []):
                    qid = str(_first(q, "qid", "question_id"))
                    docs[(topic, qid, str(day))] = _norm_ranking(q.get("doc_ranking", []))
                    rank = _first(q, "question_rank", "q_rank", default=i)
                    q_fired[(topic, str(day))].append((float(rank), qid))
    questions = {td: [qid for _r, qid in sorted(pairs)] for td, pairs in q_fired.items()}
    return docs, questions


def load_universe(path: str):
    """-> set of (topic, qid, day)."""
    u = set()
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        u.add((str(_first(o, "topic", "tid", "topic_id")),
               str(_first(o, "qid", "question_id", default="")),
               str(_first(o, "day", "date"))))
    return u


def parse_gain_map(spec: str | None) -> dict[int, float] | None:
    if not spec:
        return None
    m = {}
    for part in spec.split(","):
        k, v = part.split(":")
        m[int(k)] = float(v)
    return m


# ----------------------------- scoring: documents ---------------------------------
def evaluate_docs(docs, qrel, universe=None, p=0.5):
    """Per (topic, qid, day) document-ranking scores."""
    keys = set(universe) if universe else (set(qrel) | set(docs))
    per_key = {}
    for key in keys:
        gain_of = qrel.get(key, {})
        ranking = docs.get(key, [])
        gains = [gain_of.get(doc, 0.0) for doc in ranking]
        rel_gains = list(gain_of.values())
        per_key[key] = {"n_rel": len(rel_gains), "fired": bool(ranking),
                        **score_ranking(gains, rel_gains, p=p)}
    return per_key


# ----------------------------- scoring: questions ---------------------------------
def evaluate_questions(questions, qrel, universe=None, p=0.5):
    """Per (topic, day) question-ranking scores. A question's gain on a day = the max gain
    of its relevant documents that day; the pool is all positive question-gains that day."""
    qgain_td: dict[tuple, dict] = defaultdict(dict)   # (topic, day) -> {qid: gain}
    for (topic, qid, day), docmap in qrel.items():
        if docmap:
            qgain_td[(topic, day)][qid] = max(docmap.values())
    if universe:
        td_scope = {(t, d) for (t, _q, d) in universe}
    else:
        td_scope = {(t, d) for (t, _q, d) in qrel} | set(questions)
    per_td = {}
    for td in td_scope:
        pool = [g for g in qgain_td.get(td, {}).values() if g > 0]
        ranking = questions.get(td, [])
        gains = [qgain_td.get(td, {}).get(qid, 0.0) for qid in ranking]
        per_td[td] = {"n_rel": len(pool), "fired": bool(ranking),
                      **score_ranking(gains, pool, p=p)}
    return per_td


# ----------------------------- scoring: new questions -----------------------------
def evaluate_newq(docs, qrel, heldout):
    """New-question DISCOVERY, document-grounded (no embeddings needed). A held-out question
    is 'discovered' on a day if ANY question the run reports that day surfaces at least one of
    the held-out question's relevant documents. Reports question-level recall (covered on >=1 of
    its gold days) and day-level recall, plus the best doc-ranking AP' achieved on covered units."""
    held = {(str(h.get("topic", h.get("tid"))), str(h.get("qid"))) for h in heldout}
    hold_gold = {k: v for k, v in qrel.items() if (k[0], k[1]) in held}   # (t,q,d)->{doc:gain}
    reported_by_td = defaultdict(set)                                      # (topic,day)->reported doc ids
    for (t, _q, d), ids in docs.items():
        reported_by_td[(t, d)].update(ids)
    covered_q, total_days, covered_days, aps = set(), 0, 0, []
    for (t, q, d), gm in hold_gold.items():
        total_days += 1
        rep = reported_by_td.get((t, d), set())
        if rep & set(gm):
            covered_days += 1; covered_q.add((t, q))
        # doc-ranking quality if the system reported this question's docs directly
        if (t, q, d) in docs:
            gains = [gm.get(x, 0.0) for x in docs[(t, q, d)]]
            aps.append(score_ranking(gains, list(gm.values()))["AP_prime"])
    n_held = len(held)
    return {"n_heldout": n_held, "n_gold_days": total_days,
            "question_recall": (len(covered_q) / n_held) if n_held else float("nan"),
            "day_recall": (covered_days / total_days) if total_days else float("nan"),
            "covered_questions": len(covered_q),
            "mean_doc_ap": (sum(aps) / len(aps)) if aps else float("nan")}


# ----------------------------- aggregate ------------------------------------------
def _mean(rows, m):
    return sum(r[m] for r in rows) / len(rows) if rows else float("nan")


def aggregate(per_unit, unit_name):
    allk = list(per_unit.values())
    has = [r for r in allk if r["n_rel"] > 0]
    nil = [r for r in allk if r["n_rel"] == 0]
    silent_on_nil = [r for r in nil if not r["fired"]]
    return {
        "unit": unit_name,
        "n_units": len(allk),
        "n_has_answer": len(has),
        "n_nil": len(nil),
        "nil_silence": (len(silent_on_nil) / len(nil)) if nil else None,
        "overall": {m: _mean(allk, m) for m in METRICS},
        "has_answer": {m: _mean(has, m) for m in METRICS},
    }


def _print_block(rep):
    print(f"\n=== {rep['unit'].upper()} ranking ===")
    print(f"  units: {rep['n_units']}  ({rep['n_has_answer']} has-answer, {rep['n_nil']} nil)")
    if rep["nil_silence"] is not None:
        print(f"  nil-silence (correct silence on no-change units): {rep['nil_silence']:.3f}")
    print(f"  {'metric':11}{'overall':>10}{'has-answer':>13}")
    for m in METRICS:
        print(f"  {m:11}{rep['overall'][m]:>10.4f}{rep['has_answer'][m]:>13.4f}")


# ----------------------------- CLI ------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Score a Change Detection run (document + question levels).")
    ap.add_argument("--run", required=True, help="system run file (cdet JSONL or simple JSONL)")
    ap.add_argument("--qrels", required=True, help="ground-truth qrels JSONL")
    ap.add_argument("--universe", default=None,
                    help="JSONL of {topic,qid,day} for every decided unit (credits correct silence)")
    ap.add_argument("--level", choices=["doc", "question", "both"], default="both")
    ap.add_argument("--heldout", default=None,
                    help="held-out questions JSONL {topic,qid,question}; adds a new-question "
                         "DISCOVERY report (document-grounded)")
    ap.add_argument("--gain-map", default=None, help='map grades to gains, e.g. "1:1,2:5,3:10"')
    ap.add_argument("--binary", action="store_true", help="treat any relevant doc as gain 1")
    ap.add_argument("--rbp-p", type=float, default=0.5, help="RBP persistence p (default 0.5)")
    ap.add_argument("--out", default=None, help="write the full JSON report to this path")
    args = ap.parse_args()

    qrel = load_qrels(args.qrels, parse_gain_map(args.gain_map), args.binary)
    docs, questions = load_run(args.run)
    universe = load_universe(args.universe) if args.universe else None

    report = {}
    if args.level in ("doc", "both"):
        report["document"] = aggregate(evaluate_docs(docs, qrel, universe, args.rbp_p), "document")
    if args.level in ("question", "both"):
        report["question"] = aggregate(evaluate_questions(questions, qrel, universe, args.rbp_p), "question")

    if args.heldout:
        heldout = [json.loads(l) for l in open(args.heldout, encoding="utf-8") if l.strip()]
        report["new_question"] = evaluate_newq(docs, qrel, heldout)

    for key in ("document", "question"):
        if key in report:
            _print_block(report[key])
    if "new_question" in report:
        nq = report["new_question"]
        print(f"\n=== NEW-QUESTION discovery (document-grounded) ===")
        print(f"  held-out questions: {nq['n_heldout']}  ({nq['n_gold_days']} gold question-days)")
        print(f"  question recall (discovered on >=1 gold day): {nq['covered_questions']}/{nq['n_heldout']} = {nq['question_recall']:.3f}")
        print(f"  day recall (gold days whose docs were surfaced): {nq['day_recall']:.3f}")
        if nq['mean_doc_ap'] == nq['mean_doc_ap']:
            print(f"  mean doc AP' where the question was reported directly: {nq['mean_doc_ap']:.3f}")
    print("\noverall = all units incl. no-change days (silence-aware; the decisive view);")
    print("has-answer = quality on days that genuinely have a relevant doc (recall-oriented).")
    if any(report[k]["overall"]["RBP_prime"] > 1.0 for k in report):
        print("note: RBP' is a raw gain-rate; with graded gains it can exceed 1 (use --binary for [0,1]).")
    if not universe:
        print("note: no --universe given, so silence is only scored on nil units present in the "
              "qrels/run. Pass --universe to credit silence on every decided (topic,question,day).")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nfull report -> {args.out}")


if __name__ == "__main__":
    sys.exit(main())
