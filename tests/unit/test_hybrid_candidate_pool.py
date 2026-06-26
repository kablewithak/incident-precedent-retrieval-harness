"""Tests for the bounded keyword-plus-dense candidate pool and rerank contract."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from incident_precedent_harness.domain.enums import ProviderOperation
from incident_precedent_harness.inference.models import (
    CandidateScore,
    CandidateScoringResponse,
    InferenceProfile,
)
from incident_precedent_harness.retrieval import JsonDatasetRepository
from incident_precedent_harness.retrieval.hybrid import (
    HybridCandidatePoolBuilder,
    HybridCandidatePoolError,
    HybridTopKReranker,
)
from incident_precedent_harness.retrieval.models import DenseCandidate, KeywordCandidate

ROOT = Path(__file__).resolve().parents[2]


def _score_profile() -> InferenceProfile:
    return InferenceProfile(
        profile_id="fake-score-v1",
        provider_name="fake",
        operation=ProviderOperation.SCORE,
        model_id="deterministic-test-double",
        timeout_ms=100,
        max_retries=0,
    )


class _ScriptedScoreClient:
    def __init__(self, scores: tuple[CandidateScore, ...]) -> None:
        self._scores = scores

    def score_incident_candidates(self, request) -> CandidateScoringResponse:  # type: ignore[no-untyped-def]
        return CandidateScoringResponse(
            trace_id=request.trace_id,
            profile_id="fake-score-v1",
            scores=self._scores,
            latency_ms=7,
        )


def test_hybrid_pool_deduplicates_and_retains_keyword_and_dense_provenance() -> None:
    pool = HybridCandidatePoolBuilder(maximum_candidates=10).build(
        keyword_candidates=(
            KeywordCandidate(incident_id="INC-001", rank=1, score=3.0),
            KeywordCandidate(incident_id="INC-002", rank=2, score=2.0),
        ),
        dense_candidates=(
            DenseCandidate(incident_id="INC-002", rank=1, cosine_similarity=0.8),
            DenseCandidate(incident_id="INC-003", rank=2, cosine_similarity=0.7),
        ),
    )

    assert [candidate.incident_id for candidate in pool] == ["INC-001", "INC-002", "INC-003"]
    assert [candidate.hybrid_seed_rank for candidate in pool] == [1, 2, 3]
    assert pool[1].keyword_rank == 2
    assert pool[1].dense_rank == 1
    assert pool[2].keyword_rank is None
    assert pool[2].dense_rank == 2


def test_hybrid_pool_rejects_non_contiguous_source_ranks() -> None:
    with pytest.raises(HybridCandidatePoolError, match="contiguous"):
        HybridCandidatePoolBuilder().build(
            keyword_candidates=(
                KeywordCandidate(incident_id="INC-001", rank=2, score=3.0),
            ),
            dense_candidates=(),
        )


def test_hybrid_reranker_reorders_only_deduplicated_seed_union() -> None:
    hybrid_candidates = HybridCandidatePoolBuilder().build(
        keyword_candidates=(
            KeywordCandidate(incident_id="INC-001", rank=1, score=3.0),
            KeywordCandidate(incident_id="INC-002", rank=2, score=2.0),
        ),
        dense_candidates=(
            DenseCandidate(incident_id="INC-002", rank=1, cosine_similarity=0.8),
            DenseCandidate(incident_id="INC-003", rank=2, cosine_similarity=0.7),
        ),
    )
    reranker = HybridTopKReranker(incidents=JsonDatasetRepository(ROOT).load_incidents())
    reranked, latency_ms = reranker.rerank(
        query_text="queue backlog after worker deployment",
        hybrid_candidates=hybrid_candidates,
        client=_ScriptedScoreClient(
            (
                CandidateScore(candidate_id="INC-003", rank=1, score=2.4),
                CandidateScore(candidate_id="INC-002", rank=2, score=0.1),
                CandidateScore(candidate_id="INC-001", rank=3, score=-0.2),
            )
        ),  # type: ignore[arg-type]
        score_profile=_score_profile(),
        trace_id=uuid4(),
    )

    assert latency_ms == 7
    assert [candidate.incident_id for candidate in reranked] == ["INC-003", "INC-002", "INC-001"]
    assert [candidate.hybrid_seed_rank for candidate in reranked] == [3, 2, 1]
    assert reranked[1].keyword_rank == 2
    assert reranked[1].dense_rank == 1
