"""Bounded hybrid candidate pooling and SIE score reranking.

This module combines deterministic lexical and local dense candidate sets only
for calibration. It does not assign decision states, select an authoritative
precedent, authorize procedures, or inspect held-out fixtures.

The candidate union is deterministic:
1. keyword candidates in lexical rank order;
2. dense candidates in cosine-rank order that are not already present.

SIE score can reorder only that union. It cannot inject an unseen incident.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from incident_precedent_harness.domain.incident_data import HistoricalIncidentCard
from incident_precedent_harness.inference.models import (
    CandidateScoringRequest,
    InferenceProfile,
    TextItem,
)
from incident_precedent_harness.inference.protocol import SemanticInferenceClient
from incident_precedent_harness.retrieval.models import DenseCandidate, KeywordCandidate
from incident_precedent_harness.retrieval.representation import incident_retrieval_representation

PositiveInteger = Annotated[int, Field(ge=1)]


class HybridCandidatePoolError(ValueError):
    """Raised when a bounded hybrid candidate set would be ambiguous or unsafe."""


class HybridCandidate(BaseModel):
    """One deduplicated candidate with lexical and/or dense provenance."""

    incident_id: str = Field(min_length=1)
    hybrid_seed_rank: PositiveInteger
    keyword_rank: PositiveInteger | None = None
    keyword_score: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    dense_rank: PositiveInteger | None = None
    cosine_similarity: float | None = Field(
        default=None,
        ge=-1.000001,
        le=1.000001,
        allow_inf_nan=False,
    )

    @model_validator(mode="after")
    def require_source_provenance(self) -> "HybridCandidate":
        keyword_present = self.keyword_rank is not None
        dense_present = self.dense_rank is not None
        if not keyword_present and not dense_present:
            raise ValueError("hybrid candidates must have keyword or dense provenance")
        if (self.keyword_rank is None) != (self.keyword_score is None):
            raise ValueError("keyword rank and score must be present together")
        if (self.dense_rank is None) != (self.cosine_similarity is None):
            raise ValueError("dense rank and cosine similarity must be present together")
        return self


class HybridRerankedCandidate(BaseModel):
    """One hybrid candidate after bounded SIE score reranking."""

    incident_id: str = Field(min_length=1)
    hybrid_seed_rank: PositiveInteger
    keyword_rank: PositiveInteger | None = None
    keyword_score: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    dense_rank: PositiveInteger | None = None
    cosine_similarity: float | None = Field(
        default=None,
        ge=-1.000001,
        le=1.000001,
        allow_inf_nan=False,
    )
    rerank_rank: PositiveInteger
    raw_relevance_score: float = Field(allow_inf_nan=False)


class HybridCandidatePoolBuilder:
    """Build a bounded deterministic union of keyword and dense candidates."""

    def __init__(self, *, maximum_candidates: int = 10) -> None:
        if maximum_candidates < 1 or maximum_candidates > 10:
            raise ValueError("hybrid candidate maximum must be between 1 and 10")
        self._maximum_candidates = maximum_candidates

    @property
    def maximum_candidates(self) -> int:
        """Expose the fixed hard cap used before score reranking."""
        return self._maximum_candidates

    def build(
        self,
        *,
        keyword_candidates: tuple[KeywordCandidate, ...],
        dense_candidates: tuple[DenseCandidate, ...],
    ) -> tuple[HybridCandidate, ...]:
        """Return a deduplicated lexical-first union with complete source traces."""

        self._validate_keyword_candidates(keyword_candidates)
        self._validate_dense_candidates(dense_candidates)

        by_id: dict[str, HybridCandidate] = {}
        ordered_ids: list[str] = []

        for candidate in keyword_candidates:
            by_id[candidate.incident_id] = HybridCandidate(
                incident_id=candidate.incident_id,
                hybrid_seed_rank=1,  # Reassigned after deterministic union construction.
                keyword_rank=candidate.rank,
                keyword_score=candidate.score,
            )
            ordered_ids.append(candidate.incident_id)

        for candidate in dense_candidates:
            existing = by_id.get(candidate.incident_id)
            if existing is None:
                by_id[candidate.incident_id] = HybridCandidate(
                    incident_id=candidate.incident_id,
                    hybrid_seed_rank=1,  # Reassigned after deterministic union construction.
                    dense_rank=candidate.rank,
                    cosine_similarity=candidate.cosine_similarity,
                )
                ordered_ids.append(candidate.incident_id)
                continue
            by_id[candidate.incident_id] = HybridCandidate(
                incident_id=existing.incident_id,
                hybrid_seed_rank=1,  # Reassigned after deterministic union construction.
                keyword_rank=existing.keyword_rank,
                keyword_score=existing.keyword_score,
                dense_rank=candidate.rank,
                cosine_similarity=candidate.cosine_similarity,
            )

        if len(ordered_ids) > self._maximum_candidates:
            raise HybridCandidatePoolError(
                "hybrid candidate union exceeded the configured bounded score pool"
            )

        return tuple(
            HybridCandidate(
                incident_id=by_id[incident_id].incident_id,
                hybrid_seed_rank=rank,
                keyword_rank=by_id[incident_id].keyword_rank,
                keyword_score=by_id[incident_id].keyword_score,
                dense_rank=by_id[incident_id].dense_rank,
                cosine_similarity=by_id[incident_id].cosine_similarity,
            )
            for rank, incident_id in enumerate(ordered_ids, start=1)
        )

    @staticmethod
    def _validate_keyword_candidates(candidates: tuple[KeywordCandidate, ...]) -> None:
        ranks = tuple(candidate.rank for candidate in candidates)
        ids = tuple(candidate.incident_id for candidate in candidates)
        if ranks and ranks != tuple(range(1, len(candidates) + 1)):
            raise HybridCandidatePoolError("keyword candidates must have contiguous ranks")
        if len(ids) != len(set(ids)):
            raise HybridCandidatePoolError("keyword candidates must have unique incident IDs")

    @staticmethod
    def _validate_dense_candidates(candidates: tuple[DenseCandidate, ...]) -> None:
        ranks = tuple(candidate.rank for candidate in candidates)
        ids = tuple(candidate.incident_id for candidate in candidates)
        if ranks and ranks != tuple(range(1, len(candidates) + 1)):
            raise HybridCandidatePoolError("dense candidates must have contiguous ranks")
        if len(ids) != len(set(ids)):
            raise HybridCandidatePoolError("dense candidates must have unique incident IDs")


class HybridTopKReranker:
    """Score-rerank only the bounded hybrid candidate set using typed SIE results."""

    def __init__(self, *, incidents: tuple[HistoricalIncidentCard, ...]) -> None:
        incident_by_id = {incident.incident_id: incident for incident in incidents}
        if len(incident_by_id) != len(incidents):
            raise HybridCandidatePoolError("approved incidents must have unique incident IDs")
        self._representation_by_id = {
            incident.incident_id: incident_retrieval_representation(incident)
            for incident in incidents
        }

    def rerank(
        self,
        *,
        query_text: str,
        hybrid_candidates: tuple[HybridCandidate, ...],
        client: SemanticInferenceClient,
        score_profile: InferenceProfile,
        trace_id: UUID,
    ) -> tuple[tuple[HybridRerankedCandidate, ...], float]:
        """Return the same hybrid identities in provider rank order."""

        self._validate_hybrid_candidates(hybrid_candidates)
        candidate_ids = tuple(candidate.incident_id for candidate in hybrid_candidates)
        response = client.score_incident_candidates(
            CandidateScoringRequest(
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
        )
        self._validate_score_response(
            requested_candidate_ids=candidate_ids,
            response_profile_id=response.profile_id,
            score_profile=score_profile,
            response_scores=response.scores,
        )
        seed_by_id = {candidate.incident_id: candidate for candidate in hybrid_candidates}
        return (
            tuple(
                HybridRerankedCandidate(
                    incident_id=score.candidate_id,
                    hybrid_seed_rank=seed_by_id[score.candidate_id].hybrid_seed_rank,
                    keyword_rank=seed_by_id[score.candidate_id].keyword_rank,
                    keyword_score=seed_by_id[score.candidate_id].keyword_score,
                    dense_rank=seed_by_id[score.candidate_id].dense_rank,
                    cosine_similarity=seed_by_id[score.candidate_id].cosine_similarity,
                    rerank_rank=score.rank,
                    raw_relevance_score=score.score,
                )
                for score in response.scores
            ),
            response.latency_ms,
        )

    def _validate_hybrid_candidates(self, candidates: tuple[HybridCandidate, ...]) -> None:
        if not candidates:
            raise HybridCandidatePoolError("hybrid reranking requires at least one candidate")
        if len(candidates) > 10:
            raise HybridCandidatePoolError("hybrid reranking may score at most ten candidates")
        ids = tuple(candidate.incident_id for candidate in candidates)
        ranks = tuple(candidate.hybrid_seed_rank for candidate in candidates)
        if len(ids) != len(set(ids)):
            raise HybridCandidatePoolError("hybrid candidates must have unique incident IDs")
        if ranks != tuple(range(1, len(candidates) + 1)):
            raise HybridCandidatePoolError("hybrid candidates must have contiguous seed ranks")
        unknown = set(ids).difference(self._representation_by_id)
        if unknown:
            raise HybridCandidatePoolError(
                "hybrid candidates must belong to the approved corpus"
            )

    @staticmethod
    def _validate_score_response(
        *,
        requested_candidate_ids: tuple[str, ...],
        response_profile_id: str,
        score_profile: InferenceProfile,
        response_scores: Iterable[object],
    ) -> None:
        scores = tuple(response_scores)
        if response_profile_id != score_profile.profile_id:
            raise HybridCandidatePoolError(
                "hybrid score response profile did not match the requested score profile"
            )
        response_ids = tuple(getattr(score, "candidate_id", None) for score in scores)
        if len(response_ids) != len(requested_candidate_ids) or set(response_ids) != set(
            requested_candidate_ids
        ):
            raise HybridCandidatePoolError(
                "hybrid score response candidate identities did not match the seed union"
            )
        ranks = tuple(getattr(score, "rank", None) for score in scores)
        if tuple(sorted(ranks)) != tuple(range(1, len(requested_candidate_ids) + 1)):
            raise HybridCandidatePoolError(
                "hybrid score response ranks must cover the seed union exactly once"
            )
