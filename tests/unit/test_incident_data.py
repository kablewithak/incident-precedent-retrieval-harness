from datetime import date

import pytest
from pydantic import ValidationError

from incident_precedent_harness.domain.incident_data import (
    CandidateInvestigationProcedure,
    EvalCase,
    HistoricalIncidentCard,
    ProvenanceRecord,
    SourceManifestRecord,
)
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


def source_provenance() -> ProvenanceRecord:
    return ProvenanceRecord(
        source_record_id="SRC-001",
        source_name="Approved public postmortem source",
        source_url="https://example.com/postmortem",
        source_date=date(2025, 1, 1),
        usage_mode=SourceUsageMode.CITED_REFERENCE,
        transformation_note="Mechanism adapted into fictional RelayOps record.",
        human_verified=True,
    )


def incident(**overrides: object) -> HistoricalIncidentCard:
    values: dict[str, object] = {
        "incident_id": "INC-001",
        "title": "Queue backlog after worker deployment",
        "record_origin": RecordOrigin.SOURCE_GROUNDED,
        "incident_family": IncidentFamily.QUEUE_BACKLOG_CONSUMER_FAILURE,
        "service": "workflow-service",
        "component": "webhook-worker",
        "severity": Severity.SEV_2,
        "started_after_change": True,
        "change_context": ChangeContext.DEPLOYMENT,
        "symptoms": ("queue_backlog", "worker_errors"),
        "observability_signals": ("queue_depth_increase", "consumer_error_rate"),
        "failure_mechanism": "Consumer rejected incompatible event payloads.",
        "mitigation_summary": "Service recovered after a compatible deployment.",
        "recovery_state": RecoveryState.RECOVERED,
        "timeline_summary": "Backlog began shortly after a deploy.",
        "linked_procedure_ids": ("RB-001",),
        "safe_procedure_ids": ("RB-001",),
        "required_verification_facts": (
            RequiredVerificationFact.CONSUMER_ERROR_RATE,
            RequiredVerificationFact.WORKER_DEPLOYMENT_VERSION,
        ),
        "narrative_safe": "Synthetic source-grounded incident summary.",
        "provenance": source_provenance(),
    }
    values.update(overrides)
    return HistoricalIncidentCard(**values)


def test_source_grounded_incident_requires_human_verified_provenance() -> None:
    with pytest.raises(ValidationError, match="source_grounded incident cards require provenance"):
        incident(provenance=None)


def test_controlled_variant_cannot_impersonate_a_source_record() -> None:
    with pytest.raises(
        ValidationError,
        match="controlled or synthetic incident cards must not impersonate",
    ):
        incident(record_origin=RecordOrigin.CONTROLLED_VARIANT)


def test_incident_rejects_a_procedure_marked_both_safe_and_unsafe() -> None:
    with pytest.raises(ValidationError, match="both safe and unsafe"):
        incident(unsafe_procedure_ids=("RB-001",))


def test_no_precedent_case_cannot_name_a_candidate_procedure() -> None:
    with pytest.raises(ValidationError, match="cannot name candidate procedures"):
        EvalCase(
            eval_id="EVAL-001",
            split="heldout",
            input_summary="Synthetic novel failure without credible precedent.",
            expected_decision_state=EvidenceDecisionState.INSUFFICIENT_PRECEDENT,
            expected_candidate_procedure_ids=("RB-001",),
            failure_label_intent=("insufficient_precedent",),
            acceptance_reason="Tests abstention rather than forced retrieval.",
        )


def test_conflict_case_requires_multiple_precedents_and_no_preselected_procedure() -> None:
    with pytest.raises(ValidationError, match="at least two acceptable"):
        EvalCase(
            eval_id="EVAL-002",
            split="heldout",
            input_summary="Synthetic incident with two divergent historical paths.",
            expected_decision_state=EvidenceDecisionState.EVIDENCE_FOUND_WITH_CONFLICT,
            acceptable_precedent_ids=("INC-001",),
            failure_label_intent=("conflicting_precedent",),
            acceptance_reason="Tests whether policy avoids false certainty.",
        )


def test_candidate_procedure_rejects_self_conflicting_applicability() -> None:
    with pytest.raises(ValidationError, match="both applicable and explicitly inapplicable"):
        CandidateInvestigationProcedure(
            procedure_id="RB-001",
            title="Inspect consumer failure signals",
            version="1.0",
            status=ProcedureStatus.CURRENT,
            applicable_incident_families=(
                IncidentFamily.QUEUE_BACKLOG_CONSUMER_FAILURE,
            ),
            not_applicable_when=(
                IncidentFamily.QUEUE_BACKLOG_CONSUMER_FAILURE,
            ),
            verification_prerequisites=(
                RequiredVerificationFact.CONSUMER_ERROR_RATE,
            ),
            safe_investigation_steps=("Inspect consumer error trend.",),
            unsafe_or_out_of_scope_actions=("Do not execute remediation.",),
            last_reviewed_at=date(2026, 6, 24),
            owner_role="platform_engineering",
        )


def test_source_manifest_record_requires_explicit_usage_controls() -> None:
    source = SourceManifestRecord(
        source_record_id="SRC-001",
        source_name="PostHog public postmortems",
        source_url="https://github.com/PostHog/post-mortems",
        usage_mode=SourceUsageMode.LICENSED_SOURCE,
        licence_or_usage_note="MIT licence; retain notices where applicable.",
        approved_for=("incident structure", "operational terminology"),
        transformation_rules=(
            "Do not copy narrative text into the corpus.",
            "Adapt into RelayOps with explicit provenance.",
        ),
        source_status="approved",
    )

    assert source.source_status == "approved"


def test_eval_case_rejects_duplicate_observed_fact_entries() -> None:
    with pytest.raises(ValidationError, match="observed_facts must not repeat"):
        EvalCase(
            eval_id="EVAL-003",
            split="calibration",
            input_summary="Synthetic structured intake.",
            expected_decision_state=EvidenceDecisionState.MISSING_CRITICAL_FACTS,
            acceptable_precedent_ids=("INC-001",),
            observed_facts=(
                {
                    "fact": RequiredVerificationFact.QUEUE_DEPTH,
                    "status": "confirmed",
                },
                {
                    "fact": RequiredVerificationFact.QUEUE_DEPTH,
                    "status": "unknown",
                },
            ),
            failure_label_intent=("missing_critical_incident_fact",),
            acceptance_reason="Guards a deterministic intake fact map from ambiguous duplicates.",
        )
