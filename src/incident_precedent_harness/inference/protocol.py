"""Provider-neutral protocol for semantic inference capabilities."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from incident_precedent_harness.inference.models import (
    CandidateScoringRequest,
    CandidateScoringResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    IncidentExtractionRequest,
    IncidentExtractionResponse,
)


@runtime_checkable
class SemanticInferenceClient(Protocol):
    """Stable application contract implemented by fake and future SIE clients."""

    def extract_incident_signals(
        self,
        request: IncidentExtractionRequest,
    ) -> IncidentExtractionResponse:
        """Extract constrained candidate signals from sanitized incident text."""

    def encode_incident_texts(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Create dense representations for sanitized incident text items."""

    def score_incident_candidates(
        self,
        request: CandidateScoringRequest,
    ) -> CandidateScoringResponse:
        """Rank candidate incident texts against a sanitized query."""
