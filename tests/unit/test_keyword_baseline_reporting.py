"""Tests for scoped, calibration-only baseline reporting."""

from __future__ import annotations

import json
from pathlib import Path

from incident_precedent_harness.retrieval import JsonDatasetRepository, KeywordRetriever
from incident_precedent_harness.retrieval.reporting import run_keyword_baseline, write_report

ROOT = Path(__file__).resolve().parents[2]


def test_keyword_baseline_report_is_calibration_only_and_complete() -> None:
    repository = JsonDatasetRepository(ROOT)
    report = run_keyword_baseline(
        retriever=KeywordRetriever(repository.load_incidents()),
        cases=repository.load_calibration_cases(),
        top_k=5,
    )

    assert report.corpus_incident_count == 12
    assert report.calibration_case_count == 12
    assert len(report.outcomes) == 12
    assert report.metrics.scored_case_count == 12
    assert report.metrics.cases_with_acceptable_precedent == 8
    assert report.metrics.safety_evaluable_case_count == 11
    assert report.metrics.false_operational_match_count >= 1
    assert any(
        "lexical_candidate_returned_without_abstention_policy" in outcome.failure_labels
        for outcome in report.outcomes
    )
    assert any("Lexical ranking does not assign" in limit for limit in report.known_limits)


def test_keyword_baseline_report_writes_json_and_markdown(tmp_path: Path) -> None:
    repository = JsonDatasetRepository(ROOT)
    report = run_keyword_baseline(
        retriever=KeywordRetriever(repository.load_incidents()),
        cases=repository.load_calibration_cases(),
    )
    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"

    write_report(report, json_path=json_path, markdown_path=markdown_path)

    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    rendered = markdown_path.read_text(encoding="utf-8")
    assert parsed["report_kind"] == "keyword_baseline_calibration"
    assert "# Keyword Baseline Calibration Report" in rendered
    assert "## Known limits" in rendered
