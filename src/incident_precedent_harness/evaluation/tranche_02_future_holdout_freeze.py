"""Fail-closed import and freeze boundary for future-held-out Tranche 02.

This module accepts only the independently authored and acceptance-audited V2
proposal archive. It verifies the archive before copying its runtime inputs and
evaluator-only outcomes into an isolated frozen location. It intentionally does
not import selector, policy, retrieval, procedure, existing-heldout, or
procedure-asymmetry code.

A successful run is write-once. It creates the frozen asset tree, an immutable
freeze manifest, and JSON/Markdown evidence receipts. It never runs a selector,
changes active behavior, or authorizes selector activation.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import uuid
import zipfile
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from incident_precedent_harness.domain.incident_data import RepresentativeSelectionIntake

PROPOSAL_ROOT = "proposed_tranche_02_future_heldout"
TARGET_RELATIVE_PATH = Path("data") / "evals" / "heldout" / "tranche_02_future_heldout"
FREEZE_MANIFEST_FILENAME = "TRANCHE_02_FUTURE_HELDOUT_FREEZE_MANIFEST.json"
JSON_REPORT_RELATIVE_PATH = (
    Path("evidence_vault") / "reports" / "tranche-02-future-heldout-freeze.json"
)
MARKDOWN_REPORT_RELATIVE_PATH = (
    Path("docs") / "reports" / "tranche-02-future-heldout-freeze.md"
)
ACCEPTANCE_AUDIT_RELATIVE_PATH = (
    Path("docs") / "reports" / "tranche-02-future-heldout-v2-acceptance-audit.json"
)

EXPECTED_CASE_IDS = tuple(f"SEL-T02-FH-{number:03d}" for number in range(1, 13))
RUNTIME_PREFIX = "inputs/cases/"
OUTCOME_PREFIX = "expected_outcomes/"
REQUIRED_DOCUMENT_PATHS = (
    "APPLY_MANIFEST.md",
    "authoring_ledger.md",
    "rejected_case_ideas.md",
)
REQUIRED_COVERAGE_KEYS = (
    "strict_typed_dominance",
    "explicit_non_dominated_tie",
    "contradicted_signal_penalty",
    "unknown_identity_or_context",
    "candidate_order_reversal_pair",
    "incident_identifier_not_selector_input",
    "invalid_input_before_selector",
    "cross_family_candidate_pool_rejection_before_selector",
)
FORBIDDEN_RUNTIME_KEYS = frozenset(
    {
        "expected_outcome_kind",
        "expected_representative_ids",
        "expected_non_dominated_ids",
        "expected_reason_codes",
        "pre_selector_validation",
        "source_grounding",
        "acceptance_reason",
        "failure_label_intent",
        "diagnostic_explanation",
        "proposal_status",
        "order_reversal_invariant",
        "expected_error_class",
        "selector_execution_permitted",
        "expected_state",
    }
)


class Tranche02FutureHeldoutFreezeError(RuntimeError):
    """Raised when the proposal cannot safely enter the frozen evaluation boundary."""


class FreezeDecision(str, Enum):
    """The only successful outcome at this boundary."""

    FROZEN_TEST_ONLY = "frozen_test_only"


class ProposalAsset(BaseModel):
    """One manifest-backed source archive asset."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    asset_group: str = Field(min_length=1)
    byte_count: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class FrozenAsset(BaseModel):
    """Integrity record for one copied runtime or expected-outcome asset."""

    model_config = ConfigDict(extra="forbid")

    relative_path: str = Field(min_length=1)
    byte_count: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    asset_group: str = Field(pattern=r"^(runtime_inputs|expected_outcomes)$")


class AggregateVerification(BaseModel):
    """One source proposal aggregate verification."""

    model_config = ConfigDict(extra="forbid")

    aggregate_name: str
    expected_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    observed_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    formula: str


class PreSelectorCaseCheck(BaseModel):
    """A validation result that deliberately precedes any selector invocation."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^SEL-T02-FH-[0-9]{3}$")
    expected_outcome_kind: str
    validation_status: str = Field(pattern=r"^(valid|invalid_expected)$")
    validation_boundary: str
    expected_error_class: str | None = None
    selector_execution_permitted: bool


class FreezeAssetManifest(BaseModel):
    """The immutable integrity record used by later comparison tooling."""

    model_config = ConfigDict(extra="forbid")

    manifest_kind: str = "tranche_02_future_heldout_freeze_manifest"
    frozen_at: datetime
    freeze_status: str = "frozen_test_only_not_active"
    source_proposal_archive_name: str
    source_proposal_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_proposal_root: str = PROPOSAL_ROOT
    source_acceptance_audit_path: str
    source_acceptance_decision: str
    accepted_case_ids: tuple[str, ...] = Field(min_length=1)
    runtime_case_count: int = Field(ge=1)
    expected_outcome_count: int = Field(ge=1)
    source_archive_asset_count: int = Field(ge=1)
    source_aggregate_verifications: tuple[AggregateVerification, ...] = Field(min_length=1)
    frozen_asset_inventory: tuple[FrozenAsset, ...] = Field(min_length=1)
    frozen_aggregate_hashes: dict[str, str]
    pre_selector_checks: tuple[PreSelectorCaseCheck, ...] = Field(min_length=1)
    selector_loaded: bool = False
    active_policy_loaded: bool = False
    retrieval_loaded: bool = False
    procedures_loaded: bool = False
    existing_heldout_loaded: bool = False
    procedure_asymmetry_fixture_loaded: bool = False
    selector_activation_authorized: bool = False
    non_claims: tuple[str, ...] = Field(min_length=1)


class Tranche02FutureHeldoutFreezeReport(BaseModel):
    """Write-once receipt for the governed Tranche 02 import/freeze operation."""

    model_config = ConfigDict(extra="forbid")

    report_kind: str = "tranche_02_future_heldout_freeze"
    generated_at: datetime
    decision: FreezeDecision
    proposal_archive_name: str
    proposal_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    acceptance_audit_path: str
    frozen_fixture_path: str
    freeze_manifest_path: str
    freeze_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    runtime_case_count: int = Field(ge=1)
    expected_outcome_count: int = Field(ge=1)
    source_archive_asset_count: int = Field(ge=1)
    source_aggregate_verifications: tuple[AggregateVerification, ...] = Field(min_length=1)
    pre_selector_checks: tuple[PreSelectorCaseCheck, ...] = Field(min_length=1)
    selector_loaded: bool = False
    active_policy_loaded: bool = False
    retrieval_loaded: bool = False
    selector_activation_authorized: bool = False
    non_claims: tuple[str, ...] = Field(min_length=1)


class _RuntimeCase(BaseModel):
    """Minimal runtime envelope; selection intake stays raw for invalid-case testing."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^SEL-T02-FH-[0-9]{3}$")
    contract_version: str = Field(min_length=1)
    selection_intake: dict[str, Any]
    candidate_incident_ids: tuple[str, ...] = Field(min_length=2)
    candidate_pool_family: str = Field(min_length=1)


class _ReasonCodes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification: str
    codes: tuple[str, ...] = Field(min_length=1)
    non_runtime_notice: str = Field(min_length=1)


class _PreSelectorValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    must_pass_before_selector: bool
    expected_status: str = Field(pattern=r"^(valid|invalid)$")
    validation_boundary: str | None = None
    expected_error_class: str | None = None
    selector_execution_permitted: bool | None = None


class _GroundingCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_card_id: str = Field(pattern=r"^INC-[0-9]{3}$")
    source_card_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    incident_family: str = Field(min_length=1)
    selection_signature_present: bool


class _SourceGrounding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_corpus: str = Field(min_length=1)
    source_cards: tuple[_GroundingCard, ...] = Field(min_length=2)
    grounding_note: str = Field(min_length=1)


class _ExpectedOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^SEL-T02-FH-[0-9]{3}$")
    expected_outcome_kind: str = Field(
        pattern=r"^(single_representative|explicit_tie|invalid_input)$"
    )
    expected_representative_ids: tuple[str, ...]
    expected_non_dominated_ids: tuple[str, ...]
    expected_reason_codes: _ReasonCodes
    pre_selector_validation: _PreSelectorValidation
    source_grounding: _SourceGrounding
    acceptance_reason: str = Field(min_length=1)
    failure_label_intent: tuple[str, ...] = Field(min_length=1)
    diagnostic_explanation: str = Field(min_length=1)
    proposal_status: str = Field(min_length=1)
    order_reversal_invariant: dict[str, Any] | None = None


def validate_and_freeze_tranche_02_future_heldout(
    *,
    repository_root: Path,
    proposal_archive: Path,
) -> Tranche02FutureHeldoutFreezeReport:
    """Validate the audited V2 archive and create a frozen, isolated fixture tree.

    Nothing is copied until every archive, audit, separation, typed-input, and
    pre-selector validation gate has passed. The function intentionally does not
    import selector, policy, retrieval, procedure, or existing-heldout modules.
    """

    root = repository_root.resolve()
    archive = proposal_archive.resolve()
    if not archive.is_file():
        raise Tranche02FutureHeldoutFreezeError(f"proposal archive is missing: {archive}")

    destination = root / TARGET_RELATIVE_PATH
    freeze_manifest_path = destination / FREEZE_MANIFEST_FILENAME
    json_report_path = root / JSON_REPORT_RELATIVE_PATH
    markdown_report_path = root / MARKDOWN_REPORT_RELATIVE_PATH
    _ensure_write_once(
        destination=destination,
        freeze_manifest_path=freeze_manifest_path,
        json_report_path=json_report_path,
        markdown_report_path=markdown_report_path,
    )

    archive_sha256 = _sha256_bytes(archive.read_bytes())
    acceptance_audit_path = root / ACCEPTANCE_AUDIT_RELATIVE_PATH
    _validate_acceptance_audit(
        audit_path=acceptance_audit_path,
        archive_name=archive.name,
        archive_sha256=archive_sha256,
    )

    files = _normalise_archive_layout(_read_archive(archive))
    root_files = _validate_archive_topology(files)
    manifest = _load_json(files[f"{PROPOSAL_ROOT}/manifest.json"], "manifest.json")
    inventory = _extract_inventory(manifest=manifest, root_files=root_files)
    _verify_inventory(files=files, inventory=inventory)
    aggregate_verifications = _verify_aggregates(manifest=manifest, inventory=inventory)
    _validate_manifest_declarations(manifest=manifest, inventory=inventory)

    runtime_cases = _load_runtime_cases(files=files)
    expected_outcomes = _load_expected_outcomes(files=files)
    _validate_runtime_outcome_separation(
        runtime_cases=runtime_cases,
        expected_outcomes=expected_outcomes,
    )
    pre_selector_checks = _validate_pre_selector_contracts(
        manifest=manifest,
        runtime_cases=runtime_cases,
        expected_outcomes=expected_outcomes,
    )

    freeze_manifest = _build_freeze_manifest(
        archive=archive,
        archive_sha256=archive_sha256,
        inventory=inventory,
        aggregate_verifications=aggregate_verifications,
        runtime_cases=runtime_cases,
        expected_outcomes=expected_outcomes,
        pre_selector_checks=pre_selector_checks,
    )
    freeze_manifest_bytes = _canonical_json_bytes(freeze_manifest.model_dump(mode="json"))
    report = Tranche02FutureHeldoutFreezeReport(
        generated_at=datetime.now(UTC),
        decision=FreezeDecision.FROZEN_TEST_ONLY,
        proposal_archive_name=archive.name,
        proposal_archive_sha256=archive_sha256,
        acceptance_audit_path=ACCEPTANCE_AUDIT_RELATIVE_PATH.as_posix(),
        frozen_fixture_path=TARGET_RELATIVE_PATH.as_posix(),
        freeze_manifest_path=(TARGET_RELATIVE_PATH / FREEZE_MANIFEST_FILENAME).as_posix(),
        freeze_manifest_sha256=_sha256_bytes(freeze_manifest_bytes),
        runtime_case_count=len(runtime_cases),
        expected_outcome_count=len(expected_outcomes),
        source_archive_asset_count=len(inventory),
        source_aggregate_verifications=aggregate_verifications,
        pre_selector_checks=pre_selector_checks,
        non_claims=(
            "This operation freezes test-only evaluation inputs and evaluator outcomes; it does not activate representative selection.",
            "This operation does not load selector implementation, active policy, retrieval, procedures, existing held-out assets, or procedure-asymmetry fixtures.",
            "This operation does not authorize an activation comparison, policy integration, procedure execution, production use, or customer-data validation.",
        ),
    )
    _commit_freeze_and_receipts(
        root=root,
        files=files,
        destination=destination,
        freeze_manifest_bytes=freeze_manifest_bytes,
        json_report_path=json_report_path,
        markdown_report_path=markdown_report_path,
        report=report,
    )
    return report


def _ensure_write_once(
    *,
    destination: Path,
    freeze_manifest_path: Path,
    json_report_path: Path,
    markdown_report_path: Path,
) -> None:
    existing = tuple(
        path
        for path in (destination, freeze_manifest_path, json_report_path, markdown_report_path)
        if path.exists()
    )
    if existing:
        rendered = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            "Future-held-out Tranche 02 freeze evidence already exists and will not be "
            f"overwritten: {rendered}."
        )


def _validate_acceptance_audit(*, audit_path: Path, archive_name: str, archive_sha256: str) -> None:
    if not audit_path.is_file():
        raise Tranche02FutureHeldoutFreezeError(
            "required V2 acceptance audit is missing: "
            f"{ACCEPTANCE_AUDIT_RELATIVE_PATH.as_posix()}"
        )
    audit = _load_json(audit_path.read_bytes(), audit_path.name)
    if audit.get("decision") != "accepted_for_governed_future_tranche_freeze":
        raise Tranche02FutureHeldoutFreezeError(
            "V2 acceptance audit does not authorize governed future-tranche freeze"
        )
    audited = audit.get("audited_archive")
    if not isinstance(audited, Mapping):
        raise Tranche02FutureHeldoutFreezeError("V2 acceptance audit is missing audited_archive")
    if audited.get("file_name") != archive_name:
        raise Tranche02FutureHeldoutFreezeError(
            "proposal archive filename does not match the accepted V2 audit record"
        )
    if audited.get("sha256") != archive_sha256:
        raise Tranche02FutureHeldoutFreezeError(
            "proposal archive SHA-256 does not match the accepted V2 audit record"
        )
    if audited.get("proposal_root") != f"{PROPOSAL_ROOT}/":
        raise Tranche02FutureHeldoutFreezeError(
            "V2 acceptance audit does not name the required proposal root"
        )
    if audited.get("runtime_case_count") != 12 or audited.get("expected_outcome_count") != 12:
        raise Tranche02FutureHeldoutFreezeError(
            "V2 acceptance audit does not declare the required 12 runtime and outcome assets"
        )


def _read_archive(archive: Path) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(archive) as zip_file:
            names = tuple(zip_file.namelist())
            if len(names) != len(set(names)):
                raise Tranche02FutureHeldoutFreezeError(
                    "proposal archive contains duplicate member paths"
                )
            files: dict[str, bytes] = {}
            for name in names:
                if name.endswith("/"):
                    continue
                path = PurePosixPath(name)
                if path.is_absolute() or ".." in path.parts:
                    raise Tranche02FutureHeldoutFreezeError(
                        f"proposal archive contains an unsafe member path: {name}"
                    )
                files[name] = zip_file.read(name)
            return files
    except zipfile.BadZipFile as error:
        raise Tranche02FutureHeldoutFreezeError(
            "proposal archive is not a readable ZIP file"
        ) from error


def _normalise_archive_layout(files: Mapping[str, bytes]) -> dict[str, bytes]:
    """Accept one harmless package wrapper and reject every other root shape."""

    prefix = f"{PROPOSAL_ROOT}/"
    if files and all(path.startswith(prefix) for path in files):
        return dict(files)

    wrappers: set[str] = set()
    for path in files:
        parts = PurePosixPath(path).parts
        if len(parts) < 3 or parts[1] != PROPOSAL_ROOT:
            raise Tranche02FutureHeldoutFreezeError(
                f"proposal archive must contain only {PROPOSAL_ROOT}/ or one wrapper directory"
            )
        wrappers.add(parts[0])
    if len(wrappers) != 1:
        raise Tranche02FutureHeldoutFreezeError(
            "proposal archive must use exactly one wrapper directory when not rooted directly"
        )
    wrapper_prefix = f"{next(iter(wrappers))}/"
    normalised = {
        path.removeprefix(wrapper_prefix): payload for path, payload in files.items()
    }
    if not normalised or any(not path.startswith(prefix) for path in normalised):
        raise Tranche02FutureHeldoutFreezeError(
            f"proposal archive must contain only the {PROPOSAL_ROOT}/ root"
        )
    return normalised


def _validate_archive_topology(files: Mapping[str, bytes]) -> dict[str, bytes]:
    prefix = f"{PROPOSAL_ROOT}/"
    if not files:
        raise Tranche02FutureHeldoutFreezeError("proposal archive is empty")
    if any(not path.startswith(prefix) for path in files):
        raise Tranche02FutureHeldoutFreezeError(
            f"proposal archive must contain only the {PROPOSAL_ROOT}/ root"
        )
    root_files = {path.removeprefix(prefix): payload for path, payload in files.items()}
    expected_paths = {
        "manifest.json",
        *REQUIRED_DOCUMENT_PATHS,
        *{f"{RUNTIME_PREFIX}{case_id}.json" for case_id in EXPECTED_CASE_IDS},
        *{f"{OUTCOME_PREFIX}{case_id}.json" for case_id in EXPECTED_CASE_IDS},
    }
    observed_paths = set(root_files)
    if observed_paths != expected_paths:
        missing = sorted(expected_paths - observed_paths)
        unexpected = sorted(observed_paths - expected_paths)
        pieces: list[str] = []
        if missing:
            pieces.append("missing paths: " + ", ".join(missing))
        if unexpected:
            pieces.append("unexpected paths: " + ", ".join(unexpected))
        raise Tranche02FutureHeldoutFreezeError(
            "proposal archive topology does not match accepted V2 contract; "
            + "; ".join(pieces)
        )
    if len(root_files) != 28:
        raise Tranche02FutureHeldoutFreezeError(
            f"proposal archive must contain exactly 28 files; observed {len(root_files)}"
        )
    return root_files


def _extract_inventory(
    *, manifest: Mapping[str, Any], root_files: Mapping[str, bytes]
) -> tuple[ProposalAsset, ...]:
    raw_inventory = manifest.get("asset_inventory")
    if not isinstance(raw_inventory, list):
        raise Tranche02FutureHeldoutFreezeError("manifest must contain asset_inventory list")
    try:
        inventory = tuple(ProposalAsset.model_validate(item) for item in raw_inventory)
    except ValidationError as error:
        raise Tranche02FutureHeldoutFreezeError(
            "manifest asset_inventory contains an invalid asset record"
        ) from error
    by_path = {asset.path: asset for asset in inventory}
    if len(by_path) != len(inventory):
        raise Tranche02FutureHeldoutFreezeError("manifest asset_inventory repeats an asset path")
    expected_paths = set(root_files) - {"manifest.json"}
    if set(by_path) != expected_paths:
        raise Tranche02FutureHeldoutFreezeError(
            "manifest asset_inventory does not exactly match non-manifest archive paths"
        )
    if len(inventory) != 27:
        raise Tranche02FutureHeldoutFreezeError(
            f"manifest must inventory 27 non-manifest assets; observed {len(inventory)}"
        )
    expected_groups = {
        "runtime_inputs": 12,
        "expected_outcomes": 12,
        "documentation": 3,
    }
    observed_groups = {
        group: sum(asset.asset_group == group for asset in inventory)
        for group in expected_groups
    }
    if observed_groups != expected_groups:
        raise Tranche02FutureHeldoutFreezeError(
            f"manifest asset groups are invalid: {observed_groups}"
        )
    if any(asset.asset_group not in expected_groups for asset in inventory):
        raise Tranche02FutureHeldoutFreezeError("manifest contains an unsupported asset group")
    return tuple(sorted(inventory, key=lambda asset: asset.path))


def _verify_inventory(*, files: Mapping[str, bytes], inventory: tuple[ProposalAsset, ...]) -> None:
    for asset in inventory:
        payload = files.get(f"{PROPOSAL_ROOT}/{asset.path}")
        if payload is None:
            raise Tranche02FutureHeldoutFreezeError(
                f"archive is missing manifest-listed asset: {asset.path}"
            )
        if _sha256_bytes(payload) != asset.sha256:
            raise Tranche02FutureHeldoutFreezeError(f"SHA-256 mismatch for {asset.path}")
        if len(payload) != asset.byte_count:
            raise Tranche02FutureHeldoutFreezeError(
                f"byte count mismatch for {asset.path}"
            )


def _verify_aggregates(
    *, manifest: Mapping[str, Any], inventory: tuple[ProposalAsset, ...]
) -> tuple[AggregateVerification, ...]:
    raw_aggregates = manifest.get("aggregate_hashes")
    if not isinstance(raw_aggregates, Mapping):
        raise Tranche02FutureHeldoutFreezeError("manifest is missing aggregate_hashes")
    required = ("runtime_inputs", "expected_outcomes", "documentation", "all_non_manifest_assets")
    if set(raw_aggregates) != set(required):
        raise Tranche02FutureHeldoutFreezeError(
            "manifest aggregate_hashes must declare exactly runtime_inputs, expected_outcomes, documentation, and all_non_manifest_assets"
        )
    group_members = {
        "runtime_inputs": tuple(asset for asset in inventory if asset.asset_group == "runtime_inputs"),
        "expected_outcomes": tuple(asset for asset in inventory if asset.asset_group == "expected_outcomes"),
        "documentation": tuple(asset for asset in inventory if asset.asset_group == "documentation"),
        "all_non_manifest_assets": inventory,
    }
    report: list[AggregateVerification] = []
    for name in required:
        expected = raw_aggregates.get(name)
        if not isinstance(expected, str) or not _is_sha256(expected):
            raise Tranche02FutureHeldoutFreezeError(
                f"manifest aggregate {name} must be a lowercase SHA-256 string"
            )
        observed = _aggregate_hash(group_members[name])
        if observed != expected:
            raise Tranche02FutureHeldoutFreezeError(
                f"aggregate SHA-256 mismatch for {name}"
            )
        report.append(
            AggregateVerification(
                aggregate_name=name,
                expected_sha256=expected,
                observed_sha256=observed,
                formula="sha256_sorted_sha256_byte_count_relative_path_lines_v1",
            )
        )
    return tuple(report)


def _validate_manifest_declarations(
    *, manifest: Mapping[str, Any], inventory: tuple[ProposalAsset, ...]
) -> None:
    proposal = manifest.get("proposal")
    boundary = manifest.get("boundary_declarations")
    coverage = manifest.get("case_coverage")
    grounding = manifest.get("source_corpus_grounding")
    if not isinstance(proposal, Mapping) or not isinstance(boundary, Mapping):
        raise Tranche02FutureHeldoutFreezeError(
            "manifest is missing proposal or boundary_declarations"
        )
    if proposal.get("archive_root") != PROPOSAL_ROOT or proposal.get("proposal_status") != "not_frozen":
        raise Tranche02FutureHeldoutFreezeError(
            "manifest proposal root or not_frozen status is invalid"
        )
    required_true = (
        "not_frozen",
        "not_active_policy",
        "not_retrieval_evidence",
        "not_production_evidence",
        "not_procedure_authorization_evidence",
        "not_selector_calibration_material",
        "not_customer_data_validation",
        "runtime_inputs_are_outcome_free",
        "expected_reason_codes_are_evaluator_diagnostic_only",
    )
    missing_or_false = [key for key in required_true if boundary.get(key) is not True]
    if missing_or_false:
        raise Tranche02FutureHeldoutFreezeError(
            "manifest boundary declarations are invalid: " + ", ".join(missing_or_false)
        )
    accepted = manifest.get("accepted_case_ids")
    if accepted != list(EXPECTED_CASE_IDS):
        raise Tranche02FutureHeldoutFreezeError(
            "manifest accepted_case_ids must exactly match the 12 accepted V2 case IDs"
        )
    if not isinstance(coverage, Mapping) or set(coverage) != set(REQUIRED_COVERAGE_KEYS):
        raise Tranche02FutureHeldoutFreezeError(
            "manifest case_coverage does not match the accepted V2 coverage contract"
        )
    if coverage["candidate_order_reversal_pair"] != ["SEL-T02-FH-001", "SEL-T02-FH-002"]:
        raise Tranche02FutureHeldoutFreezeError("manifest order-reversal pair is invalid")
    if coverage["invalid_input_before_selector"] != ["SEL-T02-FH-011"]:
        raise Tranche02FutureHeldoutFreezeError("manifest invalid-input coverage is invalid")
    if coverage["cross_family_candidate_pool_rejection_before_selector"] != ["SEL-T02-FH-012"]:
        raise Tranche02FutureHeldoutFreezeError("manifest cross-family coverage is invalid")
    if not isinstance(grounding, Mapping):
        raise Tranche02FutureHeldoutFreezeError("manifest is missing source_corpus_grounding")
    if grounding.get("source_cards_mutated_by_proposal") != []:
        raise Tranche02FutureHeldoutFreezeError("proposal must not mutate source incident cards")
    source_hashes = grounding.get("source_card_hashes_referenced_by_accepted_assets")
    if not isinstance(source_hashes, Mapping) or not source_hashes:
        raise Tranche02FutureHeldoutFreezeError("manifest source-card hash declarations are invalid")
    if any(not isinstance(value, str) or not _is_sha256(value) for value in source_hashes.values()):
        raise Tranche02FutureHeldoutFreezeError("manifest source-card hashes must be SHA-256 strings")
    if len(inventory) != 27:
        raise Tranche02FutureHeldoutFreezeError("proposal asset inventory count is invalid")


def _load_runtime_cases(*, files: Mapping[str, bytes]) -> dict[str, _RuntimeCase]:
    cases: dict[str, _RuntimeCase] = {}
    for case_id in EXPECTED_CASE_IDS:
        path = f"{PROPOSAL_ROOT}/{RUNTIME_PREFIX}{case_id}.json"
        raw = _load_json(files[path], path)
        if FORBIDDEN_RUNTIME_KEYS & set(raw):
            leaked = ", ".join(sorted(FORBIDDEN_RUNTIME_KEYS & set(raw)))
            raise Tranche02FutureHeldoutFreezeError(
                f"runtime input contains evaluator-only outcome fields for {case_id}: {leaked}"
            )
        try:
            case = _RuntimeCase.model_validate(raw)
        except ValidationError as error:
            raise Tranche02FutureHeldoutFreezeError(
                f"runtime input has an invalid envelope for {case_id}"
            ) from error
        if case.case_id != case_id:
            raise Tranche02FutureHeldoutFreezeError(
                f"runtime filename and case_id differ for {case_id}"
            )
        if case.contract_version != "tranche-02-selection-v1":
            raise Tranche02FutureHeldoutFreezeError(
                f"runtime case uses an unsupported contract_version: {case_id}"
            )
        cases[case_id] = case
    return cases


def _load_expected_outcomes(*, files: Mapping[str, bytes]) -> dict[str, _ExpectedOutcome]:
    outcomes: dict[str, _ExpectedOutcome] = {}
    for case_id in EXPECTED_CASE_IDS:
        path = f"{PROPOSAL_ROOT}/{OUTCOME_PREFIX}{case_id}.json"
        try:
            outcome = _ExpectedOutcome.model_validate(_load_json(files[path], path))
        except ValidationError as error:
            raise Tranche02FutureHeldoutFreezeError(
                f"expected outcome is invalid for {case_id}"
            ) from error
        if outcome.case_id != case_id:
            raise Tranche02FutureHeldoutFreezeError(
                f"expected-outcome filename and case_id differ for {case_id}"
            )
        if outcome.expected_reason_codes.classification != "evaluator-diagnostic-only":
            raise Tranche02FutureHeldoutFreezeError(
                f"expected reason codes are not evaluator-diagnostic-only for {case_id}"
            )
        if "must not be loaded by runtime selector code" not in outcome.expected_reason_codes.non_runtime_notice:
            raise Tranche02FutureHeldoutFreezeError(
                f"expected reason-code non-runtime notice is missing for {case_id}"
            )
        outcomes[case_id] = outcome
    return outcomes


def _validate_runtime_outcome_separation(
    *, runtime_cases: Mapping[str, _RuntimeCase], expected_outcomes: Mapping[str, _ExpectedOutcome]
) -> None:
    if tuple(runtime_cases) != EXPECTED_CASE_IDS or tuple(expected_outcomes) != EXPECTED_CASE_IDS:
        raise Tranche02FutureHeldoutFreezeError(
            "runtime and expected-outcome sets must exactly match accepted V2 IDs"
        )
    for case_id in EXPECTED_CASE_IDS:
        runtime = runtime_cases[case_id]
        outcome = expected_outcomes[case_id]
        if runtime.case_id != outcome.case_id:
            raise Tranche02FutureHeldoutFreezeError(
                f"runtime/outcome case-id mismatch: {case_id}"
            )


def _validate_pre_selector_contracts(
    *,
    manifest: Mapping[str, Any],
    runtime_cases: Mapping[str, _RuntimeCase],
    expected_outcomes: Mapping[str, _ExpectedOutcome],
) -> tuple[PreSelectorCaseCheck, ...]:
    checks: list[PreSelectorCaseCheck] = []
    source_hashes = manifest["source_corpus_grounding"]["source_card_hashes_referenced_by_accepted_assets"]

    for case_id in EXPECTED_CASE_IDS:
        runtime = runtime_cases[case_id]
        outcome = expected_outcomes[case_id]
        _validate_source_grounding(
            runtime=runtime,
            outcome=outcome,
            manifest_source_hashes=source_hashes,
        )
        if len(set(runtime.candidate_incident_ids)) != len(runtime.candidate_incident_ids):
            raise Tranche02FutureHeldoutFreezeError(
                f"candidate_incident_ids repeat for {case_id}"
            )

        expected_validation = outcome.pre_selector_validation
        if expected_validation.expected_status == "valid":
            _validate_valid_runtime_case(runtime=runtime, outcome=outcome)
            checks.append(
                PreSelectorCaseCheck(
                    case_id=case_id,
                    expected_outcome_kind=outcome.expected_outcome_kind,
                    validation_status="valid",
                    validation_boundary="RepresentativeSelectionIntake_and_candidate_pool_shape",
                    selector_execution_permitted=True,
                )
            )
            continue

        check = _validate_intentionally_invalid_case(runtime=runtime, outcome=outcome)
        checks.append(check)

    _validate_order_reversal_pair(runtime_cases=runtime_cases, expected_outcomes=expected_outcomes)
    return tuple(checks)


def _validate_source_grounding(
    *,
    runtime: _RuntimeCase,
    outcome: _ExpectedOutcome,
    manifest_source_hashes: Mapping[str, Any],
) -> None:
    grounding_cards = outcome.source_grounding.source_cards
    source_ids = tuple(card.source_card_id for card in grounding_cards)
    if source_ids != runtime.candidate_incident_ids:
        raise Tranche02FutureHeldoutFreezeError(
            f"source-grounding card order must match runtime candidate order for {runtime.case_id}"
        )
    for card in grounding_cards:
        declared_hash = manifest_source_hashes.get(card.source_card_id)
        if declared_hash != card.source_card_sha256:
            raise Tranche02FutureHeldoutFreezeError(
                f"source-grounding SHA-256 does not match manifest for {runtime.case_id}/{card.source_card_id}"
            )


def _validate_valid_runtime_case(*, runtime: _RuntimeCase, outcome: _ExpectedOutcome) -> None:
    validation = outcome.pre_selector_validation
    if validation.must_pass_before_selector is not True or validation.selector_execution_permitted is not None:
        raise Tranche02FutureHeldoutFreezeError(
            f"valid case pre-selector declaration is invalid for {runtime.case_id}"
        )
    try:
        RepresentativeSelectionIntake.model_validate(runtime.selection_intake)
    except ValidationError as error:
        raise Tranche02FutureHeldoutFreezeError(
            f"valid case fails typed selection intake validation: {runtime.case_id}"
        ) from error
    families = {card.incident_family for card in outcome.source_grounding.source_cards}
    if len(families) != 1 or runtime.candidate_pool_family not in families:
        raise Tranche02FutureHeldoutFreezeError(
            f"valid case candidate pool is not one declared incident family: {runtime.case_id}"
        )
    if runtime.candidate_pool_family != "connection_pool_exhaustion":
        raise Tranche02FutureHeldoutFreezeError(
            f"valid selector case is outside current supported family: {runtime.case_id}"
        )
    if not all(card.selection_signature_present for card in outcome.source_grounding.source_cards):
        raise Tranche02FutureHeldoutFreezeError(
            f"valid selector case references an unprofiled candidate: {runtime.case_id}"
        )
    if outcome.expected_outcome_kind == "single_representative":
        if len(outcome.expected_representative_ids) != 1:
            raise Tranche02FutureHeldoutFreezeError(
                f"single representative outcome requires one representative: {runtime.case_id}"
            )
        if outcome.expected_non_dominated_ids != outcome.expected_representative_ids:
            raise Tranche02FutureHeldoutFreezeError(
                f"single representative outcome must have matching non-dominated set: {runtime.case_id}"
            )
    elif outcome.expected_outcome_kind == "explicit_tie":
        if outcome.expected_representative_ids or len(outcome.expected_non_dominated_ids) < 2:
            raise Tranche02FutureHeldoutFreezeError(
                f"explicit tie outcome is invalid: {runtime.case_id}"
            )
    else:
        raise Tranche02FutureHeldoutFreezeError(
            f"valid case cannot declare invalid_input outcome: {runtime.case_id}"
        )


def _validate_intentionally_invalid_case(
    *, runtime: _RuntimeCase, outcome: _ExpectedOutcome
) -> PreSelectorCaseCheck:
    validation = outcome.pre_selector_validation
    if outcome.expected_outcome_kind != "invalid_input":
        raise Tranche02FutureHeldoutFreezeError(
            f"invalid pre-selector case must use invalid_input outcome: {runtime.case_id}"
        )
    if (
        validation.must_pass_before_selector is not False
        or validation.selector_execution_permitted is not False
        or validation.expected_error_class is None
        or validation.validation_boundary is None
    ):
        raise Tranche02FutureHeldoutFreezeError(
            f"invalid case pre-selector declaration is incomplete: {runtime.case_id}"
        )
    if outcome.expected_representative_ids or outcome.expected_non_dominated_ids:
        raise Tranche02FutureHeldoutFreezeError(
            f"invalid case must not declare selector winners: {runtime.case_id}"
        )

    if runtime.case_id == "SEL-T02-FH-011":
        _validate_duplicate_signal_rejection(runtime=runtime, outcome=outcome)
    elif runtime.case_id == "SEL-T02-FH-012":
        _validate_cross_family_rejection(runtime=runtime, outcome=outcome)
    else:
        raise Tranche02FutureHeldoutFreezeError(
            f"unexpected invalid future-heldout case: {runtime.case_id}"
        )

    return PreSelectorCaseCheck(
        case_id=runtime.case_id,
        expected_outcome_kind=outcome.expected_outcome_kind,
        validation_status="invalid_expected",
        validation_boundary=validation.validation_boundary,
        expected_error_class=validation.expected_error_class,
        selector_execution_permitted=False,
    )


def _validate_duplicate_signal_rejection(*, runtime: _RuntimeCase, outcome: _ExpectedOutcome) -> None:
    validation = outcome.pre_selector_validation
    if (
        validation.validation_boundary != "RepresentativeSelectionIntake"
        or validation.expected_error_class != "duplicate_operational_signal_family"
    ):
        raise Tranche02FutureHeldoutFreezeError("FH-011 does not declare the accepted invalid-intake contract")
    try:
        RepresentativeSelectionIntake.model_validate(runtime.selection_intake)
    except ValidationError as error:
        if "must not repeat" not in str(error):
            raise Tranche02FutureHeldoutFreezeError(
                "FH-011 invalid intake failed for an unexpected validation reason"
            ) from error
        return
    raise Tranche02FutureHeldoutFreezeError(
        "FH-011 duplicate operational signal family was not rejected before selector execution"
    )


def _validate_cross_family_rejection(*, runtime: _RuntimeCase, outcome: _ExpectedOutcome) -> None:
    validation = outcome.pre_selector_validation
    if (
        validation.validation_boundary != "candidate_pool_family"
        or validation.expected_error_class != "cross_family_candidate_pool_rejected"
    ):
        raise Tranche02FutureHeldoutFreezeError("FH-012 does not declare the accepted cross-family contract")
    try:
        RepresentativeSelectionIntake.model_validate(runtime.selection_intake)
    except ValidationError as error:
        raise Tranche02FutureHeldoutFreezeError(
            "FH-012 typed intake must be valid before candidate-pool rejection"
        ) from error
    families = {card.incident_family for card in outcome.source_grounding.source_cards}
    if len(families) <= 1:
        raise Tranche02FutureHeldoutFreezeError(
            "FH-012 must contain a genuinely mixed-family candidate pool"
        )
    if runtime.candidate_pool_family not in families:
        raise Tranche02FutureHeldoutFreezeError(
            "FH-012 declared candidate_pool_family must name one member of the mixed pool"
        )


def _validate_order_reversal_pair(
    *, runtime_cases: Mapping[str, _RuntimeCase], expected_outcomes: Mapping[str, _ExpectedOutcome]
) -> None:
    first = runtime_cases["SEL-T02-FH-001"]
    second = runtime_cases["SEL-T02-FH-002"]
    if tuple(reversed(first.candidate_incident_ids)) != second.candidate_incident_ids:
        raise Tranche02FutureHeldoutFreezeError("FH-001/FH-002 are not exact candidate-order reversals")
    if (
        first.contract_version != second.contract_version
        or first.candidate_pool_family != second.candidate_pool_family
        or first.selection_intake != second.selection_intake
    ):
        raise Tranche02FutureHeldoutFreezeError(
            "FH-001/FH-002 differ beyond candidate serialization order"
        )
    first_outcome = expected_outcomes[first.case_id]
    second_outcome = expected_outcomes[second.case_id]
    if (
        first_outcome.expected_outcome_kind != second_outcome.expected_outcome_kind
        or first_outcome.expected_representative_ids != second_outcome.expected_representative_ids
        or first_outcome.expected_non_dominated_ids != second_outcome.expected_non_dominated_ids
    ):
        raise Tranche02FutureHeldoutFreezeError(
            "FH-001/FH-002 do not preserve the same evaluator oracle"
        )


def _build_freeze_manifest(
    *,
    archive: Path,
    archive_sha256: str,
    inventory: tuple[ProposalAsset, ...],
    aggregate_verifications: tuple[AggregateVerification, ...],
    runtime_cases: Mapping[str, _RuntimeCase],
    expected_outcomes: Mapping[str, _ExpectedOutcome],
    pre_selector_checks: tuple[PreSelectorCaseCheck, ...],
) -> FreezeAssetManifest:
    frozen_assets = tuple(
        FrozenAsset(
            relative_path=asset.path,
            byte_count=asset.byte_count,
            sha256=asset.sha256,
            asset_group=asset.asset_group,
        )
        for asset in inventory
        if asset.asset_group in {"runtime_inputs", "expected_outcomes"}
    )
    frozen_aggregates = {
        "runtime_inputs": _aggregate_hash(
            tuple(asset for asset in frozen_assets if asset.asset_group == "runtime_inputs")
        ),
        "expected_outcomes": _aggregate_hash(
            tuple(asset for asset in frozen_assets if asset.asset_group == "expected_outcomes")
        ),
        "all_frozen_assets": _aggregate_hash(frozen_assets),
    }
    return FreezeAssetManifest(
        frozen_at=datetime.now(UTC),
        source_proposal_archive_name=archive.name,
        source_proposal_archive_sha256=archive_sha256,
        source_acceptance_audit_path=ACCEPTANCE_AUDIT_RELATIVE_PATH.as_posix(),
        source_acceptance_decision="accepted_for_governed_future_tranche_freeze",
        accepted_case_ids=EXPECTED_CASE_IDS,
        runtime_case_count=len(runtime_cases),
        expected_outcome_count=len(expected_outcomes),
        source_archive_asset_count=len(inventory),
        source_aggregate_verifications=aggregate_verifications,
        frozen_asset_inventory=frozen_assets,
        frozen_aggregate_hashes=frozen_aggregates,
        pre_selector_checks=pre_selector_checks,
        non_claims=(
            "This is a frozen, test-only representative-selection evaluation tranche; it is not selector calibration material.",
            "This freeze does not run or activate representative selection and does not alter active policy, retrieval, procedures, or decision states.",
            "This freeze does not authorize procedure execution, production use, deployment, customer-data validation, or operational response decisions.",
        ),
    )


def _commit_freeze_and_receipts(
    *,
    root: Path,
    files: Mapping[str, bytes],
    destination: Path,
    freeze_manifest_bytes: bytes,
    json_report_path: Path,
    markdown_report_path: Path,
    report: Tranche02FutureHeldoutFreezeReport,
) -> None:
    """Stage all writes, then commit them only after validation has completed."""

    destination_parent = destination.parent
    destination_parent.mkdir(parents=True, exist_ok=True)
    json_report_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_report_path.parent.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    staged_destination = destination_parent / f".{destination.name}.staging-{token}"
    staged_json = json_report_path.with_name(f".{json_report_path.name}.staging-{token}")
    staged_markdown = markdown_report_path.with_name(
        f".{markdown_report_path.name}.staging-{token}"
    )
    try:
        staged_destination.mkdir(parents=False, exist_ok=False)
        for archive_relative_path, payload in files.items():
            if not archive_relative_path.startswith(f"{PROPOSAL_ROOT}/"):
                continue
            relative_path = archive_relative_path.removeprefix(f"{PROPOSAL_ROOT}/")
            if not (
                relative_path.startswith(RUNTIME_PREFIX)
                or relative_path.startswith(OUTCOME_PREFIX)
            ):
                continue
            target = staged_destination / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        (staged_destination / FREEZE_MANIFEST_FILENAME).write_bytes(freeze_manifest_bytes)
        staged_json.write_text(
            json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        staged_markdown.write_text(_render_markdown(report), encoding="utf-8")
        staged_destination.replace(destination)
        staged_json.replace(json_report_path)
        staged_markdown.replace(markdown_report_path)
    except Exception:
        shutil.rmtree(staged_destination, ignore_errors=True)
        staged_json.unlink(missing_ok=True)
        staged_markdown.unlink(missing_ok=True)
        raise


def _render_markdown(report: Tranche02FutureHeldoutFreezeReport) -> str:
    lines = [
        "# Tranche 02 Future-Held-Out Freeze Receipt",
        "",
        "## Decision",
        "",
        f"`{report.decision.value}`",
        "",
        "## Immutable source",
        "",
        f"- Archive: `{report.proposal_archive_name}`",
        f"- Archive SHA-256: `{report.proposal_archive_sha256}`",
        f"- Acceptance audit: `{report.acceptance_audit_path}`",
        f"- Frozen fixture path: `{report.frozen_fixture_path}`",
        f"- Freeze manifest: `{report.freeze_manifest_path}`",
        f"- Freeze manifest SHA-256: `{report.freeze_manifest_sha256}`",
        "",
        "## Verified contents",
        "",
        f"- Runtime selection inputs: `{report.runtime_case_count}`",
        f"- Evaluator-only expected outcomes: `{report.expected_outcome_count}`",
        f"- Source archive non-manifest assets: `{report.source_archive_asset_count}`",
        "",
        "## Pre-selector validation checks",
        "",
        "| Case | Outcome kind | Validation result | Boundary | Selector execution permitted |",
        "|---|---|---|---|---|",
    ]
    for check in report.pre_selector_checks:
        lines.append(
            "| "
            f"{check.case_id} | {check.expected_outcome_kind} | {check.validation_status} | "
            f"{check.validation_boundary} | {str(check.selector_execution_permitted).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Non-claims",
            "",
            *[f"- {claim}" for claim in report.non_claims],
            "",
        ]
    )
    return "\n".join(lines)


def _aggregate_hash(assets: tuple[ProposalAsset, ...] | tuple[FrozenAsset, ...]) -> str:
    lines = "".join(
        f"{asset.sha256}  {asset.byte_count}  {asset.path if isinstance(asset, ProposalAsset) else asset.relative_path}\n"
        for asset in sorted(
            assets,
            key=lambda asset: asset.path if isinstance(asset, ProposalAsset) else asset.relative_path,
        )
    )
    return _sha256_bytes(lines.encode("utf-8"))


def _load_json(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Tranche02FutureHeldoutFreezeError(f"invalid JSON for {label}") from error
    if not isinstance(value, dict):
        raise Tranche02FutureHeldoutFreezeError(f"JSON object required for {label}")
    return value


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)
