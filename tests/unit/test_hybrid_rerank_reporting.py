"""Tests for portable hybrid calibration report helpers."""

from __future__ import annotations

from incident_precedent_harness.retrieval.hybrid_reporting import (
    FourWayRetrievalComparison,
    _interpret_mrr,
    _interpret_safety,
)


def test_hybrid_interpretation_ties_are_explicitly_non_promotional() -> None:
    comparison = FourWayRetrievalComparison(
        keyword_correct_precedent_mrr=1.0,
        dense_correct_precedent_mrr=0.9,
        dense_reranked_correct_precedent_mrr=0.9,
        hybrid_reranked_correct_precedent_mrr=0.9,
        hybrid_mrr_delta_vs_keyword=-0.1,
        hybrid_mrr_delta_vs_dense=0.0,
        hybrid_mrr_delta_vs_dense_rerank=0.0,
        keyword_false_operational_match_rate=0.2,
        dense_false_operational_match_rate=0.1,
        dense_reranked_false_operational_match_rate=0.1,
        hybrid_reranked_false_operational_match_rate=0.1,
        hybrid_false_operational_match_rate_delta_vs_keyword=-0.1,
        hybrid_false_operational_match_rate_delta_vs_dense=0.0,
        hybrid_false_operational_match_rate_delta_vs_dense_rerank=0.0,
    )

    assert "tied dense-plus-rerank" in _interpret_mrr(comparison)
    assert "tied dense-plus-rerank" in _interpret_safety(comparison)
