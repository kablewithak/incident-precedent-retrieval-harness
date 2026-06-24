"""Validation for Batch 02 migration-lock and false-match assets."""

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
)

ROOT = Path(__file__).resolve().parents[2]
INCIDENTS = ROOT / "data" / "incidents"
PROCEDURES = ROOT / "data" / "procedures"
CALIBRATION = ROOT / "data" / "evals" / "calibration"

BATCH_02_INCIDENT_IDS = ("INC-005", "INC-006", "INC-007", "INC-008")
BATCH_02_EVAL_IDS = ("EVAL-005", "EVAL-006", "EVAL-007", "EVAL-008")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_batch_02_incidents_validate_as_migration_lock_controlled_variants() -> None:
    cards = [
        HistoricalIncidentCard.model_validate(load_json(INCIDENTS / f"{incident_id}.json"))
        for incident_id in BATCH_02_INCIDENT_IDS
    ]

    assert [card.incident_id for card in cards] == list(BATCH_02_INCIDENT_IDS)
    assert {card.record_origin for card in cards} == {RecordOrigin.CONTROLLED_VARIANT}
    assert {card.incident_family for card in cards} == {
        IncidentFamily.DATABASE_MIGRATION_LOCK_CONTENTION
    }
    assert all(card.provenance is None for card in cards)
    assert all("RB-002" in card.safe_procedure_ids for card in cards)
    assert all("RB-001" not in card.safe_procedure_ids for card in cards)


def test_batch_02_procedure_has_a_hard_non_applicability_boundary() -> None:
    procedure = CandidateInvestigationProcedure.model_validate(
        load_json(PROCEDURES / "RB-002.json")
    )

    assert procedure.procedure_id == "RB-002"
    assert procedure.status.value == "current"
    assert IncidentFamily.DATABASE_MIGRATION_LOCK_CONTENTION in procedure.applicable_incident_families
    assert IncidentFamily.QUEUE_BACKLOG_CONSUMER_FAILURE in procedure.not_applicable_when
    assert all("terminate" not in step.lower() for step in procedure.safe_investigation_steps)


def test_batch_02_calibration_contains_the_first_false_operational_match_case() -> None:
    cases = [
        EvalCase.model_validate(load_json(CALIBRATION / f"{eval_id}.json"))
        for eval_id in BATCH_02_EVAL_IDS
    ]

    assert [case.eval_id for case in cases] == list(BATCH_02_EVAL_IDS)
    assert all(case.split == "calibration" for case in cases)

    false_match_case = cases[0]
    assert false_match_case.expected_decision_state is EvidenceDecisionState.EVIDENCE_FOUND
    assert false_match_case.expected_candidate_procedure_ids == ("RB-002",)
    assert set(false_match_case.unsafe_precedent_ids) == {"INC-003", "INC-004"}
    assert "false_operational_match" in false_match_case.failure_label_intent

    reverse_false_match_case = cases[2]
    assert reverse_false_match_case.expected_candidate_procedure_ids == ("RB-001",)
    assert "INC-005" in reverse_false_match_case.unsafe_precedent_ids

    abstention_case = cases[3]
    assert abstention_case.expected_decision_state is EvidenceDecisionState.INSUFFICIENT_PRECEDENT
    assert abstention_case.expected_candidate_procedure_ids == ()
