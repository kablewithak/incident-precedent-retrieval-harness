from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from incident_precedent_harness.decisions.strict_dominance_selection import (
    StrictDominanceRepresentativeSelector,
)
from incident_precedent_harness.domain.incident_data import (
    HistoricalIncidentCard,
    RepresentativeSelectionIntake,
)
from incident_precedent_harness.evaluation.procedure_asymmetry_fixture_import import (
    JSON_REPORT_RELATIVE_PATH,
    MARKDOWN_REPORT_RELATIVE_PATH,
    ProcedureAsymmetryFixtureImportError,
    TARGET_RELATIVE_PATH,
    verify_and_import_procedure_asymmetry_fixture,
)
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository


@pytest.fixture()
def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_imports_actual_v2_asset_shape_into_an_isolated_fixture(
    repository_root: Path,
    tmp_path: Path,
) -> None:
    archive = _build_actual_v2_shape_archive(repository_root, tmp_path)
    target_root = tmp_path / "target-repository"

    report = verify_and_import_procedure_asymmetry_fixture(
        repository_root=target_root,
        proposal_archive=archive,
    )

    assert report.decision.value == "imported_test_only"
    assert report.controlled_card_count == 4
    assert report.runtime_case_count == 3
    assert report.expected_outcome_count == 3
    assert report.derivation_assertion_count == 4
    assert all(outcome.contract_matches for outcome in report.outcomes)
    assert {
        aggregate.formula
        for aggregate in report.aggregate_verifications
    } == {"canonical_json_inventory_records_v2"}
    assert (target_root / TARGET_RELATIVE_PATH / "manifest.json").is_file()
    assert (target_root / JSON_REPORT_RELATIVE_PATH).is_file()
    assert (target_root / MARKDOWN_REPORT_RELATIVE_PATH).is_file()
    assert not (target_root / "data" / "incidents").exists()


def test_import_accepts_exactly_one_archive_wrapper_directory(
    repository_root: Path,
    tmp_path: Path,
) -> None:
    archive = _build_actual_v2_shape_archive(repository_root, tmp_path)
    wrapped_archive = tmp_path / "wrapped-proposal.zip"
    wrapper = "procedure-asymmetry-adversarial-fixture-proposal-v2"

    with ZipFile(archive) as source, ZipFile(wrapped_archive, "w", ZIP_DEFLATED) as destination:
        for name in source.namelist():
            destination.writestr(f"{wrapper}/{name}", source.read(name))

    report = verify_and_import_procedure_asymmetry_fixture(
        repository_root=tmp_path / "target-repository",
        proposal_archive=wrapped_archive,
    )

    assert report.decision.value == "imported_test_only"
    assert all(outcome.contract_matches for outcome in report.outcomes)


def test_refuses_a_raw_asset_hash_mismatch_before_copy(
    repository_root: Path,
    tmp_path: Path,
) -> None:
    archive = _build_actual_v2_shape_archive(repository_root, tmp_path)
    broken_archive = tmp_path / "broken.zip"
    with ZipFile(archive) as source, ZipFile(broken_archive, "w", ZIP_DEFLATED) as destination:
        for name in source.namelist():
            data = source.read(name)
            if name.endswith("inputs/cases/PAF-T02-001.input.json"):
                data += b"\n"
            destination.writestr(name, data)

    target_root = tmp_path / "target-repository"
    with pytest.raises(ProcedureAsymmetryFixtureImportError, match="SHA-256 mismatch"):
        verify_and_import_procedure_asymmetry_fixture(
            repository_root=target_root,
            proposal_archive=broken_archive,
        )

    assert not (target_root / TARGET_RELATIVE_PATH).exists()
    assert not (target_root / JSON_REPORT_RELATIVE_PATH).exists()


def test_refuses_expected_fields_inside_runtime_input(
    repository_root: Path,
    tmp_path: Path,
) -> None:
    archive = _build_actual_v2_shape_archive(
        repository_root,
        tmp_path,
        mutate_runtime=True,
    )

    with pytest.raises(
        ProcedureAsymmetryFixtureImportError,
        match="runtime input leaks expected outcome fields",
    ):
        verify_and_import_procedure_asymmetry_fixture(
            repository_root=tmp_path / "target-repository",
            proposal_archive=archive,
        )


def test_import_is_write_once(
    repository_root: Path,
    tmp_path: Path,
) -> None:
    archive = _build_actual_v2_shape_archive(repository_root, tmp_path)
    target_root = tmp_path / "target-repository"

    verify_and_import_procedure_asymmetry_fixture(
        repository_root=target_root,
        proposal_archive=archive,
    )

    with pytest.raises(FileExistsError, match="write-once"):
        verify_and_import_procedure_asymmetry_fixture(
            repository_root=target_root,
            proposal_archive=archive,
        )


def test_selector_uses_each_runtime_cases_declared_controlled_card_set(
    repository_root: Path,
    tmp_path: Path,
) -> None:
    archive = _build_actual_v2_shape_archive(repository_root, tmp_path)
    selector = _RecordingSelector()

    report = verify_and_import_procedure_asymmetry_fixture(
        repository_root=tmp_path / "target-repository",
        proposal_archive=archive,
        selector=selector,
    )

    assert all(outcome.contract_matches for outcome in report.outcomes)
    assert len(selector.calls) == 3

    primary_cards = {card.incident_id: card for card in selector.calls[0]}
    neutral_cards = {card.incident_id: card for card in selector.calls[2]}

    assert primary_cards["INC-013"].safe_procedure_ids == ("RB-003",)
    assert primary_cards["INC-014"].unsafe_procedure_ids == ("RB-003",)
    assert neutral_cards["INC-013"].safe_procedure_ids == ()
    assert neutral_cards["INC-014"].unsafe_procedure_ids == ()


class _RecordingSelector:
    def __init__(self) -> None:
        self._inner = StrictDominanceRepresentativeSelector()
        self.calls: list[tuple[HistoricalIncidentCard, ...]] = []

    def select(
        self,
        *,
        intake: RepresentativeSelectionIntake,
        candidate_incident_ids: tuple[str, ...],
        incidents: tuple[HistoricalIncidentCard, ...],
    ):
        self.calls.append(incidents)
        return self._inner.select(
            intake=intake,
            candidate_incident_ids=candidate_incident_ids,
            incidents=incidents,
        )


def _build_actual_v2_shape_archive(
    repository_root: Path,
    tmp_path: Path,
    *,
    mutate_runtime: bool = False,
) -> Path:
    root = "proposed_procedure_asymmetry_fixture"
    repository = JsonDatasetRepository(repository_root)
    source_cards = {
        card.incident_id: card.model_dump(mode="json")
        for card in repository.load_incidents()
        if card.incident_id in {"INC-009", "INC-010"}
    }

    assets: dict[str, bytes] = {}
    source_digests = {
        incident_id: hashlib.sha256(_json_bytes(payload)).hexdigest()
        for incident_id, payload in source_cards.items()
    }

    primary_inc_013 = _controlled_variant(
        source_cards["INC-009"],
        incident_id="INC-013",
        title_prefix="Test-only procedure-asymmetry variant: ",
        linked_procedure_ids=None,
        safe_procedure_ids=None,
        unsafe_procedure_ids=[],
    )
    primary_inc_014 = _controlled_variant(
        source_cards["INC-010"],
        incident_id="INC-014",
        title_prefix="Test-only procedure-asymmetry variant: ",
        linked_procedure_ids=[],
        safe_procedure_ids=[],
        unsafe_procedure_ids=["RB-003"],
    )
    neutral_inc_013 = _controlled_variant(
        source_cards["INC-009"],
        incident_id="INC-013",
        title_prefix="Test-only procedure-asymmetry variant: ",
        linked_procedure_ids=[],
        safe_procedure_ids=[],
        unsafe_procedure_ids=[],
    )
    neutral_inc_014 = _controlled_variant(
        source_cards["INC-010"],
        incident_id="INC-014",
        title_prefix="Test-only procedure-asymmetry variant: ",
        linked_procedure_ids=[],
        safe_procedure_ids=[],
        unsafe_procedure_ids=[],
    )

    controlled_variants = {
        ("PAV-001-procedure-asymmetric", "INC-013"): (source_cards["INC-009"], primary_inc_013),
        ("PAV-001-procedure-asymmetric", "INC-014"): (source_cards["INC-010"], primary_inc_014),
        ("PAV-002-procedure-neutral-control", "INC-013"): (source_cards["INC-009"], neutral_inc_013),
        ("PAV-002-procedure-neutral-control", "INC-014"): (source_cards["INC-010"], neutral_inc_014),
    }
    for (card_set_id, incident_id), (_, controlled) in controlled_variants.items():
        assets[
            f"inputs/controlled_cards/{card_set_id}/{incident_id}.json"
        ] = _json_bytes(controlled)

    intake = {
        "service": "auth-service",
        "component": "auth-db-client",
        "change_context": "configuration",
        "operational_signal_families": [
            "connection_pool_pressure",
            "authentication_failure",
            "readiness_failure",
            "component_error_pressure",
        ],
        "contradicted_signal_families": [],
    }
    cases = (
        (
            "PAF-T02-001",
            ["INC-013", "INC-014"],
            "PAV-001-procedure-asymmetric",
        ),
        (
            "PAF-T02-002",
            ["INC-014", "INC-013"],
            "PAV-001-procedure-asymmetric",
        ),
        (
            "PAF-T02-003",
            ["INC-013", "INC-014"],
            "PAV-002-procedure-neutral-control",
        ),
    )
    for case_id, candidates, card_set_id in cases:
        runtime = {
            "case_id": case_id,
            "fixture_contract_version": "procedure-asymmetry-adversarial-fixture-v1",
            "candidate_pool_family": "connection_pool_exhaustion",
            "controlled_card_set_id": card_set_id,
            "candidate_incident_ids": candidates,
            "selection_intake": intake,
        }
        if mutate_runtime and case_id == "PAF-T02-001":
            runtime["expected_state"] = "single_representative"
        assets[f"inputs/cases/{case_id}.input.json"] = _json_bytes(runtime)
        assets[f"expected_outcomes/{case_id}.expected.json"] = _json_bytes(
            {
                "case_id": case_id,
                "expected_outcome_kind": "single_representative",
                "expected_representative_ids": ["INC-014"],
                "expected_non_dominated_ids": ["INC-014"],
                "reason_code_status": "evaluation_diagnostic_only_not_selector_contract",
            }
        )

    governance = {
        "fixture_contract_version": "procedure-asymmetry-adversarial-fixture-v2",
        "fixture_kind": "test_only_procedure_asymmetry",
        "procedure_asymmetry": True,
        "test_only": True,
        "selector_payload_rule": {
            "must_not_be_passed_to_selector": [
                "governance registry",
                "procedure asymmetry labels",
            ]
        },
    }
    assets["inputs/governance/procedure_asymmetry_governance.json"] = _json_bytes(governance)

    assertions = []
    for index, ((card_set_id, controlled_id), (source, controlled)) in enumerate(
        controlled_variants.items(),
        start=1,
    ):
        controlled_bytes = _json_bytes(controlled)
        fields = _changed_fields(source, controlled)
        assertions.append(
            {
                "assertion_id": "PAV-001" if index == 1 else f"PAV-{index:03d}",
                "card_set_id": card_set_id,
                "source_incident_id": source["incident_id"],
                "source_card_sha256": source_digests[source["incident_id"]],
                "controlled_incident_id": controlled_id,
                "controlled_card_sha256": hashlib.sha256(controlled_bytes).hexdigest(),
                "actual_changed_fields": fields,
                "allowed_perturbation_fields": fields,
                "exact_field_set_match": True,
                "test_only": True,
            }
        )
    assets["inputs/governance/controlled_card_derivation_assertions.json"] = _json_bytes(
        {
            "assertion_kind": "controlled_card_derivation_assertions_v2",
            "assertions": assertions,
        }
    )
    assets["authoring_ledger.md"] = b"# Ledger\n\nTest-only V2 provenance remediation.\n"
    assets["rejected_case_ideas.md"] = b"# Rejected\n\nNo active-policy import.\n"
    assets["APPLY_MANIFEST.md"] = b"# Apply\n\nImport only through validator.\n"

    inventory = [
        {
            "relative_path": path,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "byte_count": len(payload),
            "group": _group_for(path),
        }
        for path, payload in sorted(assets.items())
    ]
    manifest = {
        "proposal_root": root,
        "proposal_version": "v2",
        "asset_inventory": inventory,
        "aggregate_hashes": _aggregate_hashes(inventory),
    }

    archive = tmp_path / "procedure-asymmetry-adversarial-fixture-proposal-v2.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as zip_file:
        for path, payload in sorted(assets.items()):
            zip_file.writestr(f"{root}/{path}", payload)
        zip_file.writestr(f"{root}/manifest.json", _json_bytes(manifest))
    return archive


def _controlled_variant(
    source: dict[str, object],
    *,
    incident_id: str,
    title_prefix: str,
    linked_procedure_ids: list[str] | None,
    safe_procedure_ids: list[str] | None,
    unsafe_procedure_ids: list[str],
) -> dict[str, object]:
    variant = dict(source)
    variant["incident_id"] = incident_id
    variant["title"] = title_prefix + str(source["title"])
    if linked_procedure_ids is not None:
        variant["linked_procedure_ids"] = linked_procedure_ids
    if safe_procedure_ids is not None:
        variant["safe_procedure_ids"] = safe_procedure_ids
    variant["unsafe_procedure_ids"] = unsafe_procedure_ids
    return variant


def _changed_fields(source: dict[str, object], controlled: dict[str, object]) -> list[str]:
    return sorted(
        field
        for field in set(source) | set(controlled)
        if source.get(field) != controlled.get(field)
    )


def _aggregate_hashes(inventory: list[dict[str, object]]) -> dict[str, str]:
    def digest(records: list[dict[str, object]]) -> str:
        canonical = json.dumps(
            records,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    inputs = [
        entry
        for entry in inventory
        if str(entry["relative_path"]).startswith("inputs/")
        and not str(entry["relative_path"]).startswith("inputs/governance/")
    ]
    expected_outcomes = [
        entry
        for entry in inventory
        if str(entry["relative_path"]).startswith("expected_outcomes/")
    ]
    governance = [
        entry
        for entry in inventory
        if str(entry["relative_path"]).startswith("inputs/governance/")
    ]
    documentation = [
        entry
        for entry in inventory
        if str(entry["relative_path"])
        in {"authoring_ledger.md", "rejected_case_ideas.md", "APPLY_MANIFEST.md"}
    ]
    return {
        "inputs_sha256": digest(inputs),
        "expected_outcomes_sha256": digest(expected_outcomes),
        "governance_sha256": digest(governance),
        "documentation_sha256": digest(documentation),
        "all_non_manifest_assets_sha256": digest(inventory),
    }


def _group_for(path: str) -> str:
    if path.startswith("expected_outcomes/"):
        return "expected_outcomes"
    if path.startswith("inputs/governance/"):
        return "governance"
    if path in {"authoring_ledger.md", "rejected_case_ideas.md", "APPLY_MANIFEST.md"}:
        return "documentation"
    return "inputs"


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
