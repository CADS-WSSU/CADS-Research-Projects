# Ablations & negative results (30-topic full universe)

Metric reports only (AP′/RR′/RBP′/NDCG′ + nil-silence; no corpus text). See the folder
[README](../../README.md) for the narrative.

## Novelty reshapings (measured against the final Local system)
| File | Variant | Result |
|---|---|---|
| `novelty_base.json` | novelty as gate/cap (baseline) | doc has-ans 0.4388, q has-ans 0.3938 |
| `novelty_A_signal.json` | **A**: additive ranking signal (never demotes) | +0.0025 doc has-ans; **adopted default** |
| `novelty_B_zcalib.json` | **B**: per-question z-calibrated criterion | 0.000 on every metric (rejected) |
| `novelty_A_plus_B.json` | A + B | = A (B adds nothing) |
| `nzrank_A_only.json` | A, pure-relevance z-rank (comparison base) | q has-ans 0.3938 |
| `nzrank_A_nz_blend0{3,5,7}.json` | novelty-aware z-rank, blend α=0.3/0.5/0.7 | −0.011 / −0.002 / −0.001 q has-ans |
| `nzrank_A_nz_product.json` | novelty-aware z-rank, relevance×novelty | −0.001 q has-ans |

**Takeaway:** doc-level novelty does not help in any of four forms; it conflates *same-entities* with
*same-information*. Claim/fact-level novelty is left to future work.

## Query expansion
| File | Variant | Result |
|---|---|---|
| `query_expansion_oracle.json` | reranker query = question + **gold** acceptable-answers (leaky ceiling) | has-ans recall does **not** improve (doc 0.441→0.418); silence erodes (q nil 0.817→0.732) |

**Takeaway:** the reranker is not recall-limited by query underspecification; even the oracle ceiling
fails and hurts silence. Every shippable (non-leaky) expansion is ruled out a fortiori.
