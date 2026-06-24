"""Pydantic contracts for the source-grounded synthetic incident dataset."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, model_validator

from incident_precedent_harness.domain.incident_enums import (
    ChangeContext,
    EvidenceDecisionState,
    IncidentFamily,
    ProcedureStatus,
    RecordOrigin,
    RecoveryState,
    RequiredVerificationFact,
    Severity,
    SourceUsageMode,
)


NonEmptyText = Annotated[str, Field(min_length=1, max_length=500)]
Identifier = Annotated[str, Field(pattern=r"^[A-Z]{2,8}-[0-9]{3,5}$")]
RecordIdentifier = Annotated[str, Field(pattern=r"^INC-[0-9]{3}$")]
ProcedureIdentifier = Annotated[str, Field(pattern=r"^RB-[0-9]{3}$")]
SourceIdentifier = Annotated[str, Field(pattern=r"^SRC-[0-9]{3}$")]
EvalIdentifier = Annotated[str, Field(pattern=r"^EVAL-[0-9]{3}$")]


class ProvenanceRecord(BaseModel):
    """Attribution and transformation record for one source-grounded item."""

    source_record_id: SourceIdentifier
    source_name: NonEmptyText
    source_url: HttpUrl
    source_date: date | None = None
    usage_mode: SourceUsageMode
    transformation_note: NonEmptyText
    human_verified: bool

    @model_validator(mode="after")
    def require_human_verification(self) -> "ProvenanceRecord":
        if not self.human_verified:
            raise ValueError("source-grounded provenance must be human verified")
        return self


class HistoricalIncidentCard(BaseModel):
    """A fictional RelayOps incident card with strict origin controls."""

    incident_id: RecordIdentifier
    title: NonEmptyText
    record_origin: RecordOrigin
    incident_family: IncidentFamily
    service: NonEmptyText
    component: NonEmptyText
    region: str | None = Field(default=None, min_length=1, max_length=64)
    severity: Severity
    started_after_change: bool | None
    change_context: ChangeContext
    symptoms: tuple[NonEmptyText, ...] = Field(min_length=1, max_length=12)
    observability_signals: tuple[NonEmptyText, ...] = Field(
        min_length=1,
        max_length=12,
    )
    failure_mechanism: NonEmptyText
    mitigation_summary: NonEmptyText
    recovery_state: RecoveryState
    timeline_summary: NonEmptyText
    linked_procedure_ids: tuple[ProcedureIdentifier, ...] = ()
    safe_procedure_ids: tuple[ProcedureIdentifier, ...] = ()
    unsafe_procedure_ids: tuple[ProcedureIdentifier, ...] = ()
    required_verification_facts: tuple[RequiredVerificationFact, ...] = ()
    narrative_safe: NonEmptyText
    provenance: ProvenanceRecord | None = None

    @model_validator(mode="after")
    def validate_origin_and_procedure_sets(self) -> "HistoricalIncidentCard":
        if self.record_origin is RecordOrigin.SOURCE_GROUNDED and self.provenance is None:
            raise ValueError("source_grounded incident cards require provenance")
        if self.record_origin is not RecordOrigin.SOURCE_GROUNDED and self.provenance is not None:
            raise ValueError(
                "controlled or synthetic incident cards must not impersonate a source record"
            )
        if set(self.safe_procedure_ids) & set(self.unsafe_procedure_ids):
            raise ValueError("a procedure cannot be both safe and unsafe for one incident")
        return self


class CandidateInvestigationProcedure(BaseModel):
    """A bounded, non-executable investigation artifact."""

    procedure_id: ProcedureIdentifier
    title: NonEmptyText
    version: NonEmptyText
    status: ProcedureStatus
    applicable_incident_families: tuple[IncidentFamily, ...] = Field(
        min_length=1,
        max_length=8,
    )
    not_applicable_when: tuple[IncidentFamily, ...] = ()
    verification_prerequisites: tuple[RequiredVerificationFact, ...] = ()
    safe_investigation_steps: tuple[NonEmptyText, ...] = Field(
        min_length=1,
        max_length=12,
    )
    unsafe_or_out_of_scope_actions: tuple[NonEmptyText, ...] = Field(
        min_length=1,
        max_length=12,
    )
    last_reviewed_at: date
    owner_role: NonEmptyText

    @model_validator(mode="after")
    def reject_self_conflicting_applicability(self) -> "CandidateInvestigationProcedure":
        if set(self.applicable_incident_families) & set(self.not_applicable_when):
            raise ValueError(
                "a procedure cannot be both applicable and explicitly inapplicable "
                "to the same incident family"
            )
        return self


class EvalCase(BaseModel):
    """Frozen scoring contract for one calibration or held-out case."""

    eval_id: EvalIdentifier
    split: str = Field(pattern=r"^(calibration|heldout)$")
    input_summary: NonEmptyText
    expected_decision_state: EvidenceDecisionState
    acceptable_precedent_ids: tuple[RecordIdentifier, ...] = ()
    unsafe_precedent_ids: tuple[RecordIdentifier, ...] = ()
    expected_candidate_procedure_ids: tuple[ProcedureIdentifier, ...] = ()
    expected_missing_facts: tuple[RequiredVerificationFact, ...] = ()
    failure_label_intent: tuple[NonEmptyText, ...] = Field(min_length=1, max_length=8)
    acceptance_reason: NonEmptyText

    @model_validator(mode="after")
    def validate_eval_safety_contract(self) -> "EvalCase":
        if set(self.acceptable_precedent_ids) & set(self.unsafe_precedent_ids):
            raise ValueError("acceptable and unsafe precedent sets must not overlap")
        if self.expected_decision_state is EvidenceDecisionState.INSUFFICIENT_PRECEDENT:
            if self.acceptable_precedent_ids:
                raise ValueError(
                    "insufficient_precedent cases cannot name acceptable precedents"
                )
            if self.expected_candidate_procedure_ids:
                raise ValueError(
                    "insufficient_precedent cases cannot name candidate procedures"
                )
        if self.expected_decision_state is EvidenceDecisionState.EVIDENCE_FOUND_WITH_CONFLICT:
            if len(self.acceptable_precedent_ids) < 2:
                raise ValueError(
                    "conflict cases require at least two acceptable precedent IDs"
                )
            if self.expected_candidate_procedure_ids:
                raise ValueError(
                    "conflict cases must not preselect a preferred procedure"
                )
        return self


class SourceManifestRecord(BaseModel):
    """One approved public source available for controlled, attributed adaptation."""

    source_record_id: SourceIdentifier
    source_name: NonEmptyText
    source_url: HttpUrl
    source_date: date | None = None
    usage_mode: SourceUsageMode
    licence_or_usage_note: NonEmptyText
    approved_for: tuple[NonEmptyText, ...] = Field(min_length=1, max_length=8)
    transformation_rules: tuple[NonEmptyText, ...] = Field(min_length=1, max_length=8)
    source_status: str = Field(pattern=r"^(approved|review_required|retired)$")
