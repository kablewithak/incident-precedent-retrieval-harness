from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from incident_precedent_harness.decisions.strict_dominance_selection import (
    CandidateSelectionEvidence,
    RepresentativeSelectionResult,
    RepresentativeSelectionState,
)
from incident_precedent_harness.evaluation.tranche_02_future_holdout_comparison import (
    FROZEN_FIXTURE_RELATIVE_PATH,
    FREEZE_MANIFEST_FILENAME,
    FREEZE_RECEIPT_RELATIVE_PATH,
    JSON_REPORT_RELATIVE_PATH,
    MARKDOWN_REPORT_RELATIVE_PATH,
    Tranche02FutureHeldoutComparisonDecision,
    Tranche02FutureHeldoutComparisonError,
    run_tranche_02_future_heldout_comparison,
    write_tranche_02_future_heldout_comparison_report,
)


@dataclass(frozen=True)
class _FakeFamily:
    value: str


@dataclass(frozen=True)
class _FakeCard:
    incident_id: str
    incident_family: _FakeFamily
    selection_signature: object | None


class _ContractSelector:
    def __init__(self, *, force_mismatch: bool = False) -> None:
        self.force_mismatch = force_mismatch
        self.calls = 0

    def select(self, *, intake, candidate_incident_ids, incidents):
        self.calls += 1
        candidate_ids = tuple(candidate_incident_ids)
        if self.force_mismatch:
            selected = (candidate_ids[0],)
            state = RepresentativeSelectionState.SINGLE_REPRESENTATIVE
        elif set(candidate_ids) == {"INC-009", "INC-010"}:
            selected = ("INC-009",)
            state = RepresentativeSelectionState.SINGLE_REPRESENTATIVE
        else:
            selected = tuple(sorted(candidate_ids))
            state = RepresentativeSelectionState.EXPLICIT_TIE
        return RepresentativeSelectionResult(
            selection_state=state,
            representative_incident_ids=selected,
            candidate_evidence=tuple(
                CandidateSelectionEvidence(
                    incident_id=incident_id,
                    service_alignment="unknown",
                    component_alignment="unknown",
                    change_context_alignment="unknown",
                    reasons=("test trace",),
                )
                for incident_id in sorted(candidate_ids)
            ),
            selection_reason="test-only selector result",
        )


def test_frozen_comparison_passes_but_remains_activation_blocked(tmp_path: Path) -> None:
    loader = _build_frozen_fixture(tmp_path)
    selector = _ContractSelector()

    report = run_tranche_02_future_heldout_comparison(
        repository_root=tmp_path,
        selector=selector,
        incident_card_loader=loader,
    )

    assert report.comparison_decision is (
        Tranche02FutureHeldoutComparisonDecision.COMPARISON_PASSED_ACTIVATION_BLOCKED
    )
    assert report.metrics.valid_selector_case_count == 10
    assert report.metrics.pre_selector_rejection_case_count == 2
    assert report.metrics.valid_case_contract_pass_rate == 1.0
    assert report.metrics.order_invariance_passed is True
    assert selector.calls == 10
    assert all(outcome.contract_matches for outcome in report.outcomes)
    assert report.metrics.selector_activation_authorized is False


def test_frozen_asset_hash_drift_refuses_before_selector_execution(tmp_path: Path) -> None:
    loader = _build_frozen_fixture(tmp_path)
    target = (
        tmp_path
        / FROZEN_FIXTURE_RELATIVE_PATH
        / "inputs/cases/SEL-T02-FH-003.json"
    )
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    selector = _ContractSelector()

    with pytest.raises(Tranche02FutureHeldoutComparisonError, match="frozen asset .*mismatch"):
        run_tranche_02_future_heldout_comparison(
            repository_root=tmp_path,
            selector=selector,
            incident_card_loader=loader,
        )

    assert selector.calls == 0


def test_selector_contract_mismatch_is_recorded_as_blocked_evidence(tmp_path: Path) -> None:
    loader = _build_frozen_fixture(tmp_path)
    report = run_tranche_02_future_heldout_comparison(
        repository_root=tmp_path,
        selector=_ContractSelector(force_mismatch=True),
        incident_card_loader=loader,
    )

    assert report.comparison_decision is (
        Tranche02FutureHeldoutComparisonDecision.COMPARISON_BLOCKED
    )
    assert report.metrics.failed_case_ids
    assert report.metrics.valid_case_contract_pass_rate < 1.0


def test_comparison_report_is_write_once(tmp_path: Path) -> None:
    loader = _build_frozen_fixture(tmp_path)
    report = run_tranche_02_future_heldout_comparison(
        repository_root=tmp_path,
        selector=_ContractSelector(),
        incident_card_loader=loader,
    )

    write_tranche_02_future_heldout_comparison_report(
        report=report,
        json_path=tmp_path / JSON_REPORT_RELATIVE_PATH,
        markdown_path=tmp_path / MARKDOWN_REPORT_RELATIVE_PATH,
    )

    with pytest.raises(FileExistsError, match="will not be overwritten"):
        write_tranche_02_future_heldout_comparison_report(
            report=report,
            json_path=tmp_path / JSON_REPORT_RELATIVE_PATH,
            markdown_path=tmp_path / MARKDOWN_REPORT_RELATIVE_PATH,
        )


def _build_frozen_fixture(tmp_path: Path):
    fixture_root = tmp_path / FROZEN_FIXTURE_RELATIVE_PATH
    runtime_root = fixture_root / "inputs/cases"
    outcome_root = fixture_root / "expected_outcomes"
    runtime_root.mkdir(parents=True)
    outcome_root.mkdir(parents=True)
    incidents_root = tmp_path / "data/incidents"
    incidents_root.mkdir(parents=True)

    source_payloads = {
        "INC-001": _json_bytes({"incident_id": "INC-001"}),
        "INC-009": _json_bytes({"incident_id": "INC-009"}),
        "INC-010": _json_bytes({"incident_id": "INC-010"}),
        "INC-012": _json_bytes({"incident_id": "INC-012"}),
    }
    for incident_id, payload in source_payloads.items():
        (incidents_root / f"{incident_id}.json").write_bytes(payload)

    cards = {
        "INC-001": _FakeCard("INC-001", _FakeFamily("queue_backlog_consumer_failure"), None),
        "INC-009": _FakeCard("INC-009", _FakeFamily("connection_pool_exhaustion"), object()),
        "INC-010": _FakeCard("INC-010", _FakeFamily("connection_pool_exhaustion"), object()),
        "INC-012": _FakeCard("INC-012", _FakeFamily("connection_pool_exhaustion"), object()),
    }

    def loader(path: Path):
        return cards[path.stem]

    inventory = []
    for number in range(1, 13):
        case_id = f"SEL-T02-FH-{number:03d}"
        if number == 12:
            candidates = ("INC-001", "INC-009")
            family = "queue_backlog_consumer_failure"
        elif number == 2:
            candidates = ("INC-010", "INC-009")
            family = "connection_pool_exhaustion"
        elif number in {3, 4, 5, 6, 7, 8, 9, 10}:
            candidates = ("INC-009", "INC-012")
            family = "connection_pool_exhaustion"
        else:
            candidates = ("INC-009", "INC-010")
            family = "connection_pool_exhaustion"

        intake = {
            "service": "payments-api",
            "component": "postgres-client-pool",
            "change_context": "none",
            "operational_signal_families": ["connection_pool_pressure"],
            "contradicted_signal_families": [],
        }
        if number == 11:
            intake["operational_signal_families"] = [
                "connection_pool_pressure",
                "connection_pool_pressure",
            ]
        runtime = {
            "case_id": case_id,
            "contract_version": "tranche-02-selection-v1",
            "selection_intake": intake,
            "candidate_incident_ids": list(candidates),
            "candidate_pool_family": family,
        }
        runtime_payload = _json_bytes(runtime)
        runtime_path = runtime_root / f"{case_id}.json"
        runtime_path.write_bytes(runtime_payload)
        inventory.append(_asset_record(f"inputs/cases/{case_id}.json", runtime_payload, "runtime_inputs"))

        valid = number <= 10
        kind = (
            "invalid_input"
            if not valid
            else "single_representative"
            if set(candidates) == {"INC-009", "INC-010"}
            else "explicit_tie"
        )
        representatives = ["INC-009"] if kind == "single_representative" else []
        non_dominated = (
            ["INC-009"]
            if kind == "single_representative"
            else []
            if kind == "invalid_input"
            else sorted(candidates)
        )
        source_cards = [
            {
                "source_card_id": incident_id,
                "source_card_sha256": _sha256(source_payloads[incident_id]),
                "incident_family": cards[incident_id].incident_family.value,
                "selection_signature_present": cards[incident_id].selection_signature is not None,
            }
            for incident_id in candidates
        ]
        pre_selector = (
            {"must_pass_before_selector": True, "expected_status": "valid"}
            if valid
            else {
                "must_pass_before_selector": False,
                "expected_status": "invalid",
                "validation_boundary": (
                    "RepresentativeSelectionIntake"
                    if number == 11
                    else "candidate_pool_family"
                ),
                "expected_error_class": (
                    "duplicate_operational_signal_family"
                    if number == 11
                    else "cross_family_candidate_pool_rejected"
                ),
                "selector_execution_permitted": False,
            }
        )
        outcome = {
            "case_id": case_id,
            "expected_outcome_kind": kind,
            "expected_representative_ids": representatives,
            "expected_non_dominated_ids": non_dominated,
            "expected_reason_codes": {
                "classification": "evaluator-diagnostic-only",
                "codes": ["test"],
                "non_runtime_notice": "These codes must not be loaded by runtime selector code.",
            },
            "pre_selector_validation": pre_selector,
            "source_grounding": {
                "source_corpus": "test corpus",
                "source_cards": source_cards,
                "grounding_note": "test grounding",
            },
            "acceptance_reason": "test",
            "failure_label_intent": ["test"],
            "diagnostic_explanation": "test",
            "proposal_status": "frozen",
        }
        if number in {1, 2}:
            outcome["order_reversal_invariant"] = {"pair_id": "pair"}
        outcome_payload = _json_bytes(outcome)
        (outcome_root / f"{case_id}.json").write_bytes(outcome_payload)
        inventory.append(_asset_record(f"expected_outcomes/{case_id}.json", outcome_payload, "expected_outcomes"))

    aggregates = {
        "runtime_inputs": _aggregate(
            [item for item in inventory if item["asset_group"] == "runtime_inputs"]
        ),
        "expected_outcomes": _aggregate(
            [item for item in inventory if item["asset_group"] == "expected_outcomes"]
        ),
        "all_frozen_assets": _aggregate(inventory),
    }
    checks = [
        {
            "case_id": f"SEL-T02-FH-{number:03d}",
            "expected_outcome_kind": (
                "invalid_input" if number > 10 else "single_representative"
            ),
            "validation_status": "invalid_expected" if number > 10 else "valid",
            "validation_boundary": (
                "RepresentativeSelectionIntake"
                if number == 11
                else "candidate_pool_family"
                if number == 12
                else "RepresentativeSelectionIntake_and_candidate_pool_shape"
            ),
            "expected_error_class": (
                "duplicate_operational_signal_family"
                if number == 11
                else "cross_family_candidate_pool_rejected"
                if number == 12
                else None
            ),
            "selector_execution_permitted": number <= 10,
        }
        for number in range(1, 13)
    ]
    manifest = {
        "manifest_kind": "tranche_02_future_heldout_freeze_manifest",
        "freeze_status": "frozen_test_only_not_active",
        "source_acceptance_decision": "accepted_for_governed_future_tranche_freeze",
        "accepted_case_ids": [f"SEL-T02-FH-{number:03d}" for number in range(1, 13)],
        "runtime_case_count": 12,
        "expected_outcome_count": 12,
        "source_archive_asset_count": 27,
        "frozen_asset_inventory": inventory,
        "frozen_aggregate_hashes": aggregates,
        "pre_selector_checks": checks,
        "selector_loaded": False,
        "active_policy_loaded": False,
        "retrieval_loaded": False,
        "procedures_loaded": False,
        "existing_heldout_loaded": False,
        "procedure_asymmetry_fixture_loaded": False,
        "selector_activation_authorized": False,
    }
    manifest_payload = _json_bytes(manifest)
    (fixture_root / FREEZE_MANIFEST_FILENAME).write_bytes(manifest_payload)

    receipt = {
        "report_kind": "tranche_02_future_heldout_freeze",
        "decision": "frozen_test_only",
        "frozen_fixture_path": FROZEN_FIXTURE_RELATIVE_PATH.as_posix(),
        "freeze_manifest_path": (
            FROZEN_FIXTURE_RELATIVE_PATH / FREEZE_MANIFEST_FILENAME
        ).as_posix(),
        "freeze_manifest_sha256": _sha256(manifest_payload),
        "runtime_case_count": 12,
        "expected_outcome_count": 12,
        "source_archive_asset_count": 27,
        "selector_loaded": False,
        "active_policy_loaded": False,
        "retrieval_loaded": False,
        "selector_activation_authorized": False,
    }
    receipt_path = tmp_path / FREEZE_RECEIPT_RELATIVE_PATH
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_bytes(_json_bytes(receipt))
    return loader


def _asset_record(path: str, payload: bytes, group: str) -> dict[str, object]:
    return {
        "relative_path": path,
        "byte_count": len(payload),
        "sha256": _sha256(payload),
        "asset_group": group,
    }


def _aggregate(records) -> str:
    lines = "".join(
        f"{record['sha256']}  {record['byte_count']}  {record['relative_path']}\n"
        for record in sorted(records, key=lambda item: item["relative_path"])
    )
    return _sha256(lines.encode("utf-8"))


def _json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
