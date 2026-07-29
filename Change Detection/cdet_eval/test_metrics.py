#!/usr/bin/env python3
"""Correctness gate: reproduce Table 1 of Liu et al. (SIGIR 2016) to three decimals,
plus graded-gain bounding checks. Pure stdlib — run directly:

    python test_metrics.py
"""
from truncated import ap_prime, ndcg_prime, rbp_prime, rr_prime, score_ranking

# (ranking, R, RR', RBP', NDCG', AP')  -- verbatim from the paper's Table 1, p=0.5
TABLE_1 = [
    ("00", 0, 0.333, 0.250, 0.500, 0.333),
    ("000", 0, 0.250, 0.125, 0.431, 0.250),
    ("111", 3, 1.000, 1.000, 1.000, 1.000),
    ("11", 3, 1.000, 0.917, 0.922, 0.648),
    ("11100", 3, 1.000, 0.906, 0.971, 0.917),
    ("101", 3, 1.000, 0.708, 0.698, 0.528),
    ("1", 3, 1.000, 0.667, 0.742, 0.306),
    ("10100", 3, 1.000, 0.646, 0.678, 0.491),
    ("011", 3, 0.500, 0.458, 0.554, 0.403),
    ("01001", 3, 0.500, 0.302, 0.490, 0.299),
]


def main():
    fails = 0
    for ranking, R, rr, rbp, ndcg, ap in TABLE_1:
        g = [float(c) for c in ranking]
        rg = [1.0] * R
        for name, got, want in [
            ("RR'", round(rr_prime(g, rg), 3), rr),
            ("RBP'", round(rbp_prime(g, rg, 0.5), 3), rbp),
            ("NDCG'", round(ndcg_prime(g, rg), 3), ndcg),
            ("AP'", round(ap_prime(g, rg), 3), ap),
        ]:
            if got != want:
                print(f"FAIL {name} ranking={ranking!r}: got {got} want {want}")
                fails += 1

    # graded gains stay in [0,1]; perfect ranking = 1.0; vital-first beats vital-last
    REL = [10.0, 5.0, 1.0]
    for name in ("RR_prime", "NDCG_prime", "AP_prime"):
        if not (abs(score_ranking([10.0, 5.0, 1.0], REL)[name] - 1.0) < 1e-9):
            print(f"FAIL perfect graded {name}"); fails += 1
        if not (0.0 <= score_ranking([1.0, 5.0, 10.0], REL)[name] <= 1.0 + 1e-9):
            print(f"FAIL graded bound {name}"); fails += 1
    if not (score_ranking([10.0, 5.0, 1.0], REL)["AP_prime"]
            > score_ranking([1.0, 5.0, 10.0], REL)["AP_prime"]):
        print("FAIL vital-first should beat vital-last (AP')"); fails += 1

    # nil query: empty ranking scores 1.0
    for name in ("RR_prime", "NDCG_prime", "AP_prime"):
        if round(score_ranking([], [])[name], 6) != 1.0:
            print(f"FAIL nil empty {name}"); fails += 1

    if fails == 0:
        print("OK: all Table-1 rows + graded + nil checks pass.")
    else:
        print(f"\n{fails} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
