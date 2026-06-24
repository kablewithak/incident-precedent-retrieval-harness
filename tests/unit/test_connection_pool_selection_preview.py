from __future__ import annotations

from pathlib import Path

import pytest

from incident_precedent_harness.decisions.connection_pool_selection_preview import (
    ConnectionPoolRepresentativePreview,
    PreviewSelectionStatus,
    load_connection_pool_profile_set,
)
from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.domain.incident_data import EvalCase
from incident_precedent_harness.retrieval import JsonDatasetRepository
from incident_precedent_harness.retrieval.models import KeywordCandidate


@pytest.fixture()
def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture()
def preview_inputs(repository_root: Path):
    repository = JsonDatasetRepository(repository_root)
    profile_set = load_connection_pool_profile_set(
        repository_root
        / "data"
        / "selection_profiles"
        / "connection-pool-representative-profiles.json"
    )
    return (
        repository.load_incidents(),
        repository.load_procedures(),
        {case.eval_id: case for case in repository.load_calibration_cases()},
        ConnectionPoolRepresentativePreview(
            policy=AntiAnchoringDecisionPolicy(),
            profile_set=profile_set,
        ),
    )


@pytest.mark.parametrize(
    ("eval_id", "expected_selected"),
    [
        ("EVAL-009", ("INC-009",)),
        ("EVAL-010", ("INC-010",)),
        ("EVAL-011", ("INC-011",)),
    ],
)
def test_preview_selects_safe_calibration_representative(
    preview_inputs,
    eval_id: str,
    expected_selected: tuple[str, ...],
) -> None:
    incidents, procedures, cases, preview = preview_inputs

    result = preview.preview(
        intake=cases[eval_id],
        ranked_candidates=(
            KeywordCandidate(incident_id="INC-012", rank=1, score=999.0),
            KeywordCandidate(incident_id="INC-011", rank=2, score=500.0),
            KeywordCandidate(incident_id="INC-010", rank=3, score=100.0),
            KeywordCandidate(incident_id="INC-009", rank=4, score=0.1),
        ),
        incidents=incidents,
        procedures=procedures,
    )

    assert result is not None
    assert result.retained_incident_ids == expected_selected
    assert {
        candidate.selection_status
        for candidate in result.candidate_previews
        if candidate.incident_id in expected_selected
    } == {PreviewSelectionStatus.SELECTED}
    assert set(result.retained_incident_ids).isdisjoint(cases[eval_id].unsafe_precedent_ids)


def test_preview_is_invariant_to_retriever_rank_and_score(preview_inputs) -> None:
    incidents, procedures, cases, preview = preview_inputs
    case = cases["EVAL-009"]
    reversed_candidates = (
        KeywordCandidate(incident_id="INC-012", rank=1, score=999.0),
        KeywordCandidate(incident_id="INC-009", rank=2, score=0.1),
    )

    result = preview.preview(
        intake=case,
        ranked_candidates=reversed_candidates,
        incidents=incidents,
        procedures=procedures,
    )

    assert result is not None
    assert result.retained_incident_ids == ("INC-009",)


def test_preview_preserves_true_tie_without_identifier_tiebreak(preview_inputs) -> None:
    incidents, procedures, cases, preview = preview_inputs
    case = EvalCase.model_validate(
        {
            "eval_id": "EVAL-098",
            "split": "calibration",
            "input_summary": "Database client-pool utilization and acquisition latency are elevated.",
            "expected_decision_state": "evidence_found",
            "acceptable_precedent_ids": ["INC-009", "INC-012"],
            "unsafe_precedent_ids": [],
            "expected_candidate_procedure_ids": [],
            "expected_missing_facts": [],
            "failure_label_intent": ["within_family_tie"],
            "acceptance_reason": "A preview tie must not fall back to rank or identifier order.",
            "observed_facts": [
                {"fact": "database_connection_pool_utilization", "status": "confirmed"},
                {"fact": "database_connection_acquire_latency", "status": "confirmed"},
                {"fact": "active_database_connections", "status": "confirmed"},
                {"fact": "migration_lock_waits", "status": "unknown"},
                {"fact": "error_rate_by_component", "status": "unknown"}
            ]
        }
    )
    candidates = (
        KeywordCandidate(incident_id="INC-012", rank=1, score=100.0),
        KeywordCandidate(incident_id="INC-009", rank=2, score=0.01),
    )

    result = preview.preview(
        intake=case,
        ranked_candidates=candidates,
        incidents=incidents,
        procedures=procedures,
    )

    assert result is not None
    assert result.retained_incident_ids == ("INC-009", "INC-012")
    assert {
        candidate.selection_status
        for candidate in result.candidate_previews
        if candidate.incident_id in result.retained_incident_ids
    } == {PreviewSelectionStatus.TIED}
