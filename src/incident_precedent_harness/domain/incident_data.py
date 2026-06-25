"""Pydantic contracts for the source-grounded synthetic incident dataset."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from incident_precedent_harness.domain.incident_enums import (
    ChangeContext,
    EvidenceDecisionState,
    IncidentFamily,
    OperationalSignalFamily,
    ProcedureStatus,
    RecordOrigin,
    RecoveryState,
    RelayComponent,
    RelayService,
    RequiredVerificationFact,
    SelectionSignalSourceField,
    Severity,
    SourceUsageMode,
    VerificationFactStatus,
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


class SelectionSignalSourceReference(BaseModel):
    """Exact canonical card values grounding one operational signal family."""

    model_config = ConfigDict(extra="forbid")

    source_field: SelectionSignalSourceField
    source_values: tuple[NonEmptyText, ...] = Field(min_length=1, max_length=12)

    @field_validator("source_values")
    @classmethod
    def reject_duplicate_source_values(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("selection source_values must not repeat a canonical card value")
        return value


class SelectionSignalEvidence(BaseModel):
    """One independently counted signal family with canonical source references."""

    model_config = ConfigDict(extra="forbid")

    signal_family: OperationalSignalFamily
    source_references: tuple[SelectionSignalSourceReference, ...] = Field(
        min_length=1,
        max_length=4,
    )

    @field_validator("source_references")
    @classmethod
    def reject_duplicate_source_references(
        cls,
        value: tuple[SelectionSignalSourceReference, ...],
    ) -> tuple[SelectionSignalSourceReference, ...]:
        source_keys = [
            (reference.source_field, reference.source_values)
            for reference in value
        ]
        if len(set(source_keys)) != len(source_keys):
            raise ValueError("selection source_references must not repeat")
        return value


class RepresentativeSelectionSignature(BaseModel):
    """Schema-derived, candidate-side evidence permitted for later selection."""

    model_config = ConfigDict(extra="forbid")

    contract_version: Literal["representative-selection-v1"]
    service: RelayService
    component: RelayComponent
    change_context: ChangeContext
    operational_signals: tuple[SelectionSignalEvidence, ...] = Field(
        min_length=1,
        max_length=12,
    )

    @field_validator("operational_signals")
    @classmethod
    def reject_duplicate_operational_signal_families(
        cls,
        value: tuple[SelectionSignalEvidence, ...],
    ) -> tuple[SelectionSignalEvidence, ...]:
        signal_families = [signal.signal_family for signal in value]
        if len(set(signal_families)) != len(signal_families):
            raise ValueError("selection signatures must not repeat an operational signal family")
        return value


class RepresentativeSelectionIntake(BaseModel):
    """Typed selection evidence independent from evaluation labels and retrieval."""

    model_config = ConfigDict(extra="forbid")

    service: RelayService | None = None
    component: RelayComponent | None = None
    change_context: ChangeContext | None = None
    operational_signal_families: tuple[OperationalSignalFamily, ...] = ()
    contradicted_signal_families: tuple[OperationalSignalFamily, ...] = ()

    @field_validator("operational_signal_families", "contradicted_signal_families")
    @classmethod
    def reject_duplicate_signal_families(
        cls,
        value: tuple[OperationalSignalFamily, ...],
    ) -> tuple[OperationalSignalFamily, ...]:
        if len(set(value)) != len(value):
            raise ValueError("selection intake signal families must not repeat")
        return value

    @model_validator(mode="after")
    def reject_overlapping_signal_statuses(self) -> "RepresentativeSelectionIntake":
        overlap = set(self.operational_signal_families) & set(
            self.contradicted_signal_families
        )
        if overlap:
            joined = ", ".join(sorted(signal.value for signal in overlap))
            raise ValueError(
                "selection intake cannot confirm and contradict the same signal family: "
                f"{joined}"
            )
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
    selection_signature: RepresentativeSelectionSignature | None = None

    @model_validator(mode="after")
    def validate_origin_procedure_sets_and_selection_signature(
        self,
    ) -> "HistoricalIncidentCard":
        if self.record_origin is RecordOrigin.SOURCE_GROUNDED and self.provenance is None:
            raise ValueError("source_grounded incident cards require provenance")
        if self.record_origin is not RecordOrigin.SOURCE_GROUNDED and self.provenance is not None:
            raise ValueError(
                "controlled or synthetic incident cards must not impersonate a source record"
            )
        if set(self.safe_procedure_ids) & set(self.unsafe_procedure_ids):
            raise ValueError("a procedure cannot be both safe and unsafe for one incident")

        if self.incident_family is IncidentFamily.CONNECTION_POOL_EXHAUSTION:
            if self.selection_signature is None:
                raise ValueError(
                    "connection_pool_exhaustion cards require a schema-derived selection_signature"
                )
            self._validate_selection_signature()
        elif self.selection_signature is not None:
            raise ValueError(
                "selection_signature is only permitted for connection_pool_exhaustion "
                "cards in the current schema-hardening slice"
            )
        return self

    def _validate_selection_signature(self) -> None:
        signature = self.selection_signature
        if signature is None:
            raise ValueError("selection signature is required")

        if signature.service.value != self.service:
            raise ValueError(
                "selection_signature.service must equal the parent card service"
            )
        if signature.component.value != self.component:
            raise ValueError(
                "selection_signature.component must equal the parent card component"
            )
        if signature.change_context is not self.change_context:
            raise ValueError(
                "selection_signature.change_context must equal the parent card change_context"
            )

        source_values_by_field = {
            SelectionSignalSourceField.SYMPTOMS: set(self.symptoms),
            SelectionSignalSourceField.OBSERVABILITY_SIGNALS: set(
                self.observability_signals
            ),
        }
        for signal in signature.operational_signals:
            for reference in signal.source_references:
                available_values = source_values_by_field[reference.source_field]
                invalid_values = set(reference.source_values) - available_values
                if invalid_values:
                    joined = ", ".join(sorted(invalid_values))
                    raise ValueError(
                        "selection signature source values must appear in the parent "
                        f"{reference.source_field.value}: {joined}"
                    )


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


class ObservedVerificationFact(BaseModel):
    """One structured fact supplied with a simulated incident intake."""

    fact: RequiredVerificationFact
    status: VerificationFactStatus


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
    observed_facts: tuple[ObservedVerificationFact, ...] = ()
    provider_available: bool = True
    failure_label_intent: tuple[NonEmptyText, ...] = Field(min_length=1, max_length=8)
    acceptance_reason: NonEmptyText

    @model_validator(mode="after")
    def validate_eval_safety_contract(self) -> "EvalCase":
        observed_fact_names = [observation.fact for observation in self.observed_facts]
        if len(observed_fact_names) != len(set(observed_fact_names)):
            raise ValueError("observed_facts must not repeat a verification fact")
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
