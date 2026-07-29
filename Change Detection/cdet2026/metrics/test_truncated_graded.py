"""Graded-gain behavior for the TREC Change Detection scale (0/1/5/10):
RR'/NDCG'/AP' must stay in [0,1], a perfect ranking must score 1.0, and putting the
higher-gain (more vital) doc first must score >= putting it last.
"""
from .truncated import ap_prime, ndcg_prime, rr_prime, score_ranking

REL = [10.0, 5.0, 1.0]   # one vital, one important, one on-topic doc (R = 16)


def test_perfect_graded_ranking_scores_one():
    g = [10.0, 5.0, 1.0]                      # all relevant docs, best-first
    assert round(rr_prime(g, REL), 6) == 1.0
    assert round(ndcg_prime(g, REL), 6) == 1.0
    assert round(ap_prime(g, REL), 6) == 1.0


def test_graded_metrics_bounded_0_1():
    for g in ([10.0], [1.0, 5.0, 10.0], [0.0, 10.0, 0.0, 5.0], [10.0, 5.0, 1.0]):
        for name in ("RR_prime", "NDCG_prime", "AP_prime"):
            v = score_ranking(g, REL)[name]
            assert 0.0 <= v <= 1.0 + 1e-9, f"{name} out of [0,1]: {v} for {g}"


def test_single_vital_doc_was_unbounded_before_fix():
    # Regression: AP' used to return ~9.6 here (raw (R+1) denominator with graded gains).
    assert ap_prime([10.0], [10.0]) == 1.0          # one vital doc, full recall -> perfect
    assert 0.0 <= ap_prime([10.0], REL) <= 1.0      # one vital doc, partial recall -> bounded


def test_gain_order_matters():
    # vital-first should beat vital-last on the top-weighted graded metrics
    best_first = score_ranking([10.0, 5.0, 1.0], REL)
    worst_first = score_ranking([1.0, 5.0, 10.0], REL)
    assert best_first["NDCG_prime"] > worst_first["NDCG_prime"]
    assert best_first["AP_prime"] > worst_first["AP_prime"]


def test_nil_query_empty_ranking_scores_one():
    for name in ("RR_prime", "NDCG_prime", "AP_prime"):
        assert round(score_ranking([], [])[name], 6) == 1.0
