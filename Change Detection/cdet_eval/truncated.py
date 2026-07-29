"""Truncated-ranking metrics from Liu, Moffat, Baldwin & Zhang, "Quit While Ahead:
Evaluating Truncated Rankings", SIGIR 2016 — the TREC Change Detection scoring metrics.

A nominal *terminal document* is appended at rank d+1 (d = length of the system
ranking) with gain (Eq. 1):
        r_t = 1                              if R == 0
        r_t = (sum of retrieved gains) / R   if R > 0
where R is the total gain pool for the query (sum of all relevant docs' gains).

Gain mechanism (TREC Change Detection): document gains are GRADED (e.g. the track's
0 / 1 / 5 / 10 = not relevant / on-topic / important / vital). The terminal document's
gain is the "gain recall" — the fraction of the query's total gain accrued so far.
Pass the assessor's gains directly; for a binary qrel use gain 1 for every relevant doc.

Bounding under graded gains:
  - RR'   : uses only whether gain > 0 -> in [0,1].
  - NDCG' : DCG / ideal-DCG -> in [0,1], gain-aware (standard graded normalization).
  - AP'   : normalized by the IDEAL AP-numerator (not the binary (R+1) shortcut), so it
            stays in [0,1] for graded gains AND reproduces Eq. 4 / Table 1 for binary.
  - RBP'  : the paper's raw rank-biased GAIN RATE. For binary it is in [0,1]; with graded
            gains > 1 it is "expected gain per document" and CAN exceed 1 (by design).

Inputs to every metric:
    gains      : per-rank gains of the system's ranking, in rank order (0 = non-relevant)
    rel_gains  : the multiset of gains of ALL relevant docs for the query (the gain pool).
                 For binary relevance with R relevant docs this is [1]*R.
                 R = sum(rel_gains); the number of relevant docs is len(rel_gains).

Reproduces the paper's (binary) Table 1 to three decimals (see test_metrics.py).
"""
from __future__ import annotations

import math


def _log2(x: float) -> float:
    return math.log2(x)


def terminal_gain(gains: list[float], R: float) -> float:
    """Eq. 1: gain of the appended terminal document."""
    if R <= 0:
        return 1.0
    return sum(gains) / R


def _extended(gains: list[float], R: float) -> list[float]:
    """Ranking with the terminal document appended at rank d+1."""
    return list(gains) + [terminal_gain(gains, R)]


def rr_prime(gains: list[float], rel_gains: list[float]) -> float:
    """RR': reciprocal of the first rank with positive gain in the extended ranking.

    On a nil query (R=0) the terminal gain is 1, so an empty/non-relevant ranking of
    length d scores 1/(d+1) (an empty ranking scores 1.0). On a has-answer query that
    retrieved nothing relevant, the terminal gain is 0 and RR'=0.
    """
    R = sum(rel_gains)
    for i, g in enumerate(_extended(gains, R), start=1):
        if g > 0:
            return 1.0 / i
    return 0.0


def rbp_prime(gains: list[float], rel_gains: list[float], p: float = 0.5) -> float:
    """RBP' (Eq. 2): (1-p) Σ_{i=1..d} r_i p^{i-1} + r_t p^d."""
    R = sum(rel_gains)
    d = len(gains)
    body = sum((1.0 - p) * g * (p ** (i)) for i, g in enumerate(gains))  # i 0-based -> p^{i}
    rt = terminal_gain(gains, R)
    return body + rt * (p ** d)


def _ideal_extended(rel_gains: list[float], length: int) -> list[float]:
    """Ideal (d+1)-element gain vector for NDCG'/AP' normalization."""
    G = sorted(rel_gains, reverse=True)
    n_rel = len(G)
    ideal = [0.0] * length
    for k in range(length):          # k is 0-based rank index (rank = k+1)
        if k < n_rel:
            ideal[k] = G[k]
        elif k == n_rel:             # first zero-gain position -> terminal gain 1.0
            ideal[k] = 1.0
    return ideal


def ndcg_prime(gains: list[float], rel_gains: list[float]) -> float:
    """NDCG' (Eq. 3): DCG@(d+1) of [r_1..r_d, r_t] / DCG of the ideal (d+1)-ranking."""
    R = sum(rel_gains)
    ext = _extended(gains, R)
    length = len(ext)  # d+1
    dcg = sum(g / _log2(2 + k) for k, g in enumerate(ext))
    ideal = _ideal_extended(rel_gains, length)
    idcg = sum(g / _log2(2 + k) for k, g in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def _ap_numerator(seq: list[float]) -> float:
    """Σ_i  r_i * (Σ_{j<=i} r_j) / i  over a gain sequence (the AP' numerator, Eq. 4)."""
    cum = 0.0
    total = 0.0
    for i, g in enumerate(seq, start=1):
        cum += g
        if g > 0:
            total += g * (cum / i)
    return total


def ap_prime(gains: list[float], rel_gains: list[float]) -> float:
    """AP' (Eq. 4), normalized by the IDEAL ranking so it is graded-correct and bounded
    to [0,1]. For binary relevance the ideal numerator equals (R+1), reproducing Eq. 4
    (and Table 1) exactly. For graded gains the (R+1) shortcut is wrong, so we divide by
    the ideal numerator instead."""
    R = sum(rel_gains)
    ext = _extended(gains, R)
    ideal_seq = sorted(rel_gains, reverse=True) + [1.0]
    denom = _ap_numerator(ideal_seq)
    return _ap_numerator(ext) / denom if denom > 0 else 0.0


def score_ranking(gains: list[float], rel_gains: list[float], p: float = 0.5) -> dict[str, float]:
    """All four truncated metrics for one ranking."""
    return {
        "RR_prime": rr_prime(gains, rel_gains),
        "RBP_prime": rbp_prime(gains, rel_gains, p=p),
        "NDCG_prime": ndcg_prime(gains, rel_gains),
        "AP_prime": ap_prime(gains, rel_gains),
    }
