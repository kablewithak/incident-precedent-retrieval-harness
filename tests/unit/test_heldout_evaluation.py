"""Tests for write-once held-out evaluation and its strict promotion gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.evaluation.heldout import (
    HeldoutEvaluationReport,
    HeldoutManifestIntegrityError,
    run_frozen_heldout_evaluation,
    verify_heldout_freeze,
    write_heldout_report,
)
from incident_precedent_harness.retrieval import JsonDatasetRepository, KeywordRetriever

ROOT = Path(__file__).resolve().parents[2]


def _current_report():
    repository = JsonDatasetRepository(ROOT)
    incidents = repository.load_incidents()
    procedures = repository.load_procedures()
    cases = repository.load_heldout_cases()
    return run_frozen_heldout_evaluation(
        repository_root=ROOT,
        retriever=KeywordRetriever(incidents),
        policy=AntiAnchoringDecisionPolicy(),
        incidents=incidents,
        procedures=procedures,
        cases=cases,
        top_k=5,
    )


def test_freeze_verification_records_manifest_identity() -> None:
    verification = verify_heldout_freeze(ROOT)

    assert verification.verified is True
    assert verification.scope == "heldout_tranche_01"
    assert verification.case_count == 12
    assert verification.verified_case_ids[0] == "EVAL-101"
    assert verification.verified_case_ids[-1] == "EVAL-112"


def test_freeze_verification_rejects_hash_mismatch(tmp_path: Path) -> None:
    heldout = tmp_path / "data" / "evals" / "heldout"
    heldout.mkdir(parents=True)
    case_path = heldout / "EVAL-101.json"
    case_path.write_text('{"changed": true}\n', encoding="utf-8")
    manifest = {
        "freeze_schema_version": "1.0",
        "freeze_status": "frozen",
        "frozen_on": "2026-06-24",
        "scope": "test_tranche",
        "case_ids": ["EVAL-101"],
        "sha256_by_filename": {
            "EVAL-101.json": hashlib.sha256(b'{"original": true}\n').hexdigest()
        },
        "change_policy": "test only",
    }
    (heldout / "HELDOUT_FREEZE_MANIFEST.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    with pytest.raises(HeldoutManifestIntegrityError, match="hash mismatch"):
        verify_heldout_freeze(tmp_path)


def test_committed_keyword_policy_baseline_remains_blocked_evidence() -> None:
    """Historical baseline expectations must read the immutable artifact, not current policy."""
    baseline_path = ROOT / "evidence_vault" / "reports" / "heldout-tranche-01-keyword-policy.json"
    report = HeldoutEvaluationReport.model_validate_json(baseline_path.read_text(encoding="utf-8"))

    assert report.freeze_verification.verified is True
    assert report.metrics.scored_case_count == 12
    assert report.metrics.decision_state_accuracy == 0.9167
    assert report.metrics.case_contract_pass_rate == 0.8333
    assert report.metrics.acceptable_precedent_coverage == 0.8571
    assert report.metrics.blocked_case_ids == ("EVAL-102", "EVAL-110")
    assert report.promotion_gate.status == "blocked"


def test_heldout_report_is_write_once(tmp_path: Path) -> None:
    report = _current_report()
    json_path = tmp_path / "evidence_vault" / "reports" / "heldout.json"
    markdown_path = tmp_path / "docs" / "reports" / "heldout.md"

    write_heldout_report(report, json_path=json_path, markdown_path=markdown_path)

    assert json_path.is_file()
    assert markdown_path.is_file()
    assert "**Status: BLOCKED**" in markdown_path.read_text(encoding="utf-8")

    with pytest.raises(FileExistsError, match="will not be overwritten"):
        write_heldout_report(report, json_path=json_path, markdown_path=markdown_path)
