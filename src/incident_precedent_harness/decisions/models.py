"""Typed deterministic anti-anchoring policy and shadow-selection contracts."""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from incident_precedent_harness.decisions.strict_dominance_selection import (
    CandidateSelectionEvidence,
)
from incident_precedent_harness.domain.incident_data import (
    ProcedureIdentifier,
    RecordIdentifier,
    RepresentativeSelectionIntake,
)
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


class FamilyAdmissionSet(BaseModel):
    """Private, trace-safe inventory of compatibility-admitted cards in one family.

    This contract exists only to preserve the candidate pool for shadow analysis.
    It does not replace the first-compatible-card behavior exposed by
    ``PolicyDecisionResult``.
    """

    model_config = ConfigDict(extra="forbid")

    incident_family: IncidentFamily
    admitted_candidate_ids: tuple[RecordIdentifier, ...] = Field(min_length=1, max_length=12)

    @field_validator("admitted_candidate_ids")
    @classmethod
    def validate_deterministic_unique_ids(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("admitted_candidate_ids must not repeat")
        if tuple(sorted(value)) != value:
            raise ValueError("admitted_candidate_ids must use deterministic serialization order")
        return value


class ShadowSelectionState(str, Enum):
    """Trace-only outcomes. These are not product decision states."""

    NOT_APPLICABLE_SINGLE_CANDIDATE = "not_applicable_single_candidate"
    UNAVAILABLE = "unavailable"
    SINGLE_REPRESENTATIVE = "single_representative"
    EXPLICIT_TIE = "explicit_tie"


class FamilySelectionIntakeBinding(BaseModel):
    """Explicit typed bridge between one policy family and selection evidence."""

    model_config = ConfigDict(extra="forbid")

    incident_family: IncidentFamily
    selection_intake: RepresentativeSelectionIntake


class PolicyShadowRequest(BaseModel):
    """Trace-only selection inputs kept separate from normal policy intake."""

    model_config = ConfigDict(extra="forbid")

    selection_intake_bindings: tuple[FamilySelectionIntakeBinding, ...] = ()

    @field_validator("selection_intake_bindings")
    @classmethod
    def reject_duplicate_family_bindings(
        cls,
        value: tuple[FamilySelectionIntakeBinding, ...],
    ) -> tuple[FamilySelectionIntakeBinding, ...]:
        families = [binding.incident_family for binding in value]
        if len(set(families)) != len(families):
            raise ValueError("selection_intake_bindings must not repeat an incident family")
        return value

    def selection_intake_for(
        self,
        incident_family: IncidentFamily,
    ) -> RepresentativeSelectionIntake | None:
        for binding in self.selection_intake_bindings:
            if binding.incident_family is incident_family:
                return binding.selection_intake
        return None


class FamilyRepresentativeSelectionTrace(BaseModel):
    """Inspectable shadow result that cannot modify policy state or procedures."""

    model_config = ConfigDict(extra="forbid")

    incident_family: IncidentFamily
    admitted_candidate_ids: tuple[RecordIdentifier, ...] = Field(min_length=1, max_length=12)
    selection_intake_present: bool
    selector_invoked: bool
    selection_state: ShadowSelectionState
    representative_incident_ids: tuple[RecordIdentifier, ...] = ()
    unavailable_reason: NonEmptyText | None = None
    candidate_evidence: tuple[CandidateSelectionEvidence, ...] = ()

    @model_validator(mode="after")
    def validate_shadow_trace_contract(self) -> "FamilyRepresentativeSelectionTrace":
        if len(set(self.admitted_candidate_ids)) != len(self.admitted_candidate_ids):
            raise ValueError("admitted_candidate_ids must not repeat")
        if tuple(sorted(self.admitted_candidate_ids)) != self.admitted_candidate_ids:
            raise ValueError("admitted_candidate_ids must use deterministic serialization order")

        if self.selection_state is ShadowSelectionState.NOT_APPLICABLE_SINGLE_CANDIDATE:
            if len(self.admitted_candidate_ids) != 1:
                raise ValueError("single-candidate bypass requires exactly one admitted card")
            if self.selector_invoked or self.representative_incident_ids or self.candidate_evidence:
                raise ValueError("single-candidate bypass cannot invoke or serialize selector output")
            if self.unavailable_reason is None:
                raise ValueError("single-candidate bypass requires a trace-safe reason")

        if self.selection_state is ShadowSelectionState.UNAVAILABLE:
            if self.selector_invoked or self.representative_incident_ids or self.candidate_evidence:
                raise ValueError("unavailable traces cannot expose selector output")
            if self.unavailable_reason is None:
                raise ValueError("unavailable traces require a trace-safe reason")

        if self.selection_state is ShadowSelectionState.SINGLE_REPRESENTATIVE:
            if not self.selector_invoked or len(self.representative_incident_ids) != 1:
                raise ValueError("single representative traces require one selector result")
            if self.unavailable_reason is not None:
                raise ValueError("selected traces cannot carry unavailable_reason")

        if self.selection_state is ShadowSelectionState.EXPLICIT_TIE:
            if not self.selector_invoked or len(self.representative_incident_ids) < 2:
                raise ValueError("explicit tie traces require a selector tie set")
            if self.unavailable_reason is not None:
                raise ValueError("selected traces cannot carry unavailable_reason")

        if not set(self.representative_incident_ids).issubset(self.admitted_candidate_ids):
            raise ValueError("representative IDs must be policy-admitted candidate IDs")
        return self


class PolicyShadowEvaluationResult(BaseModel):
    """Policy result plus private admission sets and trace-only selector observations."""

    model_config = ConfigDict(extra="forbid")

    policy_result: PolicyDecisionResult
    family_admission_sets: tuple[FamilyAdmissionSet, ...] = ()
    selection_traces: tuple[FamilyRepresentativeSelectionTrace, ...] = ()

    @model_validator(mode="after")
    def validate_trace_admission_alignment(self) -> "PolicyShadowEvaluationResult":
        admission_by_family = {
            admission.incident_family: admission.admitted_candidate_ids
            for admission in self.family_admission_sets
        }
        if len(admission_by_family) != len(self.family_admission_sets):
            raise ValueError("family_admission_sets must not repeat an incident family")
        trace_families = [trace.incident_family for trace in self.selection_traces]
        if len(set(trace_families)) != len(trace_families):
            raise ValueError("selection_traces must not repeat an incident family")
        for trace in self.selection_traces:
            if admission_by_family.get(trace.incident_family) != trace.admitted_candidate_ids:
                raise ValueError("each trace must mirror its private family admission set")
        return self
