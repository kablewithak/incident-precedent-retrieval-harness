"""Typed requests and responses at the semantic inference boundary."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from incident_precedent_harness.domain.enums import ProviderFailureCode, ProviderOperation


class TextItem(BaseModel):
    """A bounded, sanitized text item supplied to an inference operation."""

    item_id: str = Field(min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=4_000)


class InferenceProfile(BaseModel):
    """Provider operation configuration kept outside domain decision logic."""

    profile_id: str = Field(min_length=1, max_length=128)
    provider_name: str = Field(min_length=1, max_length=64)
    operation: ProviderOperation
    model_id: str = Field(min_length=1, max_length=256)
    timeout_ms: int = Field(gt=0, le=120_000)
    max_retries: int = Field(ge=0, le=3)


class IncidentExtractionRequest(BaseModel):
    """Request to derive constrained candidate signals from sanitized text."""

    trace_id: UUID
    profile: InferenceProfile
    item: TextItem
    labels: tuple[str, ...] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def validate_operation(self) -> "IncidentExtractionRequest":
        if self.profile.operation is not ProviderOperation.EXTRACT:
            raise ValueError("incident extraction requires an extract profile")
        return self


class ExtractedSignal(BaseModel):
    """A candidate signal returned by an inference provider."""

    label: str = Field(min_length=1, max_length=128)
    value: str = Field(min_length=1, max_length=512)
    confidence: float = Field(ge=0, le=1)


class IncidentExtractionResponse(BaseModel):
    """Validated extraction response with trace-safe metadata."""

    trace_id: UUID
    profile_id: str
    signals: tuple[ExtractedSignal, ...]
    latency_ms: int = Field(ge=0)


class EmbeddingRequest(BaseModel):
    """Request for dense representations of one or more sanitized text items."""

    trace_id: UUID
    profile: InferenceProfile
    items: tuple[TextItem, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_operation(self) -> "EmbeddingRequest":
        if self.profile.operation is not ProviderOperation.ENCODE:
            raise ValueError("embedding requires an encode profile")
        return self


class EncodedVector(BaseModel):
    """A dense vector tied to its input item identifier."""

    item_id: str = Field(min_length=1, max_length=128)
    dense_values: tuple[float, ...] = Field(min_length=1, max_length=4_096)


class EmbeddingResponse(BaseModel):
    """Validated dense embedding response with trace-safe metadata."""

    trace_id: UUID
    profile_id: str
    vectors: tuple[EncodedVector, ...]
    latency_ms: int = Field(ge=0)


class CandidateScoringRequest(BaseModel):
    """Request to rank candidate incident texts against a query."""

    trace_id: UUID
    profile: InferenceProfile
    query: TextItem
    candidates: tuple[TextItem, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_operation(self) -> "CandidateScoringRequest":
        if self.profile.operation is not ProviderOperation.SCORE:
            raise ValueError("candidate scoring requires a score profile")
        return self


class CandidateScore(BaseModel):
    """A scored candidate ordered from most to least relevant.

    ``score`` is a provider-native raw relevance value, not a calibrated
    probability. It may therefore be negative or greater than one. Ordering is
    governed by ``rank``; the value is retained only as traceable ranking
    evidence and must be finite.
    """

    candidate_id: str = Field(min_length=1, max_length=128)
    rank: int = Field(ge=1)
    score: float = Field(allow_inf_nan=False)


class CandidateScoringResponse(BaseModel):
    """Validated candidate ranking response with trace-safe metadata."""

    trace_id: UUID
    profile_id: str
    scores: tuple[CandidateScore, ...]
    latency_ms: int = Field(ge=0)


class ProviderFailure(BaseModel):
    """Sanitized provider failure suitable for policy handling and safe traces."""

    trace_id: UUID
    profile_id: str
    operation: ProviderOperation
    code: ProviderFailureCode
    safe_message: str = Field(min_length=1, max_length=512)
    retryable: bool
