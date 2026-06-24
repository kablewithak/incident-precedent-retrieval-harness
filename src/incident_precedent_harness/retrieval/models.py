"""Typed, provider-neutral contracts for deterministic lexical retrieval."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from incident_precedent_harness.domain.incident_data import EvalIdentifier, RecordIdentifier

NonNegativeFloat = Annotated[float, Field(ge=0)]
PositiveInteger = Annotated[int, Field(ge=1)]


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
