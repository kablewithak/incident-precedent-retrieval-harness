from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from incident_precedent_harness.evaluation.tranche_02_future_holdout_freeze import (
    FREEZE_MANIFEST_FILENAME,
    JSON_REPORT_RELATIVE_PATH,
    MARKDOWN_REPORT_RELATIVE_PATH,
    TARGET_RELATIVE_PATH,
    Tranche02FutureHeldoutFreezeError,
    validate_and_freeze_tranche_02_future_heldout,
)

PROPOSAL_ROOT = "proposed_tranche_02_future_heldout"
EXPECTED_CASE_IDS = tuple(f"SEL-T02-FH-{number:03d}" for number in range(1, 13))


def test_freezes_only_runtime_and_expected_outcome_assets_after_all_gates_pass(
    tmp_path: Path,
) -> None:
    archive = _build_archive(tmp_path)
    _write_acceptance_audit(tmp_path, archive)

    report = validate_and_freeze_tranche_02_future_heldout(
        repository_root=tmp_path,
        proposal_archive=archive,
    )

    destination = tmp_path / TARGET_RELATIVE_PATH
    assert report.decision.value == "frozen_test_only"
    assert report.runtime_case_count == 12
    assert report.expected_outcome_count == 12
    assert (destination / FREEZE_MANIFEST_FILENAME).is_file()
    assert (tmp_path / JSON_REPORT_RELATIVE_PATH).is_file()
    assert (tmp_path / MARKDOWN_REPORT_RELATIVE_PATH).is_file()
    copied_paths = sorted(
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    )
    assert copied_paths == [
        FREEZE_MANIFEST_FILENAME,
        *[f"expected_outcomes/{case_id}.json" for case_id in EXPECTED_CASE_IDS],
        *[f"inputs/cases/{case_id}.json" for case_id in EXPECTED_CASE_IDS],
    ]
    freeze_manifest = json.loads((destination / FREEZE_MANIFEST_FILENAME).read_text())
    assert freeze_manifest["selector_loaded"] is False
    assert freeze_manifest["active_policy_loaded"] is False
    assert freeze_manifest["selector_activation_authorized"] is False


def test_refuses_to_overwrite_a_successful_freeze(tmp_path: Path) -> None:
    archive = _build_archive(tmp_path)
    _write_acceptance_audit(tmp_path, archive)
    validate_and_freeze_tranche_02_future_heldout(
        repository_root=tmp_path,
        proposal_archive=archive,
    )

    with pytest.raises(FileExistsError, match="will not be overwritten"):
        validate_and_freeze_tranche_02_future_heldout(
            repository_root=tmp_path,
            proposal_archive=archive,
        )


def test_refuses_a_manifest_hash_mismatch_before_any_copy(tmp_path: Path) -> None:
    archive = _build_archive(tmp_path, tamper_runtime=True)
    _write_acceptance_audit(tmp_path, archive)

    with pytest.raises(Tranche02FutureHeldoutFreezeError, match="SHA-256 mismatch"):
        validate_and_freeze_tranche_02_future_heldout(
            repository_root=tmp_path,
            proposal_archive=archive,
        )

    assert not (tmp_path / TARGET_RELATIVE_PATH).exists()
    assert not (tmp_path / JSON_REPORT_RELATIVE_PATH).exists()


def test_refuses_evaluator_outcome_leakage_in_runtime_input(tmp_path: Path) -> None:
    archive = _build_archive(tmp_path, runtime_leak=True)
    _write_acceptance_audit(tmp_path, archive)

    with pytest.raises(Tranche02FutureHeldoutFreezeError, match="evaluator-only outcome"):
        validate_and_freeze_tranche_02_future_heldout(
            repository_root=tmp_path,
            proposal_archive=archive,
        )


def test_refuses_when_cross_family_case_is_not_genuinely_mixed(tmp_path: Path) -> None:
    archive = _build_archive(tmp_path, broken_cross_family_case=True)
    _write_acceptance_audit(tmp_path, archive)

    with pytest.raises(Tranche02FutureHeldoutFreezeError, match="genuinely mixed-family"):
        validate_and_freeze_tranche_02_future_heldout(
            repository_root=tmp_path,
            proposal_archive=archive,
        )


def _build_archive(
    root: Path,
    *,
    tamper_runtime: bool = False,
    runtime_leak: bool = False,
    broken_cross_family_case: bool = False,
) -> Path:
    assets = _build_assets(
        runtime_leak=runtime_leak,
        broken_cross_family_case=broken_cross_family_case,
    )
    inventory = []
    for path, payload in sorted(assets.items()):
        inventory.append(
            {
                "path": path,
                "asset_group": _asset_group(path),
                "byte_count": len(payload),
                "sha256": _sha256(payload),
            }
        )
    if tamper_runtime:
        assets["inputs/cases/SEL-T02-FH-003.json"] += b"\n"

    manifest = {
        "manifest_version": "future-heldout-proposal-manifest-v1",
        "proposal": {
            "proposal_id": "tranche-02-future-heldout-blind-authoring-proposal-v2",
            "contract_version": "tranche-02-selection-v1",
            "authoring_batch": "test",
            "authoring_role": "constrained_remediation_author",
            "created_at_utc": "2026-06-27T18:30:00Z",
            "archive_root": PROPOSAL_ROOT,
            "proposal_status": "not_frozen",
            "purpose": "test fixture",
            "authoring_scope": "test fixture",
        },
        "boundary_declarations": {
            "not_frozen": True,
            "not_active_policy": True,
            "not_retrieval_evidence": True,
            "not_production_evidence": True,
            "not_procedure_authorization_evidence": True,
            "not_selector_calibration_material": True,
            "not_customer_data_validation": True,
            "runtime_inputs_are_outcome_free": True,
            "expected_reason_codes_are_evaluator_diagnostic_only": True,
        },
        "accepted_case_ids": list(EXPECTED_CASE_IDS),
        "rejected_case_ids": ["REJ-FH-001"],
        "case_coverage": {
            "strict_typed_dominance": ["SEL-T02-FH-001"],
            "explicit_non_dominated_tie": ["SEL-T02-FH-005"],
            "contradicted_signal_penalty": ["SEL-T02-FH-006"],
            "unknown_identity_or_context": ["SEL-T02-FH-009"],
            "candidate_order_reversal_pair": ["SEL-T02-FH-001", "SEL-T02-FH-002"],
            "incident_identifier_not_selector_input": ["SEL-T02-FH-001"],
            "invalid_input_before_selector": ["SEL-T02-FH-011"],
            "cross_family_candidate_pool_rejection_before_selector": ["SEL-T02-FH-012"],
        },
        "source_corpus_grounding": {
            "source_card_hashes_referenced_by_accepted_assets": _source_hashes(),
            "source_cards_mutated_by_proposal": [],
            "selection_boundary_note": "test-only fixture",
        },
        "integrity_algorithm": {
            "per_asset": "SHA-256 over exact UTF-8 file bytes.",
            "aggregate": "SHA-256 over UTF-8 concatenation of sorted lines.",
        },
        "asset_inventory": inventory,
        "aggregate_hashes": {
            "runtime_inputs": _aggregate(inventory, "runtime_inputs"),
            "expected_outcomes": _aggregate(inventory, "expected_outcomes"),
            "documentation": _aggregate(inventory, "documentation"),
            "all_non_manifest_assets": _aggregate(inventory, None),
        },
    }
    archive = root / "tranche-02-future-heldout-blind-authoring-proposal-v2.zip"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as zip_file:
        for path, payload in sorted(assets.items()):
            zip_file.writestr(f"{PROPOSAL_ROOT}/{path}", payload)
        zip_file.writestr(
            f"{PROPOSAL_ROOT}/manifest.json",
            _json_bytes(manifest),
        )
    return archive


def _build_assets(*, runtime_leak: bool, broken_cross_family_case: bool) -> dict[str, bytes]:
    assets: dict[str, bytes] = {
        "APPLY_MANIFEST.md": b"# apply\n",
        "authoring_ledger.md": b"# ledger\n",
        "rejected_case_ideas.md": b"# rejected\n",
    }
    for case_id in EXPECTED_CASE_IDS:
        number = int(case_id.rsplit("-", 1)[1])
        candidates = ["INC-009", "INC-010"]
        intake = {
            "service": "payments-api",
            "component": "postgres-client-pool",
            "change_context": "none",
            "operational_signal_families": ["connection_pool_pressure"],
            "contradicted_signal_families": [],
        }
        if case_id == "SEL-T02-FH-002":
            candidates = ["INC-010", "INC-009"]
        if case_id in {"SEL-T02-FH-005", "SEL-T02-FH-006", "SEL-T02-FH-007", "SEL-T02-FH-008", "SEL-T02-FH-009"}:
            candidates = ["INC-009", "INC-012"]
        if case_id == "SEL-T02-FH-011":
            intake["operational_signal_families"] = [
                "connection_pool_pressure",
                "connection_pool_pressure",
            ]
        if case_id == "SEL-T02-FH-012":
            candidates = ["INC-001", "INC-009"]
            intake = {
                "service": None,
                "component": None,
                "change_context": None,
                "operational_signal_families": [],
                "contradicted_signal_families": [],
            }
        runtime = {
            "case_id": case_id,
            "contract_version": "tranche-02-selection-v1",
            "selection_intake": intake,
            "candidate_incident_ids": candidates,
            "candidate_pool_family": "queue_backlog_consumer_failure"
            if case_id == "SEL-T02-FH-012"
            else "connection_pool_exhaustion",
        }
        if runtime_leak and case_id == "SEL-T02-FH-003":
            runtime["expected_representative_ids"] = ["INC-009"]
        assets[f"inputs/cases/{case_id}.json"] = _json_bytes(runtime)

        expected_kind = "single_representative"
        representative_ids = ["INC-009"]
        non_dominated_ids = ["INC-009"]
        valid = True
        if number in {5, 6, 7, 8, 9}:
            expected_kind = "explicit_tie"
            representative_ids = []
            non_dominated_ids = candidates
        if case_id in {"SEL-T02-FH-011", "SEL-T02-FH-012"}:
            expected_kind = "invalid_input"
            representative_ids = []
            non_dominated_ids = []
            valid = False
        source_cards = _source_cards_for(case_id, candidates, broken_cross_family_case)
        pre_validation: dict[str, object] = {
            "must_pass_before_selector": valid,
            "expected_status": "valid" if valid else "invalid",
        }
        if case_id == "SEL-T02-FH-011":
            pre_validation.update(
                {
                    "validation_boundary": "RepresentativeSelectionIntake",
                    "expected_error_class": "duplicate_operational_signal_family",
                    "selector_execution_permitted": False,
                }
            )
        if case_id == "SEL-T02-FH-012":
            pre_validation.update(
                {
                    "validation_boundary": "candidate_pool_family",
                    "expected_error_class": "cross_family_candidate_pool_rejected",
                    "selector_execution_permitted": False,
                }
            )
        outcome: dict[str, object] = {
            "case_id": case_id,
            "expected_outcome_kind": expected_kind,
            "expected_representative_ids": representative_ids,
            "expected_non_dominated_ids": non_dominated_ids,
            "expected_reason_codes": {
                "classification": "evaluator-diagnostic-only",
                "codes": ["test_diagnostic"],
                "non_runtime_notice": "These codes are comparison-harness diagnostics only and must not be loaded by runtime selector code.",
            },
            "pre_selector_validation": pre_validation,
            "source_grounding": {
                "source_corpus": "synthetic RelayOps incident-card corpus",
                "source_cards": source_cards,
                "grounding_note": "test fixture",
            },
            "acceptance_reason": "test fixture",
            "failure_label_intent": ["test"],
            "diagnostic_explanation": "test fixture",
            "proposal_status": "not_frozen_evaluator_controlled_expected_outcome",
        }
        if case_id == "SEL-T02-FH-001":
            outcome["order_reversal_invariant"] = {"partner_case_id": "SEL-T02-FH-002"}
        assets[f"expected_outcomes/{case_id}.json"] = _json_bytes(outcome)
    return assets


def _source_cards_for(
    case_id: str,
    candidates: list[str],
    broken_cross_family_case: bool,
) -> list[dict[str, object]]:
    families = {
        "INC-001": "queue_backlog_consumer_failure",
        "INC-009": "connection_pool_exhaustion",
        "INC-010": "connection_pool_exhaustion",
        "INC-012": "connection_pool_exhaustion",
    }
    if case_id == "SEL-T02-FH-012" and broken_cross_family_case:
        families["INC-001"] = "queue_backlog_consumer_failure"
        families["INC-009"] = "queue_backlog_consumer_failure"
    hashes = _source_hashes()
    return [
        {
            "source_card_id": candidate,
            "source_card_sha256": hashes[candidate],
            "incident_family": families[candidate],
            "selection_signature_present": candidate != "INC-001",
        }
        for candidate in candidates
    ]


def _source_hashes() -> dict[str, str]:
    return {
        "INC-001": "a" * 64,
        "INC-009": "b" * 64,
        "INC-010": "c" * 64,
        "INC-012": "d" * 64,
    }


def _write_acceptance_audit(root: Path, archive: Path) -> None:
    path = root / "docs/reports/tranche-02-future-heldout-v2-acceptance-audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "audit_kind": "tranche_02_future_heldout_v2_acceptance_audit",
        "decision": "accepted_for_governed_future_tranche_freeze",
        "audited_archive": {
            "file_name": archive.name,
            "sha256": _sha256(archive.read_bytes()),
            "proposal_root": f"{PROPOSAL_ROOT}/",
            "runtime_case_count": 12,
            "expected_outcome_count": 12,
        },
    }
    path.write_bytes(_json_bytes(payload))


def _asset_group(path: str) -> str:
    if path.startswith("inputs/cases/"):
        return "runtime_inputs"
    if path.startswith("expected_outcomes/"):
        return "expected_outcomes"
    return "documentation"


def _aggregate(inventory: list[dict[str, object]], group: str | None) -> str:
    members = [
        item for item in inventory if group is None or item["asset_group"] == group
    ]
    lines = "".join(
        f"{item['sha256']}  {item['byte_count']}  {item['path']}\n"
        for item in sorted(members, key=lambda item: str(item["path"]))
    )
    return _sha256(lines.encode("utf-8"))


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
