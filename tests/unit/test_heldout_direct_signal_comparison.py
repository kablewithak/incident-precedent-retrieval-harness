"""Tests for the write-once ADR-0008 held-out comparison boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.evaluation.comparison import (
    HeldoutComparisonIntegrityError,
    build_heldout_direct_signal_comparison,
    write_heldout_direct_signal_comparison,
)
from incident_precedent_harness.retrieval import JsonDatasetRepository, KeywordRetriever

ROOT = Path(__file__).resolve().parents[2]


def _comparison_report():
    repository = JsonDatasetRepository(ROOT)
    incidents = repository.load_incidents()
    procedures = repository.load_procedures()
    cases = repository.load_heldout_cases()
    return build_heldout_direct_signal_comparison(
        repository_root=ROOT,
        retriever=KeywordRetriever(incidents),
        policy=AntiAnchoringDecisionPolicy(),
        incidents=incidents,
        procedures=procedures,
        cases=cases,
        top_k=5,
    )


def test_direct_signal_comparison_improves_eval_102_without_regression() -> None:
    report = _comparison_report()
    deltas = {delta.eval_id: delta for delta in report.outcome_deltas}

    assert report.baseline_evidence.promotion_gate_status == "blocked"
    assert report.comparison_run.promotion_gate.status == "blocked"
    assert report.comparison_summary.conclusion == "improved_but_blocked"
    assert report.comparison_summary.improved_case_ids == ("EVAL-102",)
    assert report.comparison_summary.regressed_case_ids == ()
    assert report.comparison_run.metrics.blocked_case_ids == ("EVAL-110",)
    assert report.comparison_run.metrics.decision_state_accuracy == 1.0
    assert report.comparison_run.metrics.case_contract_pass_rate == 0.9167

    eval_102 = deltas["EVAL-102"]
    assert eval_102.change_class == "improved"
    assert eval_102.comparison_decision_state.value == "evidence_found"
    assert eval_102.comparison_retained_precedent_ids == ("INC-005",)
    assert eval_102.comparison_candidate_procedure_ids == ("RB-002",)

    eval_110 = deltas["EVAL-110"]
    assert eval_110.change_class == "unchanged"
    assert eval_110.comparison_case_contract_passed is False


def test_comparison_writer_creates_report_and_handover_once(tmp_path: Path) -> None:
    report = _comparison_report()
    json_path = tmp_path / "evidence_vault" / "reports" / "comparison.json"
    markdown_path = tmp_path / "docs" / "reports" / "comparison.md"
    handover_path = tmp_path / "docs" / "handover" / "handover.md"

    write_heldout_direct_signal_comparison(
        report,
        json_path=json_path,
        markdown_path=markdown_path,
        handover_path=handover_path,
    )

    assert json_path.is_file()
    assert markdown_path.is_file()
    assert handover_path.is_file()
    assert "IMPROVED BUT BLOCKED" in markdown_path.read_text(encoding="utf-8")
    handover = handover_path.read_text(encoding="utf-8")
    assert "Handover 002" in handover
    assert "EVAL-110" in handover

    with pytest.raises(FileExistsError, match="will not be overwritten"):
        write_heldout_direct_signal_comparison(
            report,
            json_path=json_path,
            markdown_path=markdown_path,
            handover_path=handover_path,
        )


def test_comparison_requires_committed_baseline_artifact(tmp_path: Path) -> None:
    with pytest.raises(HeldoutComparisonIntegrityError, match="requires the committed baseline"):
        build_heldout_direct_signal_comparison(
            repository_root=tmp_path,
            retriever=KeywordRetriever(JsonDatasetRepository(ROOT).load_incidents()),
            policy=AntiAnchoringDecisionPolicy(),
            incidents=(),
            procedures=(),
            cases=(),
            top_k=5,
        )
