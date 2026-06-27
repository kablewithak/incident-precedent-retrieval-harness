"""Tests for the calibration-only representative-selection readiness gate."""

from __future__ import annotations

from pathlib import Path

import pytest

from incident_precedent_harness.evaluation.selection_calibration_readiness import (
    SelectionReadinessDecision,
    run_selection_calibration_readiness_gate,
    write_selection_calibration_readiness_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _current_report():
    return run_selection_calibration_readiness_gate(repository_root=ROOT)


def test_current_calibration_contract_passes_but_activation_remains_blocked() -> None:
    report = _current_report()

    assert report.decision is SelectionReadinessDecision.CALIBRATION_PASSED_ACTIVATION_BLOCKED
    assert report.metrics.selection_calibration_case_count == 10
    assert report.metrics.selection_contract_pass_rate == 1.0
    assert report.metrics.order_invariance_group_count == 1
    assert report.metrics.order_invariance_pass_rate == 1.0
    assert report.metrics.failed_case_ids == ()


def test_readiness_gate_preserves_no_heldout_retrieval_or_policy_authority() -> None:
    report = _current_report()

    assert report.metrics.heldout_loaded is False
    assert report.metrics.retrieval_loaded is False
    assert report.metrics.active_policy_changed is False
    assert report.metrics.selector_activation_claim is False
    assert any("independent held-out evidence" in blocker for blocker in report.activation_blockers)


def test_order_invariance_variants_have_identical_actual_selection() -> None:
    report = _current_report()
    outcomes = {outcome.selection_case_id: outcome for outcome in report.outcomes}

    canonical = outcomes["SEL-CAL-007"]
    reversed_case = outcomes["SEL-CAL-008"]

    assert canonical.order_invariance_group == "ORDER-INVARIANCE-001"
    assert reversed_case.order_invariance_group == "ORDER-INVARIANCE-001"
    assert canonical.actual_state == reversed_case.actual_state
    assert (
        canonical.actual_representative_incident_ids
        == reversed_case.actual_representative_incident_ids
        == ("INC-009",)
    )


def test_readiness_report_is_write_once(tmp_path: Path) -> None:
    report = _current_report()
    json_path = tmp_path / "evidence_vault" / "reports" / "selection-readiness.json"
    markdown_path = tmp_path / "docs" / "reports" / "selection-readiness.md"

    write_selection_calibration_readiness_report(
        report,
        json_path=json_path,
        markdown_path=markdown_path,
    )

    assert json_path.is_file()
    assert markdown_path.is_file()
    assert "CALIBRATION_PASSED_ACTIVATION_BLOCKED" in markdown_path.read_text(
        encoding="utf-8"
    )

    with pytest.raises(FileExistsError, match="will not be overwritten"):
        write_selection_calibration_readiness_report(
            report,
            json_path=json_path,
            markdown_path=markdown_path,
        )
