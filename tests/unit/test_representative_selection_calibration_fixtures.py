from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from incident_precedent_harness.domain.incident_enums import (
    IncidentFamily,
    OperationalSignalFamily,
)
from incident_precedent_harness.domain.selection_calibration import (
    RepresentativeSelectionCalibrationCase,
    RepresentativeSelectionExpectationState,
)
from incident_precedent_harness.evals.selection_calibration import (
    SelectionCalibrationLoadError,
    load_selection_calibration_cases,
    validate_selection_calibration_cases,
)
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository


@pytest.fixture()
def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_selection_calibration_fixtures_are_valid_and_isolated(
    repository_root: Path,
) -> None:
    cases = load_selection_calibration_cases(repository_root)

    assert tuple(case.selection_case_id for case in cases) == (
        "SEL-CAL-001",
        "SEL-CAL-002",
        "SEL-CAL-003",
        "SEL-CAL-004",
        "SEL-CAL-005",
        "SEL-CAL-006",
        "SEL-CAL-007",
        "SEL-CAL-008",
        "SEL-CAL-009",
        "SEL-CAL-010",
    )
    assert all(case.split == "selection_calibration" for case in cases)
    assert all(case.contract_version == "representative-selection-v1" for case in cases)
    assert sum(
        case.expected_outcome.state
        is RepresentativeSelectionExpectationState.SINGLE_REPRESENTATIVE
        for case in cases
    ) == 7
    assert sum(
        case.expected_outcome.state
        is RepresentativeSelectionExpectationState.EXPLICIT_TIE
        for case in cases
    ) == 3


def test_selection_calibration_candidates_have_connection_pool_schema_coverage(
    repository_root: Path,
) -> None:
    cases = load_selection_calibration_cases(repository_root)
    incidents = {
        incident.incident_id: incident
        for incident in JsonDatasetRepository(repository_root).load_incidents()
    }

    for case in cases:
        for incident_id in case.candidate_incident_ids:
            incident = incidents[incident_id]
            assert incident.incident_family is IncidentFamily.CONNECTION_POOL_EXHAUSTION
            assert incident.selection_signature is not None


def test_order_invariance_pair_is_exact_reverse_with_identical_contract(
    repository_root: Path,
) -> None:
    cases = {
        case.selection_case_id: case
        for case in load_selection_calibration_cases(repository_root)
    }
    canonical = cases["SEL-CAL-007"]
    reversed_case = cases["SEL-CAL-008"]

    assert canonical.order_invariance_group == "ORDER-INVARIANCE-001"
    assert canonical.order_variant == "canonical"
    assert reversed_case.order_variant == "reversed"
    assert reversed_case.candidate_incident_ids == tuple(
        reversed(canonical.candidate_incident_ids)
    )
    assert reversed_case.selection_intake == canonical.selection_intake
    assert reversed_case.expected_outcome == canonical.expected_outcome


def test_correlated_source_phrases_are_one_intake_signal_family(
    repository_root: Path,
) -> None:
    cases = {
        case.selection_case_id: case
        for case in load_selection_calibration_cases(repository_root)
    }
    case = cases["SEL-CAL-004"]

    assert case.selection_intake.operational_signal_families == (
        OperationalSignalFamily.CONNECTION_POOL_PRESSURE,
    )
    assert case.expected_outcome.state is RepresentativeSelectionExpectationState.EXPLICIT_TIE


def test_fixture_model_rejects_rank_and_score_fields() -> None:
    payload = {
        "selection_case_id": "SEL-CAL-099",
        "split": "selection_calibration",
        "contract_version": "representative-selection-v1",
        "selection_intake": {
            "operational_signal_families": ["connection_pool_pressure"],
            "contradicted_signal_families": [],
        },
        "candidate_incident_ids": ["INC-009", "INC-012"],
        "expected_outcome": {
            "state": "explicit_tie",
            "representative_incident_ids": ["INC-009", "INC-012"],
        },
        "retriever_score": 0.99,
        "failure_label_intent": ["forbidden_rank_input"],
        "acceptance_reason": "Rank and score are not permitted calibration inputs.",
    }

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RepresentativeSelectionCalibrationCase.model_validate(payload)


def test_validation_fails_for_policy_compatible_candidate_without_signature(
    repository_root: Path,
) -> None:
    cases = load_selection_calibration_cases(repository_root)
    incidents = JsonDatasetRepository(repository_root).load_incidents()
    broken_incidents = tuple(
        incident.model_copy(update={"selection_signature": None})
        if incident.incident_id == "INC-009"
        else incident
        for incident in incidents
    )

    with pytest.raises(SelectionCalibrationLoadError, match="lacks selection_signature"):
        validate_selection_calibration_cases(cases=cases, incidents=broken_incidents)
