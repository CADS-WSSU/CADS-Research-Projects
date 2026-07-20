"""Pydantic schemas, metric weights, and the composite-quality function.

This module is the single source of truth for:

* The six quality-metric names and their composite weights (must sum to 1.0).
* The dataset **input** shape (:class:`ModelReport`, :class:`Question`) — note these
  carry the *already-generated* report plus its recorded generation cost / latency /
  tokens, which are the subject of the efficiency analysis.
* Every judge **output** (:class:`JudgeResult`, :class:`PairwiseVerdict`).
* Every **persisted** artifact (:class:`ModelEvaluation`, :class:`ModelAggregate`,
  :class:`EfficiencyMetrics`, :class:`LeaderboardRow`, :class:`Results`).
* The deterministic :func:`compute_quality_score` weighted average.
"""

from __future__ import annotations

import math
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Quality metric weights (from the spec)
# ---------------------------------------------------------------------------
#
#   quality_score = 0.30 * evidence_support
#                 + 0.20 * coverage
#                 + 0.15 * utility
#                 + 0.10 * uncertainty
#                 + 0.10 * corpus_awareness
#                 + 0.15 * cti_quality
#
# Defined once and consumed by judges, orchestrator and exporters alike.
METRIC_WEIGHTS: Dict[str, float] = {
    "evidence_support": 0.30,
    "coverage": 0.20,
    "utility": 0.15,
    "uncertainty": 0.10,
    "corpus_awareness": 0.10,
    "cti_quality": 0.15,
}

#: Ordered canonical metric names.
METRIC_NAMES: tuple[str, ...] = tuple(METRIC_WEIGHTS.keys())

# A convex combination on a 0-10 scale only makes sense if the weights sum to 1.
assert abs(sum(METRIC_WEIGHTS.values()) - 1.0) < 1e-9, (
    "METRIC_WEIGHTS must sum to 1.0, got " f"{sum(METRIC_WEIGHTS.values())}"
)


# ---------------------------------------------------------------------------
# Judge token usage / cost (the *judge's* own spend, not the model under test)
# ---------------------------------------------------------------------------
class Usage(BaseModel):
    """Token counts returned by a judge LLM call."""

    prompt_tokens: int = Field(0, ge=0)
    completion_tokens: int = Field(0, ge=0)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
        )


# ---------------------------------------------------------------------------
# Dataset inputs: one report per model, per question
# ---------------------------------------------------------------------------
class ModelReport(BaseModel):
    """A single MIGHTYTOASTER report produced by one candidate LLM.

    Matches the spec's input schema. The ``cost`` / ``latency_seconds`` /
    ``input_tokens`` / ``output_tokens`` fields describe the *generation* of this
    report (the thing being evaluated for efficiency), not the judging step.
    """

    model: str = Field(..., description="Identifier of the LLM that generated the report.")
    answer: str = Field(..., description="The full generated report text.")
    cost: float = Field(0.0, ge=0.0, description="USD cost to generate this report (0 for free/local models).")
    latency_seconds: float = Field(0.0, ge=0.0, description="Wall-clock generation time in seconds.")
    input_tokens: int = Field(0, ge=0, description="Prompt tokens consumed during generation.")
    output_tokens: int = Field(0, ge=0, description="Completion tokens produced during generation.")

    @property
    def total_tokens(self) -> int:
        """Total generation tokens (input + output)."""
        return self.input_tokens + self.output_tokens


class Question(BaseModel):
    """A research question with one report per candidate model."""

    question_id: str
    question: str
    category: str = Field("general", description="Optional category hint, e.g. 'actor_profile'.")
    reports: List[ModelReport] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Judge outputs
# ---------------------------------------------------------------------------
class JudgeResult(BaseModel):
    """One judge's verdict on one report."""

    metric: str
    score: float = Field(..., ge=0.0, le=10.0)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    rationale: str = ""

    @field_validator("score")
    @classmethod
    def _round_score(cls, v: float) -> float:
        return round(float(v), 2)


class QualityScores(BaseModel):
    """The six per-metric quality scores plus the composite for one report."""

    scores: Dict[str, float]
    quality_score: float = Field(..., ge=0.0, le=10.0)

    @model_validator(mode="after")
    def _check_keys(self) -> "QualityScores":
        missing = set(METRIC_NAMES) - set(self.scores)
        if missing:
            raise ValueError(f"scores missing metric(s): {sorted(missing)}")
        return self


class PairwiseVerdict(BaseModel):
    """Head-to-head verdict between two reports.

    ``winner`` uses the literals ``system_a`` / ``system_b`` / ``tie`` so the tally
    logic never parses free text; the caller maps these back to model names.
    """

    winner: Literal["system_a", "system_b", "tie"]
    confidence: Literal["low", "medium", "high"] = "medium"
    rationale: str = ""


class PairwiseRecord(BaseModel):
    """Round-robin standings for a single model."""

    model: str
    wins: int = 0
    losses: int = 0
    ties: int = 0

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.ties

    @property
    def win_rate(self) -> float:
        """Wins / games, ties counting as half a win (standard tournament scoring)."""
        if self.games == 0:
            return 0.0
        return round((self.wins + 0.5 * self.ties) / self.games, 4)


class PairwiseMatch(BaseModel):
    """One judged head-to-head comparison, persisted for position-bias analysis.

    ``model_a`` was shown to the judge in the A slot and ``model_b`` in the B slot;
    with order balancing each unordered pair appears twice (A/B and B/A), which is
    what makes position-consistency measurable downstream.
    """

    question_id: str = ""
    model_a: str
    model_b: str
    winner: Literal["system_a", "system_b", "tie"]
    confidence: Literal["low", "medium", "high"] = "medium"
    rationale: str = ""


# ---------------------------------------------------------------------------
# Efficiency metrics
# ---------------------------------------------------------------------------
class EfficiencyMetrics(BaseModel):
    """Quality-normalised efficiency ratios for one model.

    For free/local models (cost == 0) ``quality_per_dollar`` is ``+inf`` and
    ``is_free`` is set so exporters can flag it rather than printing a misleading
    number. ``inf`` is JSON-serialised as the string ``"Infinity"`` by the
    exporter layer.
    """

    quality_per_dollar: float = Field(..., description="quality_score / cost ('inf' if free).")
    quality_per_1k_tokens: float = Field(..., description="quality_score / (total_tokens / 1000).")
    quality_per_minute: float = Field(..., description="quality_score / (latency_seconds / 60).")
    is_free: bool = Field(False, description="True when cost == 0 (free/local model).")


# ---------------------------------------------------------------------------
# Per-report evaluation and per-model aggregate
# ---------------------------------------------------------------------------
class ModelEvaluation(BaseModel):
    """Full evaluation of one model's report for one question."""

    question_id: str
    model: str
    quality_score: float = Field(..., ge=0.0, le=10.0)
    scores: Dict[str, float]
    judge_results: List[JudgeResult] = Field(default_factory=list)
    # Generation metrics carried through from the input for convenience.
    cost: float = 0.0
    latency_seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class ModelAggregate(BaseModel):
    """Aggregate of one model across the whole question set.

    Per the design decision, both **mean** (per question) and **total** (summed)
    cost / latency / tokens are retained. Efficiency leaderboards use the means.
    """

    model: str
    n_questions: int = 0

    mean_quality: float = 0.0

    # Means (per question)
    mean_cost: float = 0.0
    mean_latency_seconds: float = 0.0
    mean_total_tokens: float = 0.0

    # Totals (summed across the set)
    total_cost: float = 0.0
    total_latency_seconds: float = 0.0
    total_tokens: int = 0

    efficiency: Optional[EfficiencyMetrics] = None
    win_rate: float = 0.0
    wins: int = 0
    losses: int = 0
    ties: int = 0


# ---------------------------------------------------------------------------
# Leaderboards and the top-level results bundle
# ---------------------------------------------------------------------------
class LeaderboardRow(BaseModel):
    """One ranked row of a leaderboard. ``value`` is the metric being ranked on."""

    model: str
    value: float
    note: str = ""


class Results(BaseModel):
    """The complete benchmark artifact serialised to ``results.json``."""

    dataset: str = ""
    judge_provider: str = ""
    n_questions: int = 0
    evaluations: List[ModelEvaluation] = Field(default_factory=list)
    aggregates: List[ModelAggregate] = Field(default_factory=list)
    pareto_frontier: List[str] = Field(default_factory=list)
    leaderboards: Dict[str, List[LeaderboardRow]] = Field(default_factory=dict)
    pairwise_matches: List[PairwiseMatch] = Field(default_factory=list)
    judge_cost_usd: float = 0.0
    judge_usage: Usage = Field(default_factory=Usage)


# ---------------------------------------------------------------------------
# Composite quality
# ---------------------------------------------------------------------------
def compute_quality_score(scores: Dict[str, float]) -> float:
    """Return the weighted composite quality score (0-10) from per-metric scores.

    Raises :class:`KeyError` if any canonical metric is missing.
    """
    missing = set(METRIC_NAMES) - set(scores)
    if missing:
        raise KeyError(f"Cannot compute quality_score, missing metrics: {sorted(missing)}")
    total = sum(scores[name] * weight for name, weight in METRIC_WEIGHTS.items())
    return round(total, 2)


def _safe_div(numerator: float, denominator: float) -> float:
    """Divide, returning ``+inf`` when the denominator is zero/negative.

    Used by the efficiency calculations so free/local models (cost 0) and any
    zero-latency edge cases do not raise.
    """
    if denominator <= 0:
        return math.inf
    return numerator / denominator
