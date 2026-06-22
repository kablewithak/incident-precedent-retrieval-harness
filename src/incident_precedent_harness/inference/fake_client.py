"""Deterministic fake provider for ordinary local and CI validation.

This client is intentionally not a model. It provides reproducible behavior so that
policy and evaluation work are not coupled to Docker, model downloads, or network I/O.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Collection

from incident_precedent_harness.domain.enums import ProviderFailureCode, ProviderOperation
from incident_precedent_harness.inference.errors import SemanticInferenceError
from incident_precedent_harness.inference.models import (
    CandidateScore,
    CandidateScoringRequest,
    CandidateScoringResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    EncodedVector,
    ExtractedSignal,
    IncidentExtractionRequest,
    IncidentExtractionResponse,
    ProviderFailure,
)

_TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")


class FakeSemanticInferenceClient:
    """A deterministic implementation of the semantic inference protocol."""

    def __init__(
        self,
        *,
        fail_operations: Collection[ProviderOperation] = (),
        embedding_dimensions: int = 8,
    ) -> None:
        if embedding_dimensions < 2:
            raise ValueError("embedding_dimensions must be at least 2")
        self._fail_operations = frozenset(fail_operations)
        self._embedding_dimensions = embedding_dimensions

    def extract_incident_signals(
        self,
        request: IncidentExtractionRequest,
    ) -> IncidentExtractionResponse:
        self._raise_if_configured_to_fail(
            operation=ProviderOperation.EXTRACT,
            trace_id=request.trace_id,
            profile_id=request.profile.profile_id,
        )

        text = request.item.text.casefold()
        allowed_labels = {label.casefold() for label in request.labels}
        candidates = (
            ("change_context", "deployment", "deploy"),
            ("symptom", "queue_backlog", "queue"),
            ("component", "background_worker", "worker"),
            ("symptom", "upstream_timeout", "timeout"),
        )
        signals = tuple(
            ExtractedSignal(label=label, value=value, confidence=1.0)
            for label, value, trigger in candidates
            if label in allowed_labels and trigger in text
        )
        return IncidentExtractionResponse(
            trace_id=request.trace_id,
            profile_id=request.profile.profile_id,
            signals=signals,
            latency_ms=0,
        )

    def encode_incident_texts(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self._raise_if_configured_to_fail(
            operation=ProviderOperation.ENCODE,
            trace_id=request.trace_id,
            profile_id=request.profile.profile_id,
        )
        vectors = tuple(
            EncodedVector(
                item_id=item.item_id,
                dense_values=self._deterministic_unit_vector(item.text),
            )
            for item in request.items
        )
        return EmbeddingResponse(
            trace_id=request.trace_id,
            profile_id=request.profile.profile_id,
            vectors=vectors,
            latency_ms=0,
        )

    def score_incident_candidates(
        self,
        request: CandidateScoringRequest,
    ) -> CandidateScoringResponse:
        self._raise_if_configured_to_fail(
            operation=ProviderOperation.SCORE,
            trace_id=request.trace_id,
            profile_id=request.profile.profile_id,
        )
        query_terms = set(self._tokenize(request.query.text))
        ranked = sorted(
            (
                (
                    candidate.item_id,
                    self._lexical_overlap_score(query_terms, set(self._tokenize(candidate.text))),
                    position,
                )
                for position, candidate in enumerate(request.candidates)
            ),
            key=lambda item: (-item[1], item[2]),
        )
        scores = tuple(
            CandidateScore(candidate_id=item_id, rank=rank, score=score)
            for rank, (item_id, score, _) in enumerate(ranked, start=1)
        )
        return CandidateScoringResponse(
            trace_id=request.trace_id,
            profile_id=request.profile.profile_id,
            scores=scores,
            latency_ms=0,
        )

    def _raise_if_configured_to_fail(
        self,
        *,
        operation: ProviderOperation,
        trace_id: object,
        profile_id: str,
    ) -> None:
        if operation not in self._fail_operations:
            return
        raise SemanticInferenceError(
            ProviderFailure(
                trace_id=trace_id,
                profile_id=profile_id,
                operation=operation,
                code=ProviderFailureCode.PROVIDER_UNAVAILABLE,
                safe_message="Configured fake provider failure.",
                retryable=False,
            )
        )

    def _deterministic_unit_vector(self, text: str) -> tuple[float, ...]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = tuple(
            (digest[index] / 255.0) * 2.0 - 1.0
            for index in range(self._embedding_dimensions)
        )
        magnitude = math.sqrt(sum(value * value for value in values))
        return tuple(value / magnitude for value in values)

    @staticmethod
    def _tokenize(text: str) -> tuple[str, ...]:
        return tuple(_TOKEN_PATTERN.findall(text.casefold()))

    @staticmethod
    def _lexical_overlap_score(query_terms: set[str], candidate_terms: set[str]) -> float:
        if not query_terms:
            return 0.0
        return len(query_terms & candidate_terms) / len(query_terms)
