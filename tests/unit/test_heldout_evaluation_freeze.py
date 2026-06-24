"""Tests for the frozen first held-out evaluation tranche."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from incident_precedent_harness.retrieval.repository import JsonDatasetRepository

ROOT = Path(__file__).resolve().parents[2]
HELDOUT_DIRECTORY = ROOT / "data" / "evals" / "heldout"
FREEZE_MANIFEST = HELDOUT_DIRECTORY / "HELDOUT_FREEZE_MANIFEST.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_heldout_tranche_is_validated_and_has_a_distinct_id_range() -> None:
    repository = JsonDatasetRepository(ROOT)

    cases = repository.load_heldout_cases()

    assert [case.eval_id for case in cases] == [f"EVAL-{number:03}" for number in range(101, 113)]
    assert {case.split for case in cases} == {"heldout"}


def test_heldout_tranche_has_required_case_shape() -> None:
    repository = JsonDatasetRepository(ROOT)
    cases = repository.load_heldout_cases()

    decision_counts = {}
    for case in cases:
        decision_counts[case.expected_decision_state.value] = (
            decision_counts.get(case.expected_decision_state.value, 0) + 1
        )

    assert decision_counts == {
        "evidence_found": 3,
        "insufficient_precedent": 6,
        "evidence_found_with_conflict": 2,
        "provider_degraded": 1,
    }
    assert sum("false_operational_match" in case.failure_label_intent for case in cases) >= 5


def test_heldout_manifest_hashes_match_each_frozen_case() -> None:
    manifest = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))

    assert manifest["freeze_status"] == "frozen"
    assert manifest["case_ids"] == [f"EVAL-{number:03}" for number in range(101, 113)]
    assert set(manifest["sha256_by_filename"]) == {
        f"EVAL-{number:03}.json" for number in range(101, 113)
    }

    for filename, expected_hash in manifest["sha256_by_filename"].items():
        assert _sha256(HELDOUT_DIRECTORY / filename) == expected_hash


def test_heldout_inputs_are_not_exact_calibration_rewrites() -> None:
    repository = JsonDatasetRepository(ROOT)
    calibration = repository.load_calibration_cases()
    heldout = repository.load_heldout_cases()

    calibration_summaries = {
        " ".join(case.input_summary.lower().split()) for case in calibration
    }
    heldout_summaries = {
        " ".join(case.input_summary.lower().split()) for case in heldout
    }

    assert calibration_summaries.isdisjoint(heldout_summaries)
