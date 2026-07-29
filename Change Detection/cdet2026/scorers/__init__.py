"""Scorer registry — resolve concrete scorers from config so the loop stays agnostic."""
from .base import Candidate, NoveltyScorer, RelevanceScorer
from .hybrid_relevance import HybridRelevanceScorer
from .local_novelty import LocalNoveltyScorer
from .reranker_relevance import RerankerRelevanceScorer


def build_relevance_scorer(cfg: dict) -> RelevanceScorer:
    """Resolve the relevance scorer from config. Default is the cross-encoder reranker
    (cosine cannot gate silence); "hybrid" keeps the older bi-encoder+BM25 scorer;
    "llm" judges topical relevance on the top-K cosine candidates (improvement #1 —
    attacks reranker recall; leak-free Claude via the LAS gateway)."""
    method = cfg["relevance"].get("method", "reranker")
    if method == "hybrid":
        return HybridRelevanceScorer(cfg)
    if method == "llm":
        from .llm_relevance import LLMRelevanceScorer
        return LLMRelevanceScorer(cfg)
    return RerankerRelevanceScorer(cfg)


def build_novelty_scorer(cfg: dict) -> NoveltyScorer:
    """Default novelty scorer is the local blend. M7 can swap an LLM judge here."""
    return LocalNoveltyScorer(cfg)


__all__ = [
    "Candidate",
    "RelevanceScorer",
    "NoveltyScorer",
    "HybridRelevanceScorer",
    "RerankerRelevanceScorer",
    "LocalNoveltyScorer",
    "build_relevance_scorer",
    "build_novelty_scorer",
]
