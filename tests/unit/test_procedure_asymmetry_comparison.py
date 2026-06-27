from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from incident_precedent_harness.decisions.strict_dominance_selection import (
    RepresentativeSelectionResult,
    RepresentativeSelectionState,
    StrictDominanceRepresentativeSelector,
)
from incident_precedent_harness.evaluation.procedure_asymmetry_comparison import (
    FIXTURE_RELATIVE_PATH,
    IMPORT_RECEIPT_RELATIVE_PATH,
    ProcedureAsymmetryComparisonError,
    ProcedureAsymmetryComparisonDecision,
    run_procedure_asymmetry_fixture_comparison,
    write_procedure_asymmetry_fixture_comparison_report,
)


@pytest.fixture()
def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _copy_imported_fixture(repository_root: Path, target_root: Path) -> Path:
    fixture_source = repository_root / FIXTURE_RELATIVE_PATH
    fixture_target = target_root / FIXTURE_RELATIVE_PATH
    fixture_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(fixture_source, fixture_target)

    receipt_source = repository_root / IMPORT_RECEIPT_RELATIVE_PATH
    receipt_target = target_root / IMPORT_RECEIPT_RELATIVE_PATH
    receipt_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(receipt_source, receipt_target)
    return target_root


def test_current_imported_fixture_passes_comparison_and_remains_activation_blocked(
    repository_root: Path,
) -> None:
    report = run_procedure_asymmetry_fixture_comparison(
        repository_root=repository_root,
    )

    assert (
        report.comparison_decision
        is ProcedureAsymmetryComparisonDecision.COMPARISON_PASSED_ACTIVATION_BLOCKED
    )
    assert report.metrics.imported_fixture_asset_count == 15
    assert report.metrics.runtime_case_count == 3
    assert report.metrics.expected_outcome_count == 3
    assert report.metrics.contract_pass_rate == 1.0
    assert report.metrics.order_invariance_passed is True
    assert report.metrics.procedure_asymmetry_present is True
    assert report.metrics.procedure_neutrality_passed is True
    assert report.metrics.active_policy_changed is False
    assert report.metrics.retrieval_loaded is False
    assert report.metrics.heldout_loaded is False
    assert report.metrics.selector_activation_claim is False
    assert {
        outcome.case_id: outcome.actual_representative_incident_ids
        for outcome in report.outcomes
    } == {
        "PAF-T02-001": ("INC-014",),
        "PAF-T02-002": ("INC-014",),
        "PAF-T02-003": ("INC-014",),
    }


def test_refuses_when_imported_fixture_asset_hash_drifted(
    repository_root: Path,
    tmp_path: Path,
) -> None:
    target_root = _copy_imported_fixture(repository_root, tmp_path / "repository")
    path = (
        target_root
        / FIXTURE_RELATIVE_PATH
        / "inputs"
        / "cases"
        / "PAF-T02-001.input.json"
    )
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(
        ProcedureAsymmetryComparisonError,
        match="SHA-256 mismatch",
    ):
        run_procedure_asymmetry_fixture_comparison(repository_root=target_root)


class _OrderLeakingSelector:
    def __init__(self) -> None:
        self._selector = StrictDominanceRepresentativeSelector()

    def select(self, *, intake, candidate_incident_ids, incidents):
        baseline = self._selector.select(
            intake=intake,
            candidate_incident_ids=candidate_incident_ids,
            incidents=incidents,
        )
        return RepresentativeSelectionResult(
            selection_state=RepresentativeSelectionState.SINGLE_REPRESENTATIVE,
            representative_incident_ids=(candidate_incident_ids[0],),
            candidate_evidence=baseline.candidate_evidence,
            selection_reason="Test-only order leak.",
        )


def test_blocks_when_candidate_order_changes_selection(
    repository_root: Path,
) -> None:
    report = run_procedure_asymmetry_fixture_comparison(
        repository_root=repository_root,
        selector=_OrderLeakingSelector(),
    )

    assert (
        report.comparison_decision
        is ProcedureAsymmetryComparisonDecision.COMPARISON_BLOCKED
    )
    assert report.metrics.order_invariance_passed is False
    assert report.metrics.contract_pass_rate < 1.0
    assert "PAF-T02-001" in report.metrics.failed_case_ids


class _ProcedureLeakingSelector:
    def __init__(self) -> None:
        self._selector = StrictDominanceRepresentativeSelector()

    def select(self, *, intake, candidate_incident_ids, incidents):
        safe_candidates = [
            card.incident_id
            for card in incidents
            if card.incident_id in candidate_incident_ids and card.safe_procedure_ids
        ]
        if safe_candidates:
            baseline = self._selector.select(
                intake=intake,
                candidate_incident_ids=candidate_incident_ids,
                incidents=incidents,
            )
            return RepresentativeSelectionResult(
                selection_state=RepresentativeSelectionState.SINGLE_REPRESENTATIVE,
                representative_incident_ids=(safe_candidates[0],),
                candidate_evidence=baseline.candidate_evidence,
                selection_reason="Test-only procedure metadata leak.",
            )
        return self._selector.select(
            intake=intake,
            candidate_incident_ids=candidate_incident_ids,
            incidents=incidents,
        )


def test_blocks_when_procedure_posture_changes_selection(
    repository_root: Path,
) -> None:
    report = run_procedure_asymmetry_fixture_comparison(
        repository_root=repository_root,
        selector=_ProcedureLeakingSelector(),
    )

    assert (
        report.comparison_decision
        is ProcedureAsymmetryComparisonDecision.COMPARISON_BLOCKED
    )
    assert report.metrics.procedure_asymmetry_present is True
    assert report.metrics.procedure_neutrality_passed is False
    assert "PAF-T02-001" in report.metrics.failed_case_ids


def test_comparison_evidence_is_write_once(
    repository_root: Path,
    tmp_path: Path,
) -> None:
    report = run_procedure_asymmetry_fixture_comparison(
        repository_root=repository_root,
    )
    json_path = tmp_path / "comparison.json"
    markdown_path = tmp_path / "comparison.md"

    write_procedure_asymmetry_fixture_comparison_report(
        report=report,
        json_path=json_path,
        markdown_path=markdown_path,
    )

    with pytest.raises(FileExistsError, match="will not be overwritten"):
        write_procedure_asymmetry_fixture_comparison_report(
            report=report,
            json_path=json_path,
            markdown_path=markdown_path,
        )
