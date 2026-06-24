from __future__ import annotations

import json
from pathlib import Path

from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.decisions.reporting import run_policy_calibration, write_report
from incident_precedent_harness.retrieval import JsonDatasetRepository, KeywordRetriever


def test_policy_calibration_report_scores_current_fixtures(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    repository = JsonDatasetRepository(repository_root)
    incidents = repository.load_incidents()
    procedures = repository.load_procedures()
    cases = repository.load_calibration_cases()

    report = run_policy_calibration(
        retriever=KeywordRetriever(incidents),
        policy=AntiAnchoringDecisionPolicy(),
        incidents=incidents,
        procedures=procedures,
        cases=cases,
    )

    assert report.metrics.decision_state_accuracy == 1.0
    assert report.metrics.false_operational_match_count == 0
    assert report.metrics.unsafe_procedure_surfacing_count == 0
    assert report.metrics.no_precedent_abstention_accuracy == 1.0
    assert report.metrics.conflict_state_accuracy == 1.0
    assert report.metrics.missing_fact_exact_match_rate == 1.0

    json_path = tmp_path / "policy.json"
    markdown_path = tmp_path / "policy.md"
    write_report(report, json_path=json_path, markdown_path=markdown_path)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["metrics"]["false_operational_match_count"] == 0
    assert "Anti-Anchoring Policy Calibration Report" in markdown_path.read_text(encoding="utf-8")
