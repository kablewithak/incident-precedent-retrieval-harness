"""Validation for Batch 01 controlled-variant assets."""

from __future__ import annotations

import json
from pathlib import Path

from incident_precedent_harness.domain.incident_data import (
    CandidateInvestigationProcedure,
    EvalCase,
    HistoricalIncidentCard,
)
from incident_precedent_harness.domain.incident_enums import (
    IncidentFamily,
    RecordOrigin,
)

ROOT = Path(__file__).resolve().parents[2]
INCIDENTS = ROOT / "data" / "incidents"
PROCEDURES = ROOT / "data" / "procedures"
CALIBRATION = ROOT / "data" / "evals" / "calibration"

BATCH_01_INCIDENT_IDS = ("INC-001", "INC-002", "INC-003", "INC-004")
BATCH_01_EVAL_IDS = ("EVAL-001", "EVAL-002", "EVAL-003", "EVAL-004")


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_batch_01_incidents_validate_and_remain_controlled_variants() -> None:
    cards = [
        HistoricalIncidentCard.model_validate(load_json(INCIDENTS / f"{incident_id}.json"))
        for incident_id in BATCH_01_INCIDENT_IDS
    ]

    assert [card.incident_id for card in cards] == list(BATCH_01_INCIDENT_IDS)
    assert {card.record_origin for card in cards} == {RecordOrigin.CONTROLLED_VARIANT}
    assert {card.incident_family for card in cards} == {
        IncidentFamily.QUEUE_BACKLOG_CONSUMER_FAILURE
    }
    assert all(card.provenance is None for card in cards)
    assert all(card.safe_procedure_ids == ("RB-001",) for card in cards)


def test_batch_01_procedure_is_a_bounded_investigation_artifact() -> None:
    procedure = CandidateInvestigationProcedure.model_validate(
        load_json(PROCEDURES / "RB-001.json")
    )

    assert procedure.procedure_id == "RB-001"
    assert procedure.status.value == "current"
    assert IncidentFamily.QUEUE_BACKLOG_CONSUMER_FAILURE in procedure.applicable_incident_families
    assert all("restart" not in step.lower() for step in procedure.safe_investigation_steps)


def test_batch_01_calibration_cases_validate_against_known_ids() -> None:
    cases = [
        EvalCase.model_validate(load_json(CALIBRATION / f"{eval_id}.json"))
        for eval_id in BATCH_01_EVAL_IDS
    ]

    assert [case.eval_id for case in cases] == list(BATCH_01_EVAL_IDS)
    assert all(case.split == "calibration" for case in cases)
    assert cases[0].expected_candidate_procedure_ids == ("RB-001",)
    assert cases[2].acceptable_precedent_ids == ()
    assert cases[2].expected_candidate_procedure_ids == ()
    assert cases[3].expected_decision_state.value == "provider_degraded"
