"""Bounded SIE score reranking over a dense top-k candidate set.

This module is provider-neutral. It does not import the SIE SDK, select an
operational representative, assign decision states, or authorize procedures.
It can only reorder already-retrieved dense candidates using the typed semantic
inference boundary.
"""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from incident_precedent_harness.domain.incident_data import HistoricalIncidentCard
from incident_precedent_harness.inference.models import (
    CandidateScoringRequest,
    InferenceProfile,
    TextItem,
)
from incident_precedent_harness.inference.protocol import SemanticInferenceClient
from incident_precedent_harness.retrieval.models import DenseCandidate, RerankedCandidate
from incident_precedent_harness.retrieval.representation import incident_retrieval_representation


class DenseRerankError(ValueError):
    """Raised when bounded reranking would violate the typed retrieval contract."""


class DenseTopKReranker:
    """Rerank only an existing dense candidate set using typed SIE score results."""

    def __init__(self, *, incidents: tuple[HistoricalIncidentCard, ...]) -> None:
        incident_by_id = {incident.incident_id: incident for incident in incidents}
        if len(incident_by_id) != len(incidents):
            raise DenseRerankError("approved incidents must have unique incident IDs")
        self._representation_by_id = {
            incident.incident_id: incident_retrieval_representation(incident)
            for incident in incidents
        }

    def rerank(
        self,
        *,
        query_text: str,
        dense_candidates: tuple[DenseCandidate, ...],
        client: SemanticInferenceClient,
        score_profile: InferenceProfile,
        trace_id: UUID,
    ) -> tuple[tuple[RerankedCandidate, ...], float]:
        """Return the same candidate identities in provider score-rank order.

        The model receives only the controlled representation of the already
        retrieved candidates. It cannot expand the candidate pool. Provider raw
        relevance values are retained as finite audit evidence; provider rank is
        the ordering contract.
        """

        self._validate_dense_candidates(dense_candidates)
        candidate_ids = tuple(candidate.incident_id for candidate in dense_candidates)
        request = CandidateScoringRequest(
            trace_id=trace_id,
            profile=score_profile,
            query=TextItem(item_id="calibration-query", text=query_text),
            candidates=tuple(
                TextItem(
                    item_id=incident_id,
                    text=self._representation_by_id[incident_id],
                )
                for incident_id in candidate_ids
            ),
        )
        response = client.score_incident_candidates(request)
        self._validate_response(
            requested_candidate_ids=candidate_ids,
            response_profile_id=response.profile_id,
            score_profile=score_profile,
            response_scores=response.scores,
        )

        dense_by_id = {candidate.incident_id: candidate for candidate in dense_candidates}
        reranked = tuple(
            RerankedCandidate(
                incident_id=score.candidate_id,
                dense_rank=dense_by_id[score.candidate_id].rank,
                rerank_rank=score.rank,
                cosine_similarity=dense_by_id[score.candidate_id].cosine_similarity,
                raw_relevance_score=score.score,
            )
            for score in response.scores
        )
        return reranked, response.latency_ms

    def _validate_dense_candidates(
        self,
        candidates: tuple[DenseCandidate, ...],
    ) -> None:
        if not candidates:
            raise DenseRerankError("dense reranking requires at least one candidate")
        if len(candidates) > 10:
            raise DenseRerankError("dense reranking may score at most ten candidates")
        candidate_ids = tuple(candidate.incident_id for candidate in candidates)
        if len(candidate_ids) != len(set(candidate_ids)):
            raise DenseRerankError("dense reranking candidates must have unique incident IDs")
        if tuple(candidate.rank for candidate in candidates) != tuple(
            range(1, len(candidates) + 1)
        ):
            raise DenseRerankError("dense reranking candidates must have contiguous dense ranks")
        unknown = set(candidate_ids).difference(self._representation_by_id)
        if unknown:
            raise DenseRerankError("dense reranking candidates must belong to the approved corpus")

    @staticmethod
    def _validate_response(
        *,
        requested_candidate_ids: tuple[str, ...],
        response_profile_id: str,
        score_profile: InferenceProfile,
        response_scores: Iterable[object],
    ) -> None:
        scores = tuple(response_scores)
        if response_profile_id != score_profile.profile_id:
            raise DenseRerankError("rerank response profile did not match the requested score profile")
        response_ids = tuple(getattr(score, "candidate_id", None) for score in scores)
        if len(response_ids) != len(requested_candidate_ids) or set(response_ids) != set(
            requested_candidate_ids
        ):
            raise DenseRerankError("rerank response candidate identities did not match dense top-k")
        ranks = tuple(getattr(score, "rank", None) for score in scores)
        if tuple(sorted(ranks)) != tuple(range(1, len(requested_candidate_ids) + 1)):
            raise DenseRerankError("rerank response ranks must cover dense top-k exactly once")
