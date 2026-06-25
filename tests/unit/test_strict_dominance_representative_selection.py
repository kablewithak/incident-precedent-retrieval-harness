from __future__ import annotations

from pathlib import Path

import pytest

from incident_precedent_harness.decisions.strict_dominance_selection import (
    RepresentativeSelectionState,
    SelectionInputError,
    StrictDominanceRepresentativeSelector,
)
from incident_precedent_harness.domain.incident_data import RepresentativeSelectionIntake
from incident_precedent_harness.evals.selection_calibration import (
    load_selection_calibration_cases,
)
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository


@pytest.fixture()
def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture()
def selector() -> StrictDominanceRepresentativeSelector:
    return StrictDominanceRepresentativeSelector()


@pytest.fixture()
def selection_cases(repository_root: Path):
    return {
        case.selection_case_id: case
        for case in load_selection_calibration_cases(repository_root)
    }


@pytest.fixture()
def incidents(repository_root: Path):
    return JsonDatasetRepository(repository_root).load_incidents()


@pytest.mark.parametrize(
    "selection_case_id",
    (
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
    ),
)
def test_strict_dominance_selector_matches_fixed_calibration_contract(
    selector: StrictDominanceRepresentativeSelector,
    selection_cases,
    incidents,
    selection_case_id: str,
) -> None:
    case = selection_cases[selection_case_id]

    result = selector.select(
        intake=case.selection_intake,
        candidate_incident_ids=case.candidate_incident_ids,
        incidents=incidents,
    )

    assert result.selection_state.value == case.expected_outcome.state.value
    assert result.representative_incident_ids == case.expected_outcome.representative_incident_ids


def test_order_invariance_pair_has_identical_result(
    selector: StrictDominanceRepresentativeSelector,
    selection_cases,
    incidents,
) -> None:
    canonical = selection_cases["SEL-CAL-007"]
    reversed_case = selection_cases["SEL-CAL-008"]

    canonical_result = selector.select(
        intake=canonical.selection_intake,
        candidate_incident_ids=canonical.candidate_incident_ids,
        incidents=incidents,
    )
    reversed_result = selector.select(
        intake=reversed_case.selection_intake,
        candidate_incident_ids=reversed_case.candidate_incident_ids,
        incidents=incidents,
    )

    assert canonical_result.selection_state is RepresentativeSelectionState.SINGLE_REPRESENTATIVE
    assert canonical_result.representative_incident_ids == ("INC-009",)
    assert reversed_result == canonical_result


def test_explicit_tie_contains_only_non_dominated_candidates(
    selector: StrictDominanceRepresentativeSelector,
    selection_cases,
    incidents,
) -> None:
    case = selection_cases["SEL-CAL-005"]

    result = selector.select(
        intake=case.selection_intake,
        candidate_incident_ids=case.candidate_incident_ids,
        incidents=incidents,
    )

    assert result.selection_state is RepresentativeSelectionState.EXPLICIT_TIE
    assert result.representative_incident_ids == ("INC-009", "INC-010")
    assert all(
        not evidence.dominated_by_incident_ids
        for evidence in result.candidate_evidence
        if evidence.incident_id in result.representative_incident_ids
    )


def test_contradicted_signal_can_remove_a_candidate_from_non_dominated_set(
    selector: StrictDominanceRepresentativeSelector,
    selection_cases,
    incidents,
) -> None:
    case = selection_cases["SEL-CAL-010"]

    result = selector.select(
        intake=case.selection_intake,
        candidate_incident_ids=case.candidate_incident_ids,
        incidents=incidents,
    )

    assert result.selection_state is RepresentativeSelectionState.SINGLE_REPRESENTATIVE
    assert result.representative_incident_ids == ("INC-012",)
    evidence_by_id = {evidence.incident_id: evidence for evidence in result.candidate_evidence}
    assert evidence_by_id["INC-009"].contradicted_signal_families
    assert evidence_by_id["INC-009"].dominated_by_incident_ids == ("INC-012",)


def test_selector_rejects_non_connection_pool_candidate(
    selector: StrictDominanceRepresentativeSelector,
    incidents,
) -> None:
    with pytest.raises(SelectionInputError, match="connection_pool_exhaustion"):
        selector.select(
            intake=RepresentativeSelectionIntake(),
            candidate_incident_ids=("INC-001", "INC-009"),
            incidents=incidents,
        )
