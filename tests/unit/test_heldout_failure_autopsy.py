from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from incident_precedent_harness.evaluation.autopsy import (
    HeldoutBaselineIntegrityError,
    build_heldout_failure_autopsy,
    write_heldout_failure_autopsy,
)
from incident_precedent_harness.retrieval import JsonDatasetRepository


@pytest.fixture()
def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _build(repository_root: Path):
    repository = JsonDatasetRepository(repository_root)
    return build_heldout_failure_autopsy(
        repository_root=repository_root,
        incidents=repository.load_incidents(),
        cases=repository.load_heldout_cases(),
    )


def test_autopsy_traces_only_the_blocked_cases(repository_root: Path) -> None:
    report = _build(repository_root)

    assert report.baseline_gate_status == "blocked"
    assert report.blocked_case_ids == ("EVAL-102", "EVAL-110")
    assert tuple(finding.eval_id for finding in report.findings) == ("EVAL-102", "EVAL-110")


def test_autopsy_identifies_contextual_pool_signal_overretention(repository_root: Path) -> None:
    report = _build(repository_root)
    finding = next(item for item in report.findings if item.eval_id == "EVAL-102")

    assert finding.diagnosis_category == "false_conflict_from_contextual_signal"
    assert "both direct pool signals were contradicted" in finding.diagnosis
    assert "Calibration-only intervention" in finding.intervention_boundary


def test_autopsy_identifies_within_family_representative_ambiguity(repository_root: Path) -> None:
    report = _build(repository_root)
    finding = next(item for item in report.findings if item.eval_id == "EVAL-110")

    assert finding.diagnosis_category == "within_family_representative_ambiguity"
    assert "lexical rank selected an unexpected representative" in finding.diagnosis
    assert "not a tie-break patch" in finding.intervention_boundary


def test_autopsy_writes_once_and_does_not_change_frozen_cases(
    repository_root: Path,
    tmp_path: Path,
) -> None:
    copied_root = tmp_path / "repository"
    shutil.copytree(repository_root / "data", copied_root / "data")
    shutil.copytree(repository_root / "evidence_vault", copied_root / "evidence_vault")
    shutil.copytree(repository_root / "docs", copied_root / "docs")

    before = {
        path.name: path.read_bytes()
        for path in (copied_root / "data" / "evals" / "heldout").glob("*.json")
    }
    repository = JsonDatasetRepository(copied_root)
    report = build_heldout_failure_autopsy(
        repository_root=copied_root,
        incidents=repository.load_incidents(),
        cases=repository.load_heldout_cases(),
    )
    json_path = copied_root / "evidence_vault" / "reports" / "autopsy.json"
    markdown_path = copied_root / "docs" / "reports" / "autopsy.md"

    write_heldout_failure_autopsy(report, json_path=json_path, markdown_path=markdown_path)

    after = {
        path.name: path.read_bytes()
        for path in (copied_root / "data" / "evals" / "heldout").glob("*.json")
    }
    assert before == after
    assert json_path.is_file()
    assert markdown_path.is_file()

    with pytest.raises(FileExistsError, match="will not be overwritten"):
        write_heldout_failure_autopsy(report, json_path=json_path, markdown_path=markdown_path)


def test_autopsy_refuses_missing_baseline(repository_root: Path, tmp_path: Path) -> None:
    copied_root = tmp_path / "repository"
    shutil.copytree(repository_root / "data", copied_root / "data")
    (copied_root / "evidence_vault" / "reports").mkdir(parents=True)
    repository = JsonDatasetRepository(copied_root)

    with pytest.raises(HeldoutBaselineIntegrityError, match="baseline is missing"):
        build_heldout_failure_autopsy(
            repository_root=copied_root,
            incidents=repository.load_incidents(),
            cases=repository.load_heldout_cases(),
        )
