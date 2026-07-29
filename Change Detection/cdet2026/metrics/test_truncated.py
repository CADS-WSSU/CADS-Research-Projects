"""Gate: reproduce Table 1 of Liu et al. (SIGIR 2016) to three decimals.
Each row is (ranking string, R, RR', RBP', NDCG', AP'), p=0.5.

Run:  python -m pytest cdet2026/metrics/test_truncated.py -q
"""
import pytest

from .truncated import ap_prime, ndcg_prime, rbp_prime, rr_prime

# (ranking, R, RR', RBP', NDCG', AP')  -- verbatim from the paper's Table 1
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


def _gains(ranking: str) -> list[float]:
    return [float(c) for c in ranking]


def _rel_gains(R: int) -> list[float]:
    return [1.0] * R  # binary relevance: R relevant docs each with gain 1


@pytest.mark.parametrize("ranking,R,rr,rbp,ndcg,ap", TABLE_1)
def test_table_1(ranking, R, rr, rbp, ndcg, ap):
    g = _gains(ranking)
    rg = _rel_gains(R)
    assert round(rr_prime(g, rg), 3) == rr, f"RR' {ranking}"
    assert round(rbp_prime(g, rg, p=0.5), 3) == rbp, f"RBP' {ranking}"
    assert round(ndcg_prime(g, rg), 3) == ndcg, f"NDCG' {ranking}"
    assert round(ap_prime(g, rg), 3) == ap, f"AP' {ranking}"
