"""Typed contracts for lexical and dense retrieval evidence."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from incident_precedent_harness.domain.incident_data import EvalIdentifier, RecordIdentifier
from incident_precedent_harness.inference.models import InferenceProfile

NonNegativeFloat = Annotated[float, Field(ge=0)]
PositiveInteger = Annotated[int, Field(ge=1)]
Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class KeywordCandidate(BaseModel):
    """One ranked lexical candidate with transparent match evidence."""

    incident_id: RecordIdentifier
    rank: PositiveInteger
    score: NonNegativeFloat
    matched_terms: tuple[str, ...] = ()

    @field_validator("matched_terms")
    @classmethod
    def require_unique_sorted_terms(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if tuple(sorted(set(value))) != value:
            raise ValueError("matched_terms must be unique and sorted")
        return value


class KeywordCaseOutcome(BaseModel):
    """One calibration-case result for the keyword baseline."""

    eval_id: EvalIdentifier
    expected_decision_state: str
    candidate_ids: tuple[RecordIdentifier, ...]
    candidate_incident_families: tuple[str, ...]
    expected_incident_families: tuple[str, ...]
    acceptable_precedent_ids: tuple[RecordIdentifier, ...]
    unsafe_precedent_ids: tuple[RecordIdentifier, ...]
    first_acceptable_rank: int | None = Field(default=None, ge=1)
    top_1_is_unsafe: bool
    query_latency_ms: NonNegativeFloat
    failure_labels: tuple[str, ...] = ()


class KeywordBaselineMetrics(BaseModel):
    """Metrics that a lexical ranker can legitimately measure at this stage."""

    scored_case_count: int = Field(ge=0)
    cases_with_acceptable_precedent: int = Field(ge=0)
    correct_precedent_mrr: float | None = Field(default=None, ge=0, le=1)
    incident_family_recall_at_5: float | None = Field(default=None, ge=0, le=1)
    safety_evaluable_case_count: int = Field(ge=0)
    safe_precedent_top_1_rate: float | None = Field(default=None, ge=0, le=1)
    false_operational_match_count: int = Field(ge=0)
    false_operational_match_rate: float | None = Field(default=None, ge=0, le=1)
    p50_query_latency_ms: NonNegativeFloat
    p95_query_latency_ms: NonNegativeFloat


class KeywordBaselineReport(BaseModel):
    """Reproducible calibration-only report for the deterministic baseline."""

    report_kind: str = "keyword_baseline_calibration"
    generated_at: datetime
    corpus_incident_count: int = Field(ge=0)
    calibration_case_count: int = Field(ge=0)
    top_k: PositiveInteger
    tokenization: str
    ranking_algorithm: str
    metrics: KeywordBaselineMetrics
    outcomes: tuple[KeywordCaseOutcome, ...]
    known_limits: tuple[str, ...] = Field(min_length=1)


class DenseIndexEntry(BaseModel):
    """One approved incident representation and its local dense vector."""

    incident_id: RecordIdentifier
    representation_sha256: Sha256Hex
    dense_values: tuple[float, ...] = Field(min_length=1, max_length=4_096)

    @field_validator("dense_values")
    @classmethod
    def require_finite_vector(cls, value: tuple[float, ...]) -> tuple[float, ...]:
        if not all(math.isfinite(item) for item in value):
            raise ValueError("dense index vectors must contain finite values")
        if not any(item != 0.0 for item in value):
            raise ValueError("dense index vectors must not be all zero")
        return value


class DenseIndexManifest(BaseModel):
    """Metadata binding a generated local index to its approved source corpus."""

    index_format_version: Literal["local-dense-index-v1"]
    index_id: str = Field(min_length=1, max_length=128)
    built_at: datetime
    corpus_incident_count: int = Field(gt=0)
    corpus_fingerprint_sha256: Sha256Hex
    representation_version: Literal["incident-retrieval-representation-v1"]
    embedding_profile: InferenceProfile
    vector_dimension: PositiveInteger


class LocalDenseIndex(BaseModel):
    """Versioned, serializable local dense index with strict integrity checks."""

    manifest: DenseIndexManifest
    entries: tuple[DenseIndexEntry, ...] = Field(min_length=1, max_length=512)

    @model_validator(mode="after")
    def validate_entries_against_manifest(self) -> "LocalDenseIndex":
        incident_ids = [entry.incident_id for entry in self.entries]
        if len(incident_ids) != len(set(incident_ids)):
            raise ValueError("dense index entries must have unique incident IDs")
        if tuple(sorted(incident_ids)) != tuple(incident_ids):
            raise ValueError("dense index entries must be sorted by incident ID")
        if len(self.entries) != self.manifest.corpus_incident_count:
            raise ValueError("dense index entry count must match manifest corpus count")
        dimensions = {len(entry.dense_values) for entry in self.entries}
        if dimensions != {self.manifest.vector_dimension}:
            raise ValueError("dense index entry dimensions must match manifest dimension")
        return self


class DenseCandidate(BaseModel):
    """One cosine-ranked candidate from a validated local dense index."""

    incident_id: RecordIdentifier
    rank: PositiveInteger
    cosine_similarity: float = Field(ge=-1.000001, le=1.000001, allow_inf_nan=False)


class DenseCaseOutcome(BaseModel):
    """One calibration-case dense retrieval result."""

    eval_id: EvalIdentifier
    expected_decision_state: str
    candidate_ids: tuple[RecordIdentifier, ...]
    candidate_incident_families: tuple[str, ...]
    expected_incident_families: tuple[str, ...]
    acceptable_precedent_ids: tuple[RecordIdentifier, ...]
    unsafe_precedent_ids: tuple[RecordIdentifier, ...]
    first_acceptable_rank: int | None = Field(default=None, ge=1)
    top_1_is_unsafe: bool
    similarity_latency_ms: NonNegativeFloat
    failure_labels: tuple[str, ...] = ()


class DenseRetrievalMetrics(BaseModel):
    """Calibration metrics for dense retrieval before reranking or policy."""

    scored_case_count: int = Field(ge=0)
    cases_with_acceptable_precedent: int = Field(ge=0)
    correct_precedent_mrr: float | None = Field(default=None, ge=0, le=1)
    incident_family_recall_at_5: float | None = Field(default=None, ge=0, le=1)
    safety_evaluable_case_count: int = Field(ge=0)
    safe_precedent_top_1_rate: float | None = Field(default=None, ge=0, le=1)
    false_operational_match_count: int = Field(ge=0)
    false_operational_match_rate: float | None = Field(default=None, ge=0, le=1)
    p50_similarity_latency_ms: NonNegativeFloat
    p95_similarity_latency_ms: NonNegativeFloat


class DenseVsKeywordComparison(BaseModel):
    """Side-by-side calibration-only comparison. It is not a promotion decision."""

    keyword_correct_precedent_mrr: float | None = Field(default=None, ge=0, le=1)
    dense_correct_precedent_mrr: float | None = Field(default=None, ge=0, le=1)
    correct_precedent_mrr_delta: float | None = None
    keyword_incident_family_recall_at_5: float | None = Field(default=None, ge=0, le=1)
    dense_incident_family_recall_at_5: float | None = Field(default=None, ge=0, le=1)
    incident_family_recall_at_5_delta: float | None = None
    keyword_false_operational_match_rate: float | None = Field(default=None, ge=0, le=1)
    dense_false_operational_match_rate: float | None = Field(default=None, ge=0, le=1)
    false_operational_match_rate_delta: float | None = None


class DenseRetrievalCalibrationReport(BaseModel):
    """Saved calibration-only evidence for local-SIE dense retrieval."""

    report_kind: Literal["local_sie_dense_retrieval_calibration"] = (
        "local_sie_dense_retrieval_calibration"
    )
    generated_at: datetime
    corpus_incident_count: int = Field(gt=0)
    calibration_case_count: int = Field(gt=0)
    top_k: PositiveInteger
    index_manifest: DenseIndexManifest
    query_embedding_profile: InferenceProfile
    query_embedding_batch_latency_ms: NonNegativeFloat
    metrics: DenseRetrievalMetrics
    keyword_baseline_metrics: KeywordBaselineMetrics
    comparison_to_keyword_baseline: DenseVsKeywordComparison
    outcomes: tuple[DenseCaseOutcome, ...]
    known_limits: tuple[str, ...] = Field(min_length=1)
