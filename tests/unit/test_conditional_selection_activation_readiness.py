"""Tests for the write-once conditional-selection readiness evidence."""

from __future__ import annotations

from pathlib import Path

import pytest

from incident_precedent_harness.evaluation.conditional_selection_activation_readiness import (
    JSON_REPORT_RELATIVE_PATH,
    MARKDOWN_REPORT_RELATIVE_PATH,
    ActivationReadinessDecision,
    run_conditional_selection_activation_readiness,
    write_conditional_selection_activation_readiness_report,
)

ROOT = Path(__file__).resolve().parents[2]


def test_readiness_controls_preserve_policy_authority() -> None:
    report = run_conditional_selection_activation_readiness(repository_root=ROOT)

    assert report.decision is (
        ActivationReadinessDecision.IMPLEMENTATION_VALIDATED_ACTIVATION_BLOCKED
    )
    assert report.fixed_case_count == 3
    assert report.contract_pass_rate == 1.0
    assert all(outcome.contract_matches for outcome in report.outcomes)


def test_readiness_report_is_write_once(tmp_path: Path) -> None:
    report = run_conditional_selection_activation_readiness(repository_root=ROOT)
    json_path = tmp_path / JSON_REPORT_RELATIVE_PATH
    markdown_path = tmp_path / MARKDOWN_REPORT_RELATIVE_PATH

    write_conditional_selection_activation_readiness_report(
        report=report,
        json_path=json_path,
        markdown_path=markdown_path,
    )

    assert json_path.is_file()
    assert markdown_path.is_file()

    with pytest.raises(FileExistsError):
        write_conditional_selection_activation_readiness_report(
            report=report,
            json_path=json_path,
            markdown_path=markdown_path,
        )
