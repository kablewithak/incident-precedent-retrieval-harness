"""Tests for the bounded dense top-k SIE score reranking contract."""

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
from incident_precedent_harness.retrieval.models import DenseCandidate
from incident_precedent_harness.retrieval.rerank import DenseRerankError, DenseTopKReranker

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
    def __init__(self, scores: tuple[CandidateScore, ...], profile_id: str = "fake-score-v1") -> None:
        self._scores = scores
        self._profile_id = profile_id

    def score_incident_candidates(self, request) -> CandidateScoringResponse:  # type: ignore[no-untyped-def]
        return CandidateScoringResponse(
            trace_id=request.trace_id,
            profile_id=self._profile_id,
            scores=self._scores,
            latency_ms=7,
        )


def _dense_candidates() -> tuple[DenseCandidate, ...]:
    return (
        DenseCandidate(incident_id="INC-001", rank=1, cosine_similarity=0.80),
        DenseCandidate(incident_id="INC-002", rank=2, cosine_similarity=0.70),
    )


def test_reranker_reorders_only_dense_top_k_and_preserves_dense_trace() -> None:
    reranker = DenseTopKReranker(incidents=JsonDatasetRepository(ROOT).load_incidents())
    client = _ScriptedScoreClient(
        scores=(
            CandidateScore(candidate_id="INC-002", rank=1, score=2.5),
            CandidateScore(candidate_id="INC-001", rank=2, score=-0.3),
        )
    )

    reranked, latency_ms = reranker.rerank(
        query_text="queue backlog after worker deployment",
        dense_candidates=_dense_candidates(),
        client=client,  # type: ignore[arg-type]
        score_profile=_score_profile(),
        trace_id=uuid4(),
    )

    assert latency_ms == 7
    assert [candidate.incident_id for candidate in reranked] == ["INC-002", "INC-001"]
    assert [candidate.dense_rank for candidate in reranked] == [2, 1]
    assert [candidate.rerank_rank for candidate in reranked] == [1, 2]
    assert [candidate.raw_relevance_score for candidate in reranked] == [2.5, -0.3]


def test_reranker_rejects_score_response_that_changes_candidate_identity_set() -> None:
    reranker = DenseTopKReranker(incidents=JsonDatasetRepository(ROOT).load_incidents())
    client = _ScriptedScoreClient(
        scores=(
            CandidateScore(candidate_id="INC-001", rank=1, score=0.3),
            CandidateScore(candidate_id="INC-003", rank=2, score=0.2),
        )
    )

    with pytest.raises(DenseRerankError, match="identities"):
        reranker.rerank(
            query_text="queue backlog after worker deployment",
            dense_candidates=_dense_candidates(),
            client=client,  # type: ignore[arg-type]
            score_profile=_score_profile(),
            trace_id=uuid4(),
        )


def test_reranker_rejects_more_than_ten_dense_candidates() -> None:
    reranker = DenseTopKReranker(incidents=JsonDatasetRepository(ROOT).load_incidents())
    candidates = tuple(
        DenseCandidate(
            incident_id=f"INC-{index:03d}",
            rank=index,
            cosine_similarity=0.1,
        )
        for index in range(1, 12)
    )

    with pytest.raises(DenseRerankError, match="at most ten"):
        reranker.rerank(
            query_text="synthetic query",
            dense_candidates=candidates,
            client=_ScriptedScoreClient(scores=()),  # type: ignore[arg-type]
            score_profile=_score_profile(),
            trace_id=uuid4(),
        )
