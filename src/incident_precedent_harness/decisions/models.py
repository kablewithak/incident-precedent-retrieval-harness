"""Typed deterministic anti-anchoring policy contracts."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, Field

from incident_precedent_harness.domain.incident_data import ProcedureIdentifier, RecordIdentifier
from incident_precedent_harness.domain.incident_enums import (
    EvidenceDecisionState,
    IncidentFamily,
    RequiredVerificationFact,
)

NonEmptyText = Annotated[str, Field(min_length=1, max_length=500)]


class CandidatePolicyAssessment(BaseModel):
    """Why a ranked incident was retained or blocked by deterministic policy."""

    incident_id: RecordIdentifier
    incident_family: IncidentFamily
    retained: bool
    missing_facts: tuple[RequiredVerificationFact, ...] = ()
    contradicted_facts: tuple[RequiredVerificationFact, ...] = ()
    reasons: tuple[NonEmptyText, ...] = Field(min_length=1, max_length=8)


class PolicyDecisionResult(BaseModel):
    """Safe policy output before any user-facing rendering layer exists."""

    decision_state: EvidenceDecisionState
    human_review_required: bool = True
    retained_precedent_ids: tuple[RecordIdentifier, ...] = ()
    candidate_procedure_ids: tuple[ProcedureIdentifier, ...] = ()
    missing_critical_facts: tuple[RequiredVerificationFact, ...] = ()
    conflict_summary: str | None = None
    assessments: tuple[CandidatePolicyAssessment, ...]
    safety_notes: tuple[NonEmptyText, ...] = Field(min_length=1, max_length=8)
