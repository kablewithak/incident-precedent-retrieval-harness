"""Tests for strict, deterministic loading of dataset assets."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from incident_precedent_harness.retrieval.repository import DatasetLoadError, JsonDatasetRepository

ROOT = Path(__file__).resolve().parents[2]


def test_repository_loads_current_calibration_assets_in_stable_id_order() -> None:
    repository = JsonDatasetRepository(ROOT)

    incidents = repository.load_incidents()
    cases = repository.load_calibration_cases()

    assert [incident.incident_id for incident in incidents] == [
        "INC-001",
        "INC-002",
        "INC-003",
        "INC-004",
        "INC-005",
        "INC-006",
        "INC-007",
        "INC-008",
        "INC-009",
        "INC-010",
        "INC-011",
        "INC-012",
    ]
    assert [case.eval_id for case in cases] == [f"EVAL-{number:03}" for number in range(1, 13)]


def test_repository_rejects_invalid_json(tmp_path: Path) -> None:
    incident_directory = tmp_path / "data" / "incidents"
    calibration_directory = tmp_path / "data" / "evals" / "calibration"
    incident_directory.mkdir(parents=True)
    calibration_directory.mkdir(parents=True)
    (incident_directory / "INC-001.json").write_text("not JSON", encoding="utf-8")

    repository = JsonDatasetRepository(tmp_path)

    with pytest.raises(DatasetLoadError, match="invalid JSON"):
        repository.load_incidents()


def test_repository_rejects_calibration_case_in_the_wrong_split(tmp_path: Path) -> None:
    fixture = json.loads((ROOT / "data" / "evals" / "calibration" / "EVAL-001.json").read_text())
    fixture["split"] = "heldout"
    calibration_directory = tmp_path / "data" / "evals" / "calibration"
    calibration_directory.mkdir(parents=True)
    (calibration_directory / "EVAL-001.json").write_text(json.dumps(fixture), encoding="utf-8")

    repository = JsonDatasetRepository(tmp_path)

    with pytest.raises(DatasetLoadError, match="non-calibration"):
        repository.load_calibration_cases()
