"""Validation for Batch 03 connection-pool and conflict-case assets."""

from __future__ import annotations

import json
from pathlib import Path

from incident_precedent_harness.domain.incident_data import (
    CandidateInvestigationProcedure,
    EvalCase,
    HistoricalIncidentCard,
)
from incident_precedent_harness.domain.incident_enums import (
    EvidenceDecisionState,
    IncidentFamily,
    RecordOrigin,
    RequiredVerificationFact,
)

ROOT = Path(__file__).resolve().parents[2]
INCIDENTS = ROOT / "data" / "incidents"
PROCEDURES = ROOT / "data" / "procedures"
CALIBRATION = ROOT / "data" / "evals" / "calibration"

BATCH_03_INCIDENT_IDS = ("INC-009", "INC-010", "INC-011", "INC-012")
BATCH_03_EVAL_IDS = ("EVAL-009", "EVAL-010", "EVAL-011", "EVAL-012")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_batch_03_incidents_validate_as_connection_pool_controlled_variants() -> None:
    cards = [
        HistoricalIncidentCard.model_validate(load_json(INCIDENTS / f"{incident_id}.json"))
        for incident_id in BATCH_03_INCIDENT_IDS
    ]

    assert [card.incident_id for card in cards] == list(BATCH_03_INCIDENT_IDS)
    assert {card.record_origin for card in cards} == {RecordOrigin.CONTROLLED_VARIANT}
    assert {card.incident_family for card in cards} == {
        IncidentFamily.CONNECTION_POOL_EXHAUSTION
    }
    assert all(card.provenance is None for card in cards)
    assert all(card.safe_procedure_ids == ("RB-003",) for card in cards)
    assert all("RB-002" in card.unsafe_procedure_ids for card in cards)


def test_batch_03_procedure_requires_pool_and_lock_disambiguation() -> None:
    procedure = CandidateInvestigationProcedure.model_validate(
        load_json(PROCEDURES / "RB-003.json")
    )

    assert procedure.procedure_id == "RB-003"
    assert procedure.status.value == "current"
    assert IncidentFamily.CONNECTION_POOL_EXHAUSTION in procedure.applicable_incident_families
    assert IncidentFamily.DATABASE_MIGRATION_LOCK_CONTENTION in procedure.not_applicable_when
    assert RequiredVerificationFact.DATABASE_CONNECTION_POOL_UTILIZATION in (
        procedure.verification_prerequisites
    )
    assert RequiredVerificationFact.MIGRATION_LOCK_WAITS in procedure.verification_prerequisites
    assert all("increase" not in step.lower() for step in procedure.safe_investigation_steps)


def test_batch_03_calibration_contains_missing_fact_and_no_preference_conflict_cases() -> None:
    cases = [
        EvalCase.model_validate(load_json(CALIBRATION / f"{eval_id}.json"))
        for eval_id in BATCH_03_EVAL_IDS
    ]

    assert [case.eval_id for case in cases] == list(BATCH_03_EVAL_IDS)
    assert all(case.split == "calibration" for case in cases)

    positive = cases[0]
    assert positive.expected_candidate_procedure_ids == ("RB-003",)
    assert set(positive.unsafe_precedent_ids) == {"INC-005", "INC-008"}

    missing_facts = cases[1]
    assert missing_facts.expected_decision_state is EvidenceDecisionState.MISSING_CRITICAL_FACTS
    assert missing_facts.expected_candidate_procedure_ids == ()
    assert RequiredVerificationFact.DATABASE_CONNECTION_ACQUIRE_LATENCY in (
        missing_facts.expected_missing_facts
    )

    conflict = cases[2]
    assert conflict.expected_decision_state is EvidenceDecisionState.EVIDENCE_FOUND_WITH_CONFLICT
    assert set(conflict.acceptable_precedent_ids) == {"INC-003", "INC-011"}
    assert conflict.expected_candidate_procedure_ids == ()
    assert "conflicting_precedent" in conflict.failure_label_intent

    abstention = cases[3]
    assert abstention.expected_decision_state is EvidenceDecisionState.INSUFFICIENT_PRECEDENT
    assert abstention.expected_candidate_procedure_ids == ()
