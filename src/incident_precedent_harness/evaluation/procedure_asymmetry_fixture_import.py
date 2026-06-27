"""Governed import for the accepted procedure-asymmetry fixture proposal.

This module validates a case-scoped, test-only proposal archive before copying it
into ``data/evals/procedure_asymmetry_fixture``. It never loads the active incident
corpus, retrieval, AntiAnchoringDecisionPolicy, or held-out fixtures.

The importer refuses to proceed unless archive topology, manifest inventory,
supported aggregate hashes, case-scoped controlled-card contracts, runtime/outcome
separation, provenance assertions, and the fixed selector oracle all validate first.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from incident_precedent_harness.decisions.strict_dominance_selection import (
    RepresentativeSelectionResult,
    StrictDominanceRepresentativeSelector,
)
from incident_precedent_harness.domain.incident_data import (
    HistoricalIncidentCard,
    RepresentativeSelectionIntake,
)

PROPOSAL_ROOT = "proposed_procedure_asymmetry_fixture"
TARGET_RELATIVE_PATH = Path("data") / "evals" / "procedure_asymmetry_fixture"
JSON_REPORT_RELATIVE_PATH = (
    Path("evidence_vault")
    / "reports"
    / "procedure-asymmetry-fixture-import.json"
)
MARKDOWN_REPORT_RELATIVE_PATH = (
    Path("docs")
    / "reports"
    / "procedure-asymmetry-fixture-import.md"
)

REQUIRED_DOCUMENT_PATHS = (
    "authoring_ledger.md",
    "rejected_case_ideas.md",
    "APPLY_MANIFEST.md",
)
REQUIRED_GOVERNANCE_PATHS = (
    "inputs/governance/procedure_asymmetry_governance.json",
    "inputs/governance/controlled_card_derivation_assertions.json",
)
EXPECTED_CASE_IDS = (
    "PAF-T02-001",
    "PAF-T02-002",
    "PAF-T02-003",
)
EXPECTED_WINNER_ID = "INC-014"
EXPECTED_PROCEDURE_FAVOURED_NONWINNER_ID = "INC-013"
REQUIRED_AGGREGATES = (
    "inputs_sha256",
    "expected_outcomes_sha256",
    "governance_sha256",
    "documentation_sha256",
    "all_non_manifest_assets_sha256",
)


class ProcedureAsymmetryFixtureImportError(RuntimeError):
    """Raised when a proposal archive cannot be safely validated or imported."""


class Selector(Protocol):
    """Minimal isolated selector interface used only after archive validation."""

    def select(
        self,
        *,
        intake: RepresentativeSelectionIntake,
        candidate_incident_ids: tuple[str, ...],
        incidents: tuple[HistoricalIncidentCard, ...],
    ) -> RepresentativeSelectionResult:
        """Return a non-authoritative representative-selection result."""


class FixtureImportDecision(str, Enum):
    """Result of the governed archive validation and isolated import."""

    IMPORTED_TEST_ONLY = "imported_test_only"
    REFUSED = "refused"


class FixtureAsset(BaseModel):
    """Manifest-backed integrity data for one non-manifest archive asset."""

    model_config = ConfigDict(extra="forbid")

    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(ge=0)
    group: str = Field(min_length=1)


class AggregateVerification(BaseModel):
    """One declared group hash and the supported formula that reproduced it."""

    model_config = ConfigDict(extra="forbid")

    aggregate_name: str
    expected_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    observed_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    formula: str


class ProcedureAsymmetryCaseOutcome(BaseModel):
    """Trace-safe isolated selector result for one accepted fixture case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^PAF-T02-[0-9]{3}$")
    candidate_incident_ids: tuple[str, ...] = Field(min_length=2)
    expected_state: str
    actual_state: str
    expected_representative_incident_ids: tuple[str, ...] = Field(min_length=1)
    actual_representative_incident_ids: tuple[str, ...] = Field(min_length=1)
    contract_matches: bool


class ProcedureAsymmetryFixtureImportReport(BaseModel):
    """Write-once receipt for a case-scoped, test-only fixture import."""

    model_config = ConfigDict(extra="forbid")

    report_kind: str = "procedure_asymmetry_fixture_import"
    generated_at: datetime
    decision: FixtureImportDecision
    proposal_archive_name: str
    proposal_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    proposal_root: str = PROPOSAL_ROOT
    non_manifest_asset_count: int = Field(ge=0)
    controlled_card_count: int = Field(ge=0)
    runtime_case_count: int = Field(ge=0)
    expected_outcome_count: int = Field(ge=0)
    derivation_assertion_count: int = Field(ge=0)
    aggregate_verifications: tuple[AggregateVerification, ...] = Field(min_length=1)
    outcomes: tuple[ProcedureAsymmetryCaseOutcome, ...] = Field(min_length=1)
    imported_fixture_path: str
    active_policy_changed: bool = False
    retrieval_loaded: bool = False
    heldout_loaded: bool = False
    selector_activation_claim: bool = False
    non_claims: tuple[str, ...] = Field(min_length=1)


def verify_and_import_procedure_asymmetry_fixture(
    *,
    repository_root: Path,
    proposal_archive: Path,
    selector: Selector | None = None,
) -> ProcedureAsymmetryFixtureImportReport:
    """Validate the accepted V2-style archive and import it only after all gates pass.

    The archive is treated as untrusted input. No destination path is created until
    every integrity, schema, separation, adversarial-oracle, and selector check has
    passed. This function intentionally never touches active-policy or held-out paths.
    """

    root = repository_root.resolve()
    archive = proposal_archive.resolve()
    if not archive.is_file():
        raise ProcedureAsymmetryFixtureImportError(
            f"proposal archive is missing: {archive}"
        )

    destination = root / TARGET_RELATIVE_PATH
    json_report = root / JSON_REPORT_RELATIVE_PATH
    markdown_report = root / MARKDOWN_REPORT_RELATIVE_PATH
    _ensure_write_once(destination=destination, json_report=json_report, markdown_report=markdown_report)

    files = _normalise_archive_layout(_read_archive(archive))
    root_files = _validate_archive_topology(files)
    manifest = _load_json(files[f"{PROPOSAL_ROOT}/manifest.json"], "manifest.json")
    inventory = _extract_inventory(manifest, root_files)
    _verify_inventory(files=files, inventory=inventory)
    aggregate_verifications = _verify_aggregates(manifest=manifest, inventory=inventory)

    controlled_card_sets = _load_controlled_card_sets(files)
    runtime_cases = _load_runtime_cases(files)
    expected_outcomes = _load_expected_outcomes(files)
    _validate_runtime_outcome_separation(runtime_cases=runtime_cases, expected_outcomes=expected_outcomes)
    derivation_assertion_count = _validate_derivation_assertions(
        payload=_load_json(
            files[f"{PROPOSAL_ROOT}/inputs/governance/controlled_card_derivation_assertions.json"],
            "controlled_card_derivation_assertions.json",
        ),
        controlled_card_sets=controlled_card_sets,
        files=files,
    )
    _validate_governance(
        payload=_load_json(
            files[f"{PROPOSAL_ROOT}/inputs/governance/procedure_asymmetry_governance.json"],
            "procedure_asymmetry_governance.json",
        )
    )

    outcomes = _evaluate_isolated_selector(
        controlled_card_sets=controlled_card_sets,
        runtime_cases=runtime_cases,
        expected_outcomes=expected_outcomes,
        selector=selector or StrictDominanceRepresentativeSelector(),
    )

    _copy_archive_assets(
        files=files,
        repository_root=root,
        destination=destination,
    )
    report = ProcedureAsymmetryFixtureImportReport(
        generated_at=datetime.now(UTC),
        decision=FixtureImportDecision.IMPORTED_TEST_ONLY,
        proposal_archive_name=archive.name,
        proposal_archive_sha256=_sha256_bytes(archive.read_bytes()),
        non_manifest_asset_count=len(inventory),
        controlled_card_count=sum(len(cards) for cards in controlled_card_sets.values()),
        runtime_case_count=len(runtime_cases),
        expected_outcome_count=len(expected_outcomes),
        derivation_assertion_count=derivation_assertion_count,
        aggregate_verifications=aggregate_verifications,
        outcomes=outcomes,
        imported_fixture_path=TARGET_RELATIVE_PATH.as_posix(),
        non_claims=(
            "This imports an isolated, test-only evaluation fixture; it does not add cards to data/incidents or procedures to data/procedures.",
            "This run does not load retrieval, held-out cases, or AntiAnchoringDecisionPolicy.",
            "The strict-dominance selector remains isolated and non-authoritative after this import.",
            "The report does not freeze Tranche 02, authorize selector activation, authorize procedures, or establish production or customer-data readiness.",
        ),
    )
    write_procedure_asymmetry_fixture_import_report(
        report=report,
        json_path=json_report,
        markdown_path=markdown_report,
    )
    return report


def write_procedure_asymmetry_fixture_import_report(
    *,
    report: ProcedureAsymmetryFixtureImportReport,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write the import receipt once and reject evidence overwrite."""

    existing = tuple(path for path in (json_path, markdown_path) if path.exists())
    if existing:
        rendered = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            "Procedure-asymmetry fixture import evidence already exists and will not "
            f"be overwritten: {rendered}."
        )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _read_archive(archive: Path) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(archive) as zip_file:
            names = tuple(zip_file.namelist())
            if len(names) != len(set(names)):
                raise ProcedureAsymmetryFixtureImportError(
                    "proposal archive contains duplicate member paths"
                )
            files: dict[str, bytes] = {}
            for name in names:
                path = PurePosixPath(name)
                if name.endswith("/"):
                    continue
                if path.is_absolute() or ".." in path.parts:
                    raise ProcedureAsymmetryFixtureImportError(
                        f"proposal archive contains an unsafe member path: {name}"
                    )
                files[name] = zip_file.read(name)
            return files
    except zipfile.BadZipFile as error:
        raise ProcedureAsymmetryFixtureImportError(
            "proposal archive is not a readable ZIP file"
        ) from error


def _normalise_archive_layout(files: Mapping[str, bytes]) -> dict[str, bytes]:
    """Accept one harmless packaging wrapper while preserving one fixture root.

    The accepted fixture identity is the byte content of assets underneath
    ``proposed_procedure_asymmetry_fixture/``. Some archive tools add exactly one
    outer folder named after the ZIP. This function strips that outer folder only
    when *every* non-directory member is underneath the same wrapper and then
    underneath the required fixture root. Any sibling files, multiple wrappers,
    or alternate roots remain a hard refusal.
    """

    direct_prefix = f"{PROPOSAL_ROOT}/"
    if files and all(path.startswith(direct_prefix) for path in files):
        return dict(files)

    wrappers: set[str] = set()
    for path in files:
        parts = PurePosixPath(path).parts
        if len(parts) < 3 or parts[1] != PROPOSAL_ROOT:
            raise ProcedureAsymmetryFixtureImportError(
                f"proposal archive must contain only the {PROPOSAL_ROOT}/ root "
                "or one wrapper directory containing that root"
            )
        wrappers.add(parts[0])

    if len(wrappers) != 1:
        raise ProcedureAsymmetryFixtureImportError(
            "proposal archive must use exactly one wrapper directory when the "
            f"{PROPOSAL_ROOT}/ root is not top-level"
        )

    wrapper = next(iter(wrappers))
    wrapper_prefix = f"{wrapper}/"
    normalised = {
        path.removeprefix(wrapper_prefix): payload
        for path, payload in files.items()
    }
    if not normalised or any(not path.startswith(direct_prefix) for path in normalised):
        raise ProcedureAsymmetryFixtureImportError(
            f"proposal archive must contain only the {PROPOSAL_ROOT}/ root"
        )
    return normalised


def _validate_archive_topology(files: Mapping[str, bytes]) -> dict[str, bytes]:
    prefix = f"{PROPOSAL_ROOT}/"
    if not files:
        raise ProcedureAsymmetryFixtureImportError("proposal archive is empty")
    if any(not path.startswith(prefix) for path in files):
        raise ProcedureAsymmetryFixtureImportError(
            f"proposal archive must contain only the {PROPOSAL_ROOT}/ root"
        )

    root_files = {
        path.removeprefix(prefix): payload
        for path, payload in files.items()
    }
    required = {
        "manifest.json",
        *REQUIRED_DOCUMENT_PATHS,
        *REQUIRED_GOVERNANCE_PATHS,
    }
    missing = sorted(required - set(root_files))
    if missing:
        raise ProcedureAsymmetryFixtureImportError(
            "proposal archive is missing required paths: " + ", ".join(missing)
        )

    runtime_paths = sorted(
        path for path in root_files if path.startswith("inputs/cases/") and path.endswith(".json")
    )
    outcome_paths = sorted(
        path for path in root_files if path.startswith("expected_outcomes/") and path.endswith(".json")
    )
    controlled_paths = sorted(
        path
        for path in root_files
        if path.startswith("inputs/controlled_cards/") and path.endswith(".json")
    )
    if len(root_files) != 16:
        raise ProcedureAsymmetryFixtureImportError(
            f"proposal archive must contain exactly 16 files; observed {len(root_files)}"
        )
    if len(runtime_paths) != 3 or len(outcome_paths) != 3 or len(controlled_paths) != 4:
        raise ProcedureAsymmetryFixtureImportError(
            "proposal archive requires exactly 3 runtime cases, 3 expected outcomes, "
            "and 4 controlled cards"
        )
    return root_files


def _extract_inventory(
    manifest: Mapping[str, Any],
    root_files: Mapping[str, bytes],
) -> tuple[FixtureAsset, ...]:
    """Normalise a manifest inventory from supported V2-compatible shapes.

    A manifest may expose entries as a list with path fields or as a mapping keyed
    by relative path. Every extracted entry must include a SHA-256 and byte count.
    The validator then requires exact agreement with all non-manifest archive files.
    """

    entries: list[FixtureAsset] = []

    def add_entry(path: object, metadata: object, group_hint: str | None = None) -> None:
        if not isinstance(path, str) or not isinstance(metadata, Mapping):
            return
        digest = _first_str(metadata, ("sha256", "sha256_hex", "digest_sha256"))
        byte_count = _first_int(metadata, ("byte_count", "bytes", "size_bytes"))
        group = _first_str(metadata, ("group", "asset_group", "category")) or group_hint
        if digest is None or byte_count is None or group is None:
            return
        relative_path = _normalise_manifest_path(path)
        try:
            entries.append(
                FixtureAsset(
                    relative_path=relative_path,
                    sha256=digest,
                    byte_count=byte_count,
                    group=group,
                )
            )
        except ValidationError as error:
            raise ProcedureAsymmetryFixtureImportError(
                f"manifest inventory entry is invalid for {path}"
            ) from error

    def walk(value: object, group_hint: str | None = None) -> None:
        if isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping):
                    path = _first_str(item, ("relative_path", "path", "file_path", "file"))
                    if path is not None:
                        add_entry(path, item, group_hint)
                    walk(item, group_hint)
            return
        if not isinstance(value, Mapping):
            return
        for key, item in value.items():
            next_group = str(key) if str(key) in {
                "inputs",
                "expected_outcomes",
                "governance",
                "documentation",
            } else group_hint
            if _looks_like_asset_path(str(key)) and isinstance(item, Mapping):
                add_entry(str(key), item, group_hint)
            walk(item, next_group)

    walk(manifest)
    by_path: dict[str, FixtureAsset] = {}
    for entry in entries:
        prior = by_path.get(entry.relative_path)
        if prior is not None and prior != entry:
            raise ProcedureAsymmetryFixtureImportError(
                f"manifest lists conflicting integrity metadata for {entry.relative_path}"
            )
        by_path[entry.relative_path] = entry

    expected_paths = set(root_files) - {"manifest.json"}
    observed_paths = set(by_path)
    if observed_paths != expected_paths:
        missing = sorted(expected_paths - observed_paths)
        unexpected = sorted(observed_paths - expected_paths)
        pieces: list[str] = []
        if missing:
            pieces.append("missing inventory entries: " + ", ".join(missing))
        if unexpected:
            pieces.append("unexpected inventory entries: " + ", ".join(unexpected))
        raise ProcedureAsymmetryFixtureImportError(
            "manifest inventory does not match the proposal archive; " + "; ".join(pieces)
        )
    if len(by_path) != 15:
        raise ProcedureAsymmetryFixtureImportError(
            f"manifest must inventory 15 non-manifest assets; observed {len(by_path)}"
        )
    return tuple(sorted(by_path.values(), key=lambda item: item.relative_path))


def _verify_inventory(
    *,
    files: Mapping[str, bytes],
    inventory: tuple[FixtureAsset, ...],
) -> None:
    for asset in inventory:
        archive_path = f"{PROPOSAL_ROOT}/{asset.relative_path}"
        payload = files.get(archive_path)
        if payload is None:
            raise ProcedureAsymmetryFixtureImportError(
                f"archive is missing manifest-listed asset: {asset.relative_path}"
            )
        # Digest is the primary raw-asset integrity identity. Verify it before
        # byte count so a tampered payload has one stable, content-specific
        # failure classification even when the mutation also changes length.
        if _sha256_bytes(payload) != asset.sha256:
            raise ProcedureAsymmetryFixtureImportError(
                f"SHA-256 mismatch for {asset.relative_path}"
            )
        if len(payload) != asset.byte_count:
            raise ProcedureAsymmetryFixtureImportError(
                f"byte count mismatch for {asset.relative_path}"
            )


def _verify_aggregates(
    *,
    manifest: Mapping[str, Any],
    inventory: tuple[FixtureAsset, ...],
) -> tuple[AggregateVerification, ...]:
    declared = _extract_declared_aggregates(manifest)
    missing = sorted(set(REQUIRED_AGGREGATES) - set(declared))
    if missing:
        raise ProcedureAsymmetryFixtureImportError(
            "manifest is missing required aggregate hashes: " + ", ".join(missing)
        )

    report: list[AggregateVerification] = []
    for name in REQUIRED_AGGREGATES:
        members = _aggregate_members(name=name, inventory=inventory)
        candidates = _aggregate_candidates(members)
        expected = declared[name]
        matches = [(formula, value) for formula, value in candidates.items() if value == expected]
        if len(matches) != 1:
            raise ProcedureAsymmetryFixtureImportError(
                f"aggregate hash could not be reproduced with one supported formula: {name}"
            )
        formula, observed = matches[0]
        report.append(
            AggregateVerification(
                aggregate_name=name,
                expected_sha256=expected,
                observed_sha256=observed,
                formula=formula,
            )
        )
    return tuple(report)


def _extract_declared_aggregates(manifest: Mapping[str, Any]) -> dict[str, str]:
    declared: dict[str, str] = {}

    def walk(value: object) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if key in REQUIRED_AGGREGATES and isinstance(item, str):
                    declared[key] = item
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(manifest)
    invalid = {
        name: value
        for name, value in declared.items()
        if not re_full_sha256(value)
    }
    if invalid:
        raise ProcedureAsymmetryFixtureImportError(
            "manifest aggregate hash values must be lowercase SHA-256 strings"
        )
    return declared


def _aggregate_members(
    *,
    name: str,
    inventory: tuple[FixtureAsset, ...],
) -> tuple[FixtureAsset, ...]:
    if name == "inputs_sha256":
        members = tuple(
            asset
            for asset in inventory
            if asset.relative_path.startswith("inputs/")
            and not asset.relative_path.startswith("inputs/governance/")
        )
    elif name == "expected_outcomes_sha256":
        members = tuple(
            asset
            for asset in inventory
            if asset.relative_path.startswith("expected_outcomes/")
        )
    elif name == "governance_sha256":
        members = tuple(
            asset
            for asset in inventory
            if asset.relative_path.startswith("inputs/governance/")
        )
    elif name == "documentation_sha256":
        members = tuple(
            asset
            for asset in inventory
            if asset.relative_path in REQUIRED_DOCUMENT_PATHS
        )
    elif name == "all_non_manifest_assets_sha256":
        members = inventory
    else:
        raise ProcedureAsymmetryFixtureImportError(
            f"unsupported aggregate name: {name}"
        )
    if not members:
        raise ProcedureAsymmetryFixtureImportError(
            f"aggregate {name} has no members"
        )
    return tuple(sorted(members, key=lambda item: item.relative_path))


def _aggregate_candidates(
    members: tuple[FixtureAsset, ...],
) -> dict[str, str]:
    """Compute approved, deterministic aggregate encodings.

    V2 aggregate hashes are computed from the exact path-sorted manifest inventory
    records. ``group`` is integrity-relevant because the declaration places each
    raw asset in a controlled aggregate domain. The previous implementation dropped
    that field before hashing, which made valid V2 manifests unreproducible and
    masked later, more diagnostic validation errors.

    The reduced v1 record form remains supported only for explicitly older
    proposals. Every candidate formula is deterministic and metadata-only; no raw
    content, selector behavior, or evaluation outcome participates in aggregate
    reconstruction.
    """

    full_inventory_records = [
        {
            "relative_path": member.relative_path,
            "sha256": member.sha256,
            "byte_count": member.byte_count,
            "group": member.group,
        }
        for member in members
    ]
    reduced_records = [
        {
            "relative_path": member.relative_path,
            "sha256": member.sha256,
            "byte_count": member.byte_count,
        }
        for member in members
    ]
    canonical_inventory_json = json.dumps(
        full_inventory_records,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    canonical_reduced_json = json.dumps(
        reduced_records,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    path_hash_bytes = "".join(
        f"{member.relative_path}\t{member.sha256}\t{member.byte_count}\n"
        for member in members
    ).encode("utf-8")
    path_hash = "".join(
        f"{member.relative_path}\t{member.sha256}\n"
        for member in members
    ).encode("utf-8")
    hashes_only = "".join(f"{member.sha256}\n" for member in members).encode("utf-8")
    return {
        "canonical_json_inventory_records_v2": _sha256_bytes(canonical_inventory_json),
        "canonical_json_records_v1": _sha256_bytes(canonical_reduced_json),
        "path_sha256_byte_count_lines_v1": _sha256_bytes(path_hash_bytes),
        "path_sha256_lines_v1": _sha256_bytes(path_hash),
        "sha256_lines_v1": _sha256_bytes(hashes_only),
    }


def _load_controlled_card_sets(
    files: Mapping[str, bytes],
) -> dict[str, tuple[HistoricalIncidentCard, ...]]:
    """Load controlled cards by declared case-scoped set.

    The accepted V2 fixture has duplicate incident IDs across two independent card
    sets. Collapsing them into one global map would silently replace the primary
    adversarial cards with the procedure-neutral control cards. The importer must
    preserve card-set identity and select exactly the set named by each runtime
    case before the isolated selector runs.
    """

    prefix = f"{PROPOSAL_ROOT}/inputs/controlled_cards/"
    grouped: dict[str, list[HistoricalIncidentCard]] = {}
    seen_identifiers: set[tuple[str, str]] = set()

    for path, payload in sorted(files.items()):
        if not (path.startswith(prefix) and path.endswith(".json")):
            continue
        relative = PurePosixPath(path.removeprefix(prefix))
        if len(relative.parts) != 2:
            raise ProcedureAsymmetryFixtureImportError(
                f"controlled card must be nested under exactly one card-set directory: {path}"
            )
        card_set_id, filename = relative.parts
        if not filename.endswith(".json"):
            raise ProcedureAsymmetryFixtureImportError(
                f"controlled card must use a JSON filename: {path}"
            )
        raw = _load_json(payload, path)
        try:
            card = HistoricalIncidentCard.model_validate(raw)
        except ValidationError as error:
            raise ProcedureAsymmetryFixtureImportError(
                f"controlled card is invalid: {path}"
            ) from error

        expected_filename = f"{card.incident_id}.json"
        if filename != expected_filename:
            raise ProcedureAsymmetryFixtureImportError(
                f"controlled-card filename does not match incident_id: {path}"
            )
        identity = (card_set_id, card.incident_id)
        if identity in seen_identifiers:
            raise ProcedureAsymmetryFixtureImportError(
                f"duplicate controlled card identity in one set: {card_set_id}/{card.incident_id}"
            )
        seen_identifiers.add(identity)
        grouped.setdefault(card_set_id, []).append(card)

    total_count = sum(len(cards) for cards in grouped.values())
    if total_count != 4 or set(grouped) != {
        "PAV-001-procedure-asymmetric",
        "PAV-002-procedure-neutral-control",
    }:
        raise ProcedureAsymmetryFixtureImportError(
            "accepted V2 fixture requires exactly four controlled cards in the "
            "PAV-001-procedure-asymmetric and PAV-002-procedure-neutral-control sets"
        )

    required_pair = {
        EXPECTED_PROCEDURE_FAVOURED_NONWINNER_ID,
        EXPECTED_WINNER_ID,
    }
    normalised: dict[str, tuple[HistoricalIncidentCard, ...]] = {}
    for card_set_id, cards in grouped.items():
        ids = {card.incident_id for card in cards}
        if ids != required_pair or len(cards) != 2:
            raise ProcedureAsymmetryFixtureImportError(
                f"{card_set_id} must contain exactly the accepted V2 adversarial pair "
                "INC-013 and INC-014"
            )
        normalised[card_set_id] = tuple(
            sorted(cards, key=lambda card: card.incident_id)
        )
    return normalised

def _load_runtime_cases(files: Mapping[str, bytes]) -> dict[str, Mapping[str, Any]]:
    cases: dict[str, Mapping[str, Any]] = {}
    for path, payload in sorted(files.items()):
        if not (
            path.startswith(f"{PROPOSAL_ROOT}/inputs/cases/")
            and path.endswith(".json")
        ):
            continue
        raw = _load_json(payload, path)
        case_id = _case_id(raw, path)
        if case_id in cases:
            raise ProcedureAsymmetryFixtureImportError(
                f"duplicate runtime case ID: {case_id}"
            )
        cases[case_id] = raw
    _require_case_set(cases, "runtime inputs")
    return cases


def _load_expected_outcomes(files: Mapping[str, bytes]) -> dict[str, Mapping[str, Any]]:
    outcomes: dict[str, Mapping[str, Any]] = {}
    for path, payload in sorted(files.items()):
        if not (
            path.startswith(f"{PROPOSAL_ROOT}/expected_outcomes/")
            and path.endswith(".json")
        ):
            continue
        raw = _load_json(payload, path)
        case_id = _case_id(raw, path)
        if case_id in outcomes:
            raise ProcedureAsymmetryFixtureImportError(
                f"duplicate expected outcome ID: {case_id}"
            )
        outcomes[case_id] = raw
    _require_case_set(outcomes, "expected outcomes")
    return outcomes


def _validate_runtime_outcome_separation(
    *,
    runtime_cases: Mapping[str, Mapping[str, Any]],
    expected_outcomes: Mapping[str, Mapping[str, Any]],
) -> None:
    forbidden_runtime_keys = {
        "expected_outcome",
        "expected_state",
        "expected_selection_state",
        "expected_representative_incident_ids",
        "representative_incident_ids",
    }
    forbidden_outcome_keys = {
        "selection_intake",
        "candidate_incident_ids",
        "candidate_pool_family",
    }
    for case_id, payload in runtime_cases.items():
        overlap = forbidden_runtime_keys & set(payload)
        if overlap:
            raise ProcedureAsymmetryFixtureImportError(
                f"{case_id} runtime input leaks expected outcome fields: {', '.join(sorted(overlap))}"
            )
        intake = payload.get("selection_intake")
        candidate_ids = payload.get("candidate_incident_ids")
        try:
            RepresentativeSelectionIntake.model_validate(intake)
        except ValidationError as error:
            raise ProcedureAsymmetryFixtureImportError(
                f"{case_id} has an invalid typed selection_intake"
            ) from error
        if not isinstance(candidate_ids, list) or len(candidate_ids) < 2:
            raise ProcedureAsymmetryFixtureImportError(
                f"{case_id} must provide at least two candidate_incident_ids"
            )
    for case_id, payload in expected_outcomes.items():
        overlap = forbidden_outcome_keys & set(payload)
        if overlap:
            raise ProcedureAsymmetryFixtureImportError(
                f"{case_id} expected outcome leaks runtime fields: {', '.join(sorted(overlap))}"
            )


def _validate_derivation_assertions(
    *,
    payload: Mapping[str, Any],
    controlled_card_sets: Mapping[str, tuple[HistoricalIncidentCard, ...]],
    files: Mapping[str, bytes],
) -> int:
    """Validate card-set-specific provenance assertions without loading source cards.

    The V2 proposal intentionally keeps source cards outside the import root. Each
    assertion therefore proves consistency against the imported controlled-card
    digest and records the audited source digest plus exact declared/observed
    difference fields. The acceptance audit remains the source-to-controlled
    comparison authority; this importer verifies that the approved assertion binds
    to the correct in-archive controlled variant.
    """

    assertions = payload.get("assertions") or payload.get("derivation_assertions")
    if not isinstance(assertions, list) or len(assertions) != 4:
        raise ProcedureAsymmetryFixtureImportError(
            "controlled-card derivation assertions must contain exactly four entries"
        )

    expected_identities = {
        (card_set_id, card.incident_id)
        for card_set_id, cards in controlled_card_sets.items()
        for card in cards
    }
    observed_identities: set[tuple[str, str]] = set()
    primary_assertion_validated = False

    for item in assertions:
        if not isinstance(item, Mapping):
            raise ProcedureAsymmetryFixtureImportError(
                "derivation assertions must be JSON objects"
            )
        assertion_id = _first_str(item, ("assertion_id", "id", "derivation_id"))
        card_set_id = _first_str(
            item,
            ("card_set_id", "controlled_card_set_id", "set_id"),
        )
        controlled_id = _first_str(
            item,
            (
                "controlled_incident_id",
                "controlled_card_id",
                "controlled_id",
            ),
        )
        allowed_fields = _first_str_sequence(
            item,
            (
                "allowed_perturbation_fields",
                "declared_perturbation_fields",
                "permitted_difference_fields",
            ),
        )
        actual_fields = _first_str_sequence(
            item,
            (
                "actual_changed_fields",
                "observed_changed_fields",
                "source_difference_fields",
            ),
        )
        source_digest = _first_str(
            item,
            ("source_card_sha256", "source_sha256", "source_digest_sha256"),
        )
        controlled_digest = _first_str(
            item,
            (
                "controlled_card_sha256",
                "controlled_sha256",
                "controlled_digest_sha256",
            ),
        )
        exact_match = item.get("exact_field_set_match")

        if (
            assertion_id is None
            or card_set_id is None
            or controlled_id is None
            or not allowed_fields
            or not actual_fields
            or source_digest is None
            or controlled_digest is None
            or exact_match is not True
        ):
            raise ProcedureAsymmetryFixtureImportError(
                "each derivation assertion must bind one controlled card, source and "
                "controlled digests, actual/declared changed fields, and exact equality"
            )
        if not re_full_sha256(source_digest) or not re_full_sha256(controlled_digest):
            raise ProcedureAsymmetryFixtureImportError(
                "derivation assertion digests must be lowercase SHA-256 strings"
            )
        identity = (card_set_id, controlled_id)
        if identity not in expected_identities or identity in observed_identities:
            raise ProcedureAsymmetryFixtureImportError(
                "derivation assertions must bind each controlled card exactly once"
            )
        if tuple(sorted(set(actual_fields))) != tuple(sorted(set(allowed_fields))):
            raise ProcedureAsymmetryFixtureImportError(
                f"derivation assertion field-set mismatch for {card_set_id}/{controlled_id}"
            )

        asset_path = (
            f"{PROPOSAL_ROOT}/inputs/controlled_cards/{card_set_id}/{controlled_id}.json"
        )
        payload_bytes = files.get(asset_path)
        if payload_bytes is None or _sha256_bytes(payload_bytes) != controlled_digest:
            raise ProcedureAsymmetryFixtureImportError(
                f"derivation assertion controlled-card digest mismatch for "
                f"{card_set_id}/{controlled_id}"
            )
        observed_identities.add(identity)

        if (
            assertion_id == "PAV-001"
            and card_set_id == "PAV-001-procedure-asymmetric"
            and controlled_id == EXPECTED_PROCEDURE_FAVOURED_NONWINNER_ID
        ):
            if "unsafe_procedure_ids" not in allowed_fields:
                raise ProcedureAsymmetryFixtureImportError(
                    "PAV-001 / INC-013 must explicitly declare unsafe_procedure_ids "
                    "as a governed perturbation"
                )
            primary_assertion_validated = True

    if observed_identities != expected_identities:
        raise ProcedureAsymmetryFixtureImportError(
            "derivation assertions do not cover the exact controlled-card set"
        )
    if not primary_assertion_validated:
        raise ProcedureAsymmetryFixtureImportError(
            "derivation assertions do not declare the required PAV-001 / INC-013 provenance control"
        )
    return len(assertions)

def _validate_governance(*, payload: Mapping[str, Any]) -> None:
    if not payload:
        raise ProcedureAsymmetryFixtureImportError(
            "procedure-asymmetry governance payload is empty"
        )
    text = json.dumps(payload, sort_keys=True)
    required_markers = (
        "procedure",
        "asymmetry",
        "test",
    )
    if not all(marker in text.lower() for marker in required_markers):
        raise ProcedureAsymmetryFixtureImportError(
            "procedure-asymmetry governance payload lacks required test-only design markers"
        )


def _evaluate_isolated_selector(
    *,
    controlled_card_sets: Mapping[str, tuple[HistoricalIncidentCard, ...]],
    runtime_cases: Mapping[str, Mapping[str, Any]],
    expected_outcomes: Mapping[str, Mapping[str, Any]],
    selector: Selector,
) -> tuple[ProcedureAsymmetryCaseOutcome, ...]:
    """Evaluate each runtime case against only its declared controlled-card set."""

    outcomes: list[ProcedureAsymmetryCaseOutcome] = []
    first_candidates: tuple[str, ...] | None = None
    second_candidates: tuple[str, ...] | None = None

    for case_id in EXPECTED_CASE_IDS:
        runtime = runtime_cases[case_id]
        outcome = expected_outcomes[case_id]
        intake = RepresentativeSelectionIntake.model_validate(runtime["selection_intake"])
        card_set_id = runtime.get("controlled_card_set_id")
        if not isinstance(card_set_id, str) or card_set_id not in controlled_card_sets:
            raise ProcedureAsymmetryFixtureImportError(
                f"{case_id} references an unknown controlled_card_set_id"
            )
        cards = controlled_card_sets[card_set_id]
        cards_by_id = {card.incident_id: card for card in cards}
        candidate_ids = tuple(str(value) for value in runtime["candidate_incident_ids"])
        if len(set(candidate_ids)) != len(candidate_ids):
            raise ProcedureAsymmetryFixtureImportError(
                f"{case_id} repeats candidate incident IDs"
            )
        if any(candidate_id not in cards_by_id for candidate_id in candidate_ids):
            raise ProcedureAsymmetryFixtureImportError(
                f"{case_id} references a candidate outside the declared controlled-card set"
            )

        expected_state, expected_ids = _expected_outcome(outcome, case_id)
        result = selector.select(
            intake=intake,
            candidate_incident_ids=candidate_ids,
            incidents=cards,
        )
        actual_state = result.selection_state.value
        actual_ids = tuple(result.representative_incident_ids)
        contract_matches = expected_state == actual_state and expected_ids == actual_ids
        outcomes.append(
            ProcedureAsymmetryCaseOutcome(
                case_id=case_id,
                candidate_incident_ids=candidate_ids,
                expected_state=expected_state,
                actual_state=actual_state,
                expected_representative_incident_ids=expected_ids,
                actual_representative_incident_ids=actual_ids,
                contract_matches=contract_matches,
            )
        )
        if case_id == "PAF-T02-001":
            first_candidates = candidate_ids
        elif case_id == "PAF-T02-002":
            second_candidates = candidate_ids

    if not all(outcome.contract_matches for outcome in outcomes):
        failed = ", ".join(
            outcome.case_id for outcome in outcomes if not outcome.contract_matches
        )
        raise ProcedureAsymmetryFixtureImportError(
            "isolated strict-dominance selector did not match the accepted V2 oracle: "
            + failed
        )
    if any(
        outcome.expected_state != "single_representative"
        or outcome.expected_representative_incident_ids != (EXPECTED_WINNER_ID,)
        for outcome in outcomes
    ):
        raise ProcedureAsymmetryFixtureImportError(
            "accepted V2 oracle requires a single representative INC-014 for all three cases"
        )
    if (
        first_candidates is None
        or second_candidates is None
        or second_candidates != tuple(reversed(first_candidates))
    ):
        raise ProcedureAsymmetryFixtureImportError(
            "PAF-T02-001 and PAF-T02-002 must form an exact reversed-order pair"
        )
    if first_candidates[0] != EXPECTED_PROCEDURE_FAVOURED_NONWINNER_ID:
        raise ProcedureAsymmetryFixtureImportError(
            "PAF-T02-001 must place the procedure-favoured non-winner INC-013 first"
        )
    return tuple(outcomes)

def _expected_outcome(payload: Mapping[str, Any], case_id: str) -> tuple[str, tuple[str, ...]]:
    nested = payload.get("expected_outcome")
    source: Mapping[str, Any] = nested if isinstance(nested, Mapping) else payload
    state = _first_str(
        source,
        (
            "state",
            "expected_state",
            "expected_selection_state",
            "expected_outcome_kind",
        ),
    )
    ids = _first_str_sequence(
        source,
        (
            "representative_incident_ids",
            "expected_representative_incident_ids",
            "expected_representative_ids",
        ),
    )
    if state is None or not ids:
        raise ProcedureAsymmetryFixtureImportError(
            f"{case_id} expected outcome lacks state or representative incident IDs"
        )
    return state, tuple(ids)


def _copy_archive_assets(
    *,
    files: Mapping[str, bytes],
    repository_root: Path,
    destination: Path,
) -> None:
    temporary = repository_root / ".tmp" / "procedure-asymmetry-fixture-import"
    shutil.rmtree(temporary, ignore_errors=True)
    try:
        for archive_path, payload in files.items():
            relative_path = Path(archive_path.removeprefix(f"{PROPOSAL_ROOT}/"))
            target = temporary / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(temporary), str(destination))
    except OSError as error:
        shutil.rmtree(temporary, ignore_errors=True)
        raise ProcedureAsymmetryFixtureImportError(
            "validated fixture archive could not be copied into its isolated destination"
        ) from error


def _ensure_write_once(
    *,
    destination: Path,
    json_report: Path,
    markdown_report: Path,
) -> None:
    existing = tuple(
        path for path in (destination, json_report, markdown_report) if path.exists()
    )
    if existing:
        rendered = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            "Procedure-asymmetry fixture import is write-once and cannot overwrite: "
            f"{rendered}"
        )


def _load_json(payload: bytes, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProcedureAsymmetryFixtureImportError(
            f"{label} is not valid UTF-8 JSON"
        ) from error
    if not isinstance(value, Mapping):
        raise ProcedureAsymmetryFixtureImportError(
            f"{label} must contain a JSON object"
        )
    return value


def _case_id(payload: Mapping[str, Any], label: str) -> str:
    case_id = _first_str(payload, ("case_id", "fixture_case_id", "eval_id"))
    if case_id is None or not re_case_id(case_id):
        raise ProcedureAsymmetryFixtureImportError(
            f"{label} lacks a valid PAF-T02 case ID"
        )
    return case_id


def _require_case_set(items: Mapping[str, object], label: str) -> None:
    if tuple(sorted(items)) != EXPECTED_CASE_IDS:
        raise ProcedureAsymmetryFixtureImportError(
            f"{label} must contain exactly: {', '.join(EXPECTED_CASE_IDS)}"
        )


def _normalise_manifest_path(path: str) -> str:
    cleaned = path.removeprefix(f"{PROPOSAL_ROOT}/").lstrip("/")
    pure = PurePosixPath(cleaned)
    if pure.is_absolute() or ".." in pure.parts or cleaned == "manifest.json":
        raise ProcedureAsymmetryFixtureImportError(
            f"manifest contains an unsafe or unsupported asset path: {path}"
        )
    return pure.as_posix()


def _looks_like_asset_path(value: str) -> bool:
    return value.endswith((".json", ".md")) and "/" in value


def _first_str(mapping: Mapping[str, Any], names: Iterable[str]) -> str | None:
    for name in names:
        value = mapping.get(name)
        if isinstance(value, str):
            return value
    return None


def _first_int(mapping: Mapping[str, Any], names: Iterable[str]) -> int | None:
    for name in names:
        value = mapping.get(name)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _first_str_sequence(
    mapping: Mapping[str, Any],
    names: Iterable[str],
) -> tuple[str, ...] | None:
    for name in names:
        value = mapping.get(name)
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return tuple(value)
        if isinstance(value, tuple) and all(isinstance(item, str) for item in value):
            return tuple(value)
    return None


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def re_full_sha256(value: str) -> bool:
    return bool(__import__("re").fullmatch(r"[a-f0-9]{64}", value))


def re_case_id(value: str) -> bool:
    return bool(__import__("re").fullmatch(r"PAF-T02-[0-9]{3}", value))


def _render_markdown(report: ProcedureAsymmetryFixtureImportReport) -> str:
    lines = [
        "# Procedure-Asymmetry Fixture Import",
        "",
        "## Scope",
        "",
        "This write-once receipt records validation and isolated import of the accepted "
        "test-only procedure-asymmetry fixture proposal.",
        "It does not load active policy, retrieval, held-out evaluation, or provider infrastructure.",
        "",
        "## Decision",
        "",
        f"**Decision: {report.decision.value.upper()}**",
        "",
        "## Integrity summary",
        "",
        f"- Proposal archive: `{report.proposal_archive_name}`",
        f"- Proposal archive SHA-256: `{report.proposal_archive_sha256}`",
        f"- Non-manifest assets verified: `{report.non_manifest_asset_count}`",
        f"- Controlled cards: `{report.controlled_card_count}`",
        f"- Runtime cases: `{report.runtime_case_count}`",
        f"- Expected outcomes: `{report.expected_outcome_count}`",
        f"- Derivation assertions: `{report.derivation_assertion_count}`",
        f"- Imported fixture path: `{report.imported_fixture_path}`",
        "",
        "## Aggregate verification",
        "",
        "| Aggregate | Formula | Result |",
        "|---|---|---|",
    ]
    for aggregate in report.aggregate_verifications:
        lines.append(
            f"| {aggregate.aggregate_name} | {aggregate.formula} | pass |"
        )
    lines.extend(
        [
            "",
            "## Isolated selector outcomes",
            "",
            "| Case | Expected | Actual | Result |",
            "|---|---|---|---|",
        ]
    )
    for outcome in report.outcomes:
        expected = (
            f"{outcome.expected_state}: "
            f"{', '.join(outcome.expected_representative_incident_ids)}"
        )
        actual = (
            f"{outcome.actual_state}: "
            f"{', '.join(outcome.actual_representative_incident_ids)}"
        )
        status = "pass" if outcome.contract_matches else "blocked"
        lines.append(f"| {outcome.case_id} | {expected} | {actual} | {status} |")
    lines.extend(["", "## Non-claims", ""])
    lines.extend(f"- {claim}" for claim in report.non_claims)
    lines.append("")
    return "\n".join(lines)
