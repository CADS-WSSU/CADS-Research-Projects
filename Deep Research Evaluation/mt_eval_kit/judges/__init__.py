"""Quality judges.

The six single-metric judges score one quality dimension each;
:class:`PairwiseJudge` performs head-to-head comparisons. :data:`JUDGE_CLASSES`
is the canonical ordered list the orchestrator instantiates.
"""

from .base_judge import BaseJudge
from .corpus_awareness_judge import CorpusAwarenessJudge
from .coverage_judge import CoverageJudge
from .cti_quality_judge import CTIQualityJudge
from .evidence_judge import EvidenceJudge
from .pairwise_judge import PairwiseJudge
from .uncertainty_judge import UncertaintyJudge
from .utility_judge import UtilityJudge

#: The six judge classes, in spec order.
JUDGE_CLASSES: tuple[type[BaseJudge], ...] = (
    EvidenceJudge,
    CoverageJudge,
    UtilityJudge,
    UncertaintyJudge,
    CorpusAwarenessJudge,
    CTIQualityJudge,
)

__all__ = [
    "BaseJudge",
    "EvidenceJudge",
    "CoverageJudge",
    "UtilityJudge",
    "UncertaintyJudge",
    "CorpusAwarenessJudge",
    "CTIQualityJudge",
    "PairwiseJudge",
    "JUDGE_CLASSES",
]
