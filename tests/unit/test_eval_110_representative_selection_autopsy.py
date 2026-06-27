"""Tests for the write-once EVAL-110 representative-selection autopsy."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from incident_precedent_harness.evaluation.eval_110_representative_selection_autopsy import (
    Eval110AutopsyVerdict,
    Eval110RepresentativeSelectionAutopsyError,
    build_eval_110_representative_selection_autopsy,
    write_eval_110_representative_selection_autopsy,
)
from incident_precedent_harness.retrieval import JsonDatasetRepository

ROOT = Path(__file__).resolve().parents[2]


def _build_report():
    repository = JsonDatasetRepository(ROOT)
    return build_eval_110_representative_selection_autopsy(
        repository_root=ROOT,
        incidents=repository.load_incidents(),
        cases=repository.load_heldout_cases(),
    )


def test_current_evidence_classifies_an_undocumented_within_family_rule() -> None:
    report = _build_report()

    assert report.target_eval_id == "EVAL-110"
    assert report.verdict is Eval110AutopsyVerdict.UNDOCUMENTED_CONFLICT_RULE
    assert report.expected_decision_state.value == "evidence_found_with_conflict"
    assert report.baseline_decision_state.value == "evidence_found_with_conflict"
    assert report.retained_precedent_ids == ("INC-012", "INC-003")
    assert report.omitted_required_precedent_ids == ("INC-009",)
    assert report.unexpected_retained_precedent_ids == ("INC-012",)
    assert report.promotion_parity.policy_matches_baseline is True
    assert report.promotion_parity.typed_triage_matches_expected_state is True
    assert report.promotion_parity.procedure_execution_authorized is False


def test_candidate_trace_preserves_typed_selection_evidence_without_using_it_as_authority() -> None:
    report = _build_report()
    trace_by_id = {trace.incident_id: trace for trace in report.candidate_traces}

    assert trace_by_id["INC-012"].incident_family.value == "connection_pool_exhaustion"
    assert trace_by_id["INC-012"].ranked_position == 1
    assert trace_by_id["INC-012"].retained_by_policy is True
    assert trace_by_id["INC-009"].incident_family.value == "connection_pool_exhaustion"
    assert trace_by_id["INC-009"].ranked_position == 3
    assert trace_by_id["INC-009"].expected_acceptable is True
    assert trace_by_id["INC-009"].selection_signature_present is True


def test_refuses_when_typed_triage_retained_ids_do_not_match_baseline(tmp_path: Path) -> None:
    repository = JsonDatasetRepository(ROOT)
    source = ROOT / "evidence_vault" / "reports" / "frozen-typed-triage-promotion-gate.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    target = next(item for item in payload["outcomes"] if item["eval_id"] == "EVAL-110")
    target["policy_retained_precedent_ids"] = ["INC-009", "INC-003"]
    promotion_path = tmp_path / "promotion.json"
    promotion_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        Eval110RepresentativeSelectionAutopsyError,
        match="retained precedents do not match",
    ):
        build_eval_110_representative_selection_autopsy(
            repository_root=ROOT,
            incidents=repository.load_incidents(),
            cases=repository.load_heldout_cases(),
            promotion_relative_path=promotion_path,
        )


def test_report_is_write_once(tmp_path: Path) -> None:
    report = _build_report()
    json_path = tmp_path / "evidence_vault" / "reports" / "eval-110.json"
    markdown_path = tmp_path / "docs" / "reports" / "eval-110.md"

    write_eval_110_representative_selection_autopsy(
        report,
        json_path=json_path,
        markdown_path=markdown_path,
    )

    assert json_path.is_file()
    assert markdown_path.is_file()
    assert "**UNDOCUMENTED_CONFLICT_RULE**" in markdown_path.read_text(encoding="utf-8")

    with pytest.raises(FileExistsError, match="will not be overwritten"):
        write_eval_110_representative_selection_autopsy(
            report,
            json_path=json_path,
            markdown_path=markdown_path,
        )
