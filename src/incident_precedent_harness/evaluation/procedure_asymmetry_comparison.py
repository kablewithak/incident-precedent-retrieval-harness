"""Write-once comparison harness for the imported procedure-asymmetry fixture.

This module evaluates the isolated, manifest-verified procedure-asymmetry fixture
under the standalone strict-dominance selector. It never reads the active incident
corpus, retrieval, held-out evaluations, or AntiAnchoringDecisionPolicy.

The harness proves one narrow regression boundary: typed representative selection
must remain stable when candidate order and governed procedure posture vary inside
the imported test-only fixture. A passing comparison remains insufficient to
activate the selector.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from incident_precedent_harness.decisions.strict_dominance_selection import (
    RepresentativeSelectionResult,
    StrictDominanceRepresentativeSelector,
)
from incident_precedent_harness.domain.incident_data import (
    HistoricalIncidentCard,
    RepresentativeSelectionIntake,
)

FIXTURE_RELATIVE_PATH = Path("data") / "evals" / "procedure_asymmetry_fixture"
IMPORT_RECEIPT_RELATIVE_PATH = (
    Path("evidence_vault") / "reports" / "procedure-asymmetry-fixture-import.json"
)
JSON_REPORT_RELATIVE_PATH = (
    Path("evidence_vault")
    / "reports"
    / "procedure-asymmetry-fixture-comparison.json"
)
MARKDOWN_REPORT_RELATIVE_PATH = (
    Path("docs")
    / "reports"
    / "procedure-asymmetry-fixture-comparison.md"
)
REQUIRED_DOCUMENT_PATHS = (
    "APPLY_MANIFEST.md",
    "authoring_ledger.md",
    "rejected_case_ideas.md",
)
EXPECTED_CASE_IDS = ("PAF-T02-001", "PAF-T02-002", "PAF-T02-003")
PRIMARY_CASE_ID = "PAF-T02-001"
ORDER_REVERSED_CASE_ID = "PAF-T02-002"
PROCEDURE_NEUTRAL_CASE_ID = "PAF-T02-003"
EXPECTED_WINNER_ID = "INC-014"
PROCEDURE_FAVOURED_NONWINNER_ID = "INC-013"


class ProcedureAsymmetryComparisonError(RuntimeError):
    """Raised when the imported fixture cannot be trusted for comparison."""


class ProcedureAsymmetryComparisonDecision(str, Enum):
    """Outcome for the isolated procedure-asymmetry comparison boundary."""

    COMPARISON_PASSED_ACTIVATION_BLOCKED = "comparison_passed_activation_blocked"
    COMPARISON_BLOCKED = "comparison_blocked"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class Selector(Protocol):
    """Minimal isolated selector protocol for deterministic comparison tests."""

    def select(
        self,
        *,
        intake: RepresentativeSelectionIntake,
        candidate_incident_ids: tuple[str, ...],
        incidents: tuple[HistoricalIncidentCard, ...],
    ) -> RepresentativeSelectionResult:
        """Return a non-authoritative representative-selection result."""


class AssetInventoryEntry(BaseModel):
    """One manifest-pinned imported fixture asset."""

    model_config = ConfigDict(extra="forbid")

    relative_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_count: int = Field(ge=0)
    group: str = Field(min_length=1)


class AcceptedCaseReference(BaseModel):
    """One manifest reference connecting runtime input and expected outcome."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^PAF-T02-[0-9]{3}$")
    input_path: str
    expected_outcome_path: str
    governance_path: str


class AggregateHashes(BaseModel):
    """Declared aggregate hashes for the imported fixture."""

    model_config = ConfigDict(extra="forbid")

    inputs_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_outcomes_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    governance_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    documentation_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    all_non_manifest_assets_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class V2RemediationBoundary(BaseModel):
    """V2 provenance boundary carried into the isolated imported fixture."""

    model_config = ConfigDict(extra="forbid")

    all_other_v1_assets_byte_identical: bool
    baseline_kind: str
    changed_or_new_paths: tuple[str, ...]


class ProcedureAsymmetryFixtureManifest(BaseModel):
    """Strict manifest contract for the accepted V2 test-only fixture."""

    model_config = ConfigDict(extra="forbid")

    accepted_cases: tuple[AcceptedCaseReference, ...]
    aggregate_hashes: AggregateHashes
    asset_inventory: tuple[AssetInventoryEntry, ...]
    fixture_contract_version: str
    governing_adr: str
    non_claims: tuple[str, ...]
    proposal_kind: str
    proposal_root: str
    proposal_version: str
    status: str
    v2_remediation_boundary: V2RemediationBoundary


class InputProvenance(BaseModel):
    """Provenance attached to one independent runtime input asset."""

    model_config = ConfigDict(extra="forbid")

    authored_by_role: str
    authoring_batch: str
    created_at_utc: datetime
    source_type: str


class ProcedureAsymmetryRuntimeCase(BaseModel):
    """Typed runtime input that deliberately excludes reviewer expected outcomes."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^PAF-T02-[0-9]{3}$")
    candidate_incident_ids: tuple[str, ...] = Field(min_length=2, max_length=4)
    candidate_pool_family: str
    case_design_tags: tuple[str, ...] = Field(min_length=1)
    contract_version: str
    controlled_card_set_id: str = Field(min_length=1)
    fixture_contract_version: str
    input_provenance: InputProvenance
    selection_intake: RepresentativeSelectionIntake
    source_incident_ids: tuple[str, ...] = Field(min_length=1)


class ProcedureAsymmetryExpectedOutcome(BaseModel):
    """Reviewer-controlled outcome, structurally separate from selector input."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^PAF-T02-[0-9]{3}$")
    expected_non_dominated_ids: tuple[str, ...] = Field(min_length=1)
    expected_outcome_kind: str
    expected_reason_codes: tuple[str, ...] = Field(min_length=1)
    expected_representative_ids: tuple[str, ...] = Field(min_length=1)
    reason_code_status: str
    review_rationale: str = Field(min_length=1)


class ImportReceiptOutcome(BaseModel):
    """One import-time selector result required by the comparison precondition."""

    model_config = ConfigDict(extra="ignore")

    case_id: str
    contract_matches: bool


class ImportReceipt(BaseModel):
    """Minimum import proof required before this comparison harness can run."""

    model_config = ConfigDict(extra="ignore")

    decision: str
    imported_fixture_path: str
    controlled_card_count: int
    runtime_case_count: int
    expected_outcome_count: int
    outcomes: tuple[ImportReceiptOutcome, ...]
    active_policy_changed: bool
    retrieval_loaded: bool
    heldout_loaded: bool
    selector_activation_claim: bool


class ProcedureAsymmetryComparisonOutcome(BaseModel):
    """One isolated selector result plus expected-outcome parity."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^PAF-T02-[0-9]{3}$")
    controlled_card_set_id: str
    candidate_incident_ids: tuple[str, ...]
    expected_state: str
    actual_state: str
    expected_representative_incident_ids: tuple[str, ...]
    actual_representative_incident_ids: tuple[str, ...]
    contract_matches: bool
    diagnostic_reason_codes: tuple[str, ...]


class ProcedureAsymmetryComparisonMetrics(BaseModel):
    """Bounded metrics for one isolated, non-authoritative comparison run."""

    model_config = ConfigDict(extra="forbid")

    imported_fixture_asset_count: int = Field(ge=0)
    runtime_case_count: int = Field(ge=0)
    expected_outcome_count: int = Field(ge=0)
    contract_pass_rate: float = Field(ge=0, le=1)
    order_invariance_passed: bool
    procedure_asymmetry_present: bool
    procedure_neutrality_passed: bool
    import_receipt_verified: bool
    active_policy_changed: bool = False
    retrieval_loaded: bool = False
    heldout_loaded: bool = False
    selector_activation_claim: bool = False
    failed_case_ids: tuple[str, ...]


class ProcedureAsymmetryComparisonReport(BaseModel):
    """Write-once evidence for the isolated procedure-asymmetry comparison."""

    model_config = ConfigDict(extra="forbid")

    report_kind: str = "procedure_asymmetry_fixture_comparison"
    generated_at: datetime
    fixture_contract_version: str
    comparison_decision: ProcedureAsymmetryComparisonDecision
    decision_reasons: tuple[str, ...] = Field(min_length=1)
    metrics: ProcedureAsymmetryComparisonMetrics
    outcomes: tuple[ProcedureAsymmetryComparisonOutcome, ...] = Field(min_length=1)
    activation_blockers: tuple[str, ...] = Field(min_length=1)
    non_claims: tuple[str, ...] = Field(min_length=1)


def run_procedure_asymmetry_fixture_comparison(
    *,
    repository_root: Path,
    selector: Selector | None = None,
) -> ProcedureAsymmetryComparisonReport:
    """Validate the imported fixture and compare all accepted cases.

    The import receipt proves an archive-level validation occurred before import.
    This harness re-verifies current on-disk fixture integrity so a later local edit
    cannot silently turn the imported fixture into comparison input.
    """

    root = repository_root.resolve()
    fixture_root = root / FIXTURE_RELATIVE_PATH
    import_receipt = _load_verified_import_receipt(root)
    manifest = _load_manifest(fixture_root)
    asset_payloads = _verify_imported_fixture_integrity(
        fixture_root=fixture_root,
        manifest=manifest,
    )
    runtime_cases = _load_runtime_cases(
        fixture_root=fixture_root,
        references=manifest.accepted_cases,
    )
    expected_outcomes = _load_expected_outcomes(
        fixture_root=fixture_root,
        references=manifest.accepted_cases,
    )
    _validate_runtime_outcome_separation(
        runtime_cases=runtime_cases,
        expected_outcomes=expected_outcomes,
    )
    controlled_card_sets = _load_controlled_card_sets(
        fixture_root=fixture_root,
        expected_asset_paths=set(asset_payloads),
    )
    outcomes = _evaluate_cases(
        selector=selector or StrictDominanceRepresentativeSelector(),
        runtime_cases=runtime_cases,
        expected_outcomes=expected_outcomes,
        controlled_card_sets=controlled_card_sets,
    )
    metrics = _build_metrics(
        import_receipt=import_receipt,
        manifest=manifest,
        asset_payloads=asset_payloads,
        runtime_cases=runtime_cases,
        expected_outcomes=expected_outcomes,
        controlled_card_sets=controlled_card_sets,
        outcomes=outcomes,
    )
    decision, reasons = _decide(metrics)
    return ProcedureAsymmetryComparisonReport(
        generated_at=datetime.now(UTC),
        fixture_contract_version=manifest.fixture_contract_version,
        comparison_decision=decision,
        decision_reasons=reasons,
        metrics=metrics,
        outcomes=outcomes,
        activation_blockers=(
            "The strict-dominance selector remains disconnected from AntiAnchoringDecisionPolicy.",
            "This fixture is a governed test-only adversarial control, not independent future held-out activation evidence.",
            "The fixture covers only connection_pool_exhaustion candidates and does not establish cross-family policy safety.",
            "Selector activation still requires a separate ADR, independently authored future held-out cases, policy integration review, and a promotion gate.",
        ),
        non_claims=(
            "This harness does not load the active incident corpus, retrieval, held-out cases, procedures, or AntiAnchoringDecisionPolicy.",
            "Expected reason codes are evaluator diagnostics; they are not supplied to the selector and are not a selector-output contract.",
            "A passing comparison does not freeze Tranche 02, activate representative selection, authorize procedures, or prove production or customer-data readiness.",
        ),
    )


def write_procedure_asymmetry_fixture_comparison_report(
    *,
    report: ProcedureAsymmetryComparisonReport,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write a comparison report once and reject any overwrite attempt."""

    existing = tuple(path for path in (json_path, markdown_path) if path.exists())
    if existing:
        raise FileExistsError(
            "Procedure-asymmetry comparison evidence already exists and will not be "
            "overwritten: " + ", ".join(str(path) for path in existing)
        )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _load_verified_import_receipt(repository_root: Path) -> ImportReceipt:
    receipt_path = repository_root / IMPORT_RECEIPT_RELATIVE_PATH
    payload = _read_json_path(receipt_path, label="procedure-asymmetry import receipt")
    try:
        receipt = ImportReceipt.model_validate(payload)
    except ValidationError as error:
        raise ProcedureAsymmetryComparisonError(
            "procedure-asymmetry import receipt does not satisfy the required comparison precondition"
        ) from error

    expected_path = FIXTURE_RELATIVE_PATH.as_posix()
    if receipt.decision != "imported_test_only":
        raise ProcedureAsymmetryComparisonError(
            "procedure-asymmetry import receipt is not an imported_test_only decision"
        )
    if receipt.imported_fixture_path != expected_path:
        raise ProcedureAsymmetryComparisonError(
            "procedure-asymmetry import receipt points to an unexpected fixture path"
        )
    if (
        receipt.controlled_card_count != 4
        or receipt.runtime_case_count != 3
        or receipt.expected_outcome_count != 3
        or tuple(outcome.case_id for outcome in receipt.outcomes) != EXPECTED_CASE_IDS
        or not all(outcome.contract_matches for outcome in receipt.outcomes)
    ):
        raise ProcedureAsymmetryComparisonError(
            "procedure-asymmetry import receipt does not prove the accepted V2 import contract"
        )
    if any(
        (
            receipt.active_policy_changed,
            receipt.retrieval_loaded,
            receipt.heldout_loaded,
            receipt.selector_activation_claim,
        )
    ):
        raise ProcedureAsymmetryComparisonError(
            "procedure-asymmetry import receipt violates the isolated test-only boundary"
        )
    return receipt


def _load_manifest(fixture_root: Path) -> ProcedureAsymmetryFixtureManifest:
    payload = _read_json_path(fixture_root / "manifest.json", label="fixture manifest")
    try:
        manifest = ProcedureAsymmetryFixtureManifest.model_validate(payload)
    except ValidationError as error:
        raise ProcedureAsymmetryComparisonError(
            "imported procedure-asymmetry fixture manifest is invalid"
        ) from error

    if manifest.proposal_root != "proposed_procedure_asymmetry_fixture":
        raise ProcedureAsymmetryComparisonError("fixture manifest has an unexpected proposal root")
    if manifest.proposal_version != "v2":
        raise ProcedureAsymmetryComparisonError("fixture manifest is not the accepted V2 contract")
    if manifest.fixture_contract_version != "procedure-asymmetry-adversarial-fixture-v2":
        raise ProcedureAsymmetryComparisonError(
            "fixture manifest has an unsupported fixture contract version"
        )
    if tuple(case.case_id for case in manifest.accepted_cases) != EXPECTED_CASE_IDS:
        raise ProcedureAsymmetryComparisonError(
            "fixture manifest accepted case IDs do not match the governed comparison set"
        )
    if len(manifest.asset_inventory) != 15:
        raise ProcedureAsymmetryComparisonError(
            "fixture manifest must inventory exactly 15 non-manifest assets"
        )
    return manifest


def _verify_imported_fixture_integrity(
    *,
    fixture_root: Path,
    manifest: ProcedureAsymmetryFixtureManifest,
) -> dict[str, bytes]:
    if not fixture_root.is_dir():
        raise ProcedureAsymmetryComparisonError(
            f"imported procedure-asymmetry fixture is missing: {fixture_root}"
        )
    inventory_by_path = {
        entry.relative_path: entry for entry in manifest.asset_inventory
    }
    if len(inventory_by_path) != len(manifest.asset_inventory):
        raise ProcedureAsymmetryComparisonError(
            "fixture manifest has duplicate asset inventory paths"
        )

    on_disk_paths = {
        path.relative_to(fixture_root).as_posix()
        for path in fixture_root.rglob("*")
        if path.is_file()
    }
    expected_paths = set(inventory_by_path) | {"manifest.json"}
    if on_disk_paths != expected_paths:
        missing = sorted(expected_paths - on_disk_paths)
        unexpected = sorted(on_disk_paths - expected_paths)
        details: list[str] = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if unexpected:
            details.append("unexpected: " + ", ".join(unexpected))
        raise ProcedureAsymmetryComparisonError(
            "imported fixture file set diverges from manifest inventory; " + "; ".join(details)
        )

    payloads: dict[str, bytes] = {}
    for relative_path, entry in inventory_by_path.items():
        payload = (fixture_root / relative_path).read_bytes()
        if _sha256_bytes(payload) != entry.sha256:
            raise ProcedureAsymmetryComparisonError(
                f"imported fixture SHA-256 mismatch for {relative_path}"
            )
        if len(payload) != entry.byte_count:
            raise ProcedureAsymmetryComparisonError(
                f"imported fixture byte count mismatch for {relative_path}"
            )
        payloads[relative_path] = payload

    _verify_aggregate_hashes(manifest=manifest)
    return payloads


def _verify_aggregate_hashes(*, manifest: ProcedureAsymmetryFixtureManifest) -> None:
    inventory = tuple(sorted(manifest.asset_inventory, key=lambda item: item.relative_path))
    groups: dict[str, tuple[AssetInventoryEntry, ...]] = {
        "inputs_sha256": tuple(
            entry
            for entry in inventory
            if entry.relative_path.startswith("inputs/")
            and not entry.relative_path.startswith("inputs/governance/")
        ),
        "expected_outcomes_sha256": tuple(
            entry
            for entry in inventory
            if entry.relative_path.startswith("expected_outcomes/")
        ),
        "governance_sha256": tuple(
            entry
            for entry in inventory
            if entry.relative_path.startswith("inputs/governance/")
        ),
        "documentation_sha256": tuple(
            entry for entry in inventory if entry.relative_path in REQUIRED_DOCUMENT_PATHS
        ),
        "all_non_manifest_assets_sha256": inventory,
    }
    declared = manifest.aggregate_hashes.model_dump()
    for aggregate_name, members in groups.items():
        if not members:
            raise ProcedureAsymmetryComparisonError(
                f"fixture manifest aggregate has no members: {aggregate_name}"
            )
        records = [
            {
                "relative_path": member.relative_path,
                "sha256": member.sha256,
                "byte_count": member.byte_count,
                "group": member.group,
            }
            for member in members
        ]
        observed = _sha256_bytes(
            json.dumps(records, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        if observed != declared[aggregate_name]:
            raise ProcedureAsymmetryComparisonError(
                f"imported fixture aggregate hash mismatch for {aggregate_name}"
            )


def _load_runtime_cases(
    *,
    fixture_root: Path,
    references: tuple[AcceptedCaseReference, ...],
) -> tuple[ProcedureAsymmetryRuntimeCase, ...]:
    cases: list[ProcedureAsymmetryRuntimeCase] = []
    for reference in references:
        payload = _read_json_path(fixture_root / reference.input_path, label=reference.input_path)
        _reject_expected_outcome_fields(payload=payload, label=reference.input_path)
        try:
            case = ProcedureAsymmetryRuntimeCase.model_validate(payload)
        except ValidationError as error:
            raise ProcedureAsymmetryComparisonError(
                f"invalid typed runtime case: {reference.input_path}"
            ) from error
        if case.case_id != reference.case_id:
            raise ProcedureAsymmetryComparisonError(
                f"runtime case ID does not match manifest reference: {reference.input_path}"
            )
        if case.candidate_pool_family != "connection_pool_exhaustion":
            raise ProcedureAsymmetryComparisonError(
                f"runtime case is outside selector family scope: {case.case_id}"
            )
        cases.append(case)
    return tuple(cases)


def _load_expected_outcomes(
    *,
    fixture_root: Path,
    references: tuple[AcceptedCaseReference, ...],
) -> tuple[ProcedureAsymmetryExpectedOutcome, ...]:
    outcomes: list[ProcedureAsymmetryExpectedOutcome] = []
    for reference in references:
        payload = _read_json_path(
            fixture_root / reference.expected_outcome_path,
            label=reference.expected_outcome_path,
        )
        try:
            outcome = ProcedureAsymmetryExpectedOutcome.model_validate(payload)
        except ValidationError as error:
            raise ProcedureAsymmetryComparisonError(
                f"invalid expected outcome: {reference.expected_outcome_path}"
            ) from error
        if outcome.case_id != reference.case_id:
            raise ProcedureAsymmetryComparisonError(
                "expected outcome ID does not match manifest reference: "
                f"{reference.expected_outcome_path}"
            )
        if outcome.reason_code_status != "evaluation_diagnostic_only_not_selector_contract":
            raise ProcedureAsymmetryComparisonError(
                "expected reason codes must remain evaluator diagnostics, not selector input"
            )
        outcomes.append(outcome)
    return tuple(outcomes)


def _reject_expected_outcome_fields(*, payload: object, label: str) -> None:
    if not isinstance(payload, Mapping):
        raise ProcedureAsymmetryComparisonError(f"runtime input is not a JSON object: {label}")
    forbidden = {
        "expected_outcome_kind",
        "expected_non_dominated_ids",
        "expected_representative_ids",
        "expected_reason_codes",
        "reason_code_status",
        "review_rationale",
    }
    present = sorted(forbidden & set(payload))
    if present:
        raise ProcedureAsymmetryComparisonError(
            f"runtime input leaks expected outcome fields in {label}: " + ", ".join(present)
        )


def _validate_runtime_outcome_separation(
    *,
    runtime_cases: tuple[ProcedureAsymmetryRuntimeCase, ...],
    expected_outcomes: tuple[ProcedureAsymmetryExpectedOutcome, ...],
) -> None:
    runtime_ids = tuple(case.case_id for case in runtime_cases)
    outcome_ids = tuple(outcome.case_id for outcome in expected_outcomes)
    if runtime_ids != EXPECTED_CASE_IDS or outcome_ids != EXPECTED_CASE_IDS:
        raise ProcedureAsymmetryComparisonError(
            "runtime and expected outcome cases must exactly match the governed case IDs"
        )


def _load_controlled_card_sets(
    *,
    fixture_root: Path,
    expected_asset_paths: set[str],
) -> dict[str, tuple[HistoricalIncidentCard, ...]]:
    prefix = "inputs/controlled_cards/"
    grouped: dict[str, list[HistoricalIncidentCard]] = {}
    for relative_path in sorted(expected_asset_paths):
        if not (relative_path.startswith(prefix) and relative_path.endswith(".json")):
            continue
        relative_parts = Path(relative_path).parts
        if len(relative_parts) != 4:
            raise ProcedureAsymmetryComparisonError(
                "controlled card path must have one case-scoped card-set directory: "
                f"{relative_path}"
            )
        _, _, card_set_id, _ = relative_parts
        payload = _read_json_path(fixture_root / relative_path, label=relative_path)
        try:
            card = HistoricalIncidentCard.model_validate(payload)
        except ValidationError as error:
            raise ProcedureAsymmetryComparisonError(
                f"invalid controlled incident card: {relative_path}"
            ) from error
        grouped.setdefault(card_set_id, []).append(card)

    required_sets = {
        "PAV-001-procedure-asymmetric",
        "PAV-002-procedure-neutral-control",
    }
    if set(grouped) != required_sets:
        raise ProcedureAsymmetryComparisonError(
            "controlled card sets do not match the governed procedure-asymmetry fixture"
        )
    normalized: dict[str, tuple[HistoricalIncidentCard, ...]] = {}
    for card_set_id, cards in grouped.items():
        identifiers = tuple(sorted(card.incident_id for card in cards))
        if identifiers != (PROCEDURE_FAVOURED_NONWINNER_ID, EXPECTED_WINNER_ID):
            raise ProcedureAsymmetryComparisonError(
                f"controlled card set has an unexpected candidate identity set: {card_set_id}"
            )
        normalized[card_set_id] = tuple(sorted(cards, key=lambda card: card.incident_id))
    return normalized


def _evaluate_cases(
    *,
    selector: Selector,
    runtime_cases: tuple[ProcedureAsymmetryRuntimeCase, ...],
    expected_outcomes: tuple[ProcedureAsymmetryExpectedOutcome, ...],
    controlled_card_sets: Mapping[str, tuple[HistoricalIncidentCard, ...]],
) -> tuple[ProcedureAsymmetryComparisonOutcome, ...]:
    expected_by_case_id = {outcome.case_id: outcome for outcome in expected_outcomes}
    results: list[ProcedureAsymmetryComparisonOutcome] = []
    for case in runtime_cases:
        cards = controlled_card_sets.get(case.controlled_card_set_id)
        if cards is None:
            raise ProcedureAsymmetryComparisonError(
                f"runtime case references an unknown controlled card set: {case.case_id}"
            )
        expected = expected_by_case_id[case.case_id]
        result = selector.select(
            intake=case.selection_intake,
            candidate_incident_ids=case.candidate_incident_ids,
            incidents=cards,
        )
        expected_ids = tuple(expected.expected_representative_ids)
        actual_ids = tuple(result.representative_incident_ids)
        expected_state = expected.expected_outcome_kind
        actual_state = result.selection_state.value
        results.append(
            ProcedureAsymmetryComparisonOutcome(
                case_id=case.case_id,
                controlled_card_set_id=case.controlled_card_set_id,
                candidate_incident_ids=case.candidate_incident_ids,
                expected_state=expected_state,
                actual_state=actual_state,
                expected_representative_incident_ids=expected_ids,
                actual_representative_incident_ids=actual_ids,
                contract_matches=(
                    expected_state == actual_state and expected_ids == actual_ids
                ),
                diagnostic_reason_codes=expected.expected_reason_codes,
            )
        )
    return tuple(results)


def _build_metrics(
    *,
    import_receipt: ImportReceipt,
    manifest: ProcedureAsymmetryFixtureManifest,
    asset_payloads: Mapping[str, bytes],
    runtime_cases: tuple[ProcedureAsymmetryRuntimeCase, ...],
    expected_outcomes: tuple[ProcedureAsymmetryExpectedOutcome, ...],
    controlled_card_sets: Mapping[str, tuple[HistoricalIncidentCard, ...]],
    outcomes: tuple[ProcedureAsymmetryComparisonOutcome, ...],
) -> ProcedureAsymmetryComparisonMetrics:
    outcome_by_id = {outcome.case_id: outcome for outcome in outcomes}
    case_by_id = {case.case_id: case for case in runtime_cases}
    primary = outcome_by_id[PRIMARY_CASE_ID]
    order_reversed = outcome_by_id[ORDER_REVERSED_CASE_ID]
    neutral = outcome_by_id[PROCEDURE_NEUTRAL_CASE_ID]
    primary_case = case_by_id[PRIMARY_CASE_ID]
    reversed_case = case_by_id[ORDER_REVERSED_CASE_ID]

    primary_cards = {
        card.incident_id: card
        for card in controlled_card_sets[primary_case.controlled_card_set_id]
    }
    neutral_cards = {
        card.incident_id: card
        for card in controlled_card_sets[
            case_by_id[PROCEDURE_NEUTRAL_CASE_ID].controlled_card_set_id
        ]
    }

    procedure_asymmetry_present = _procedure_asymmetry_present(primary_cards)
    procedure_neutrality_passed = _procedure_neutrality_passed(
        primary_cards=primary_cards,
        neutral_cards=neutral_cards,
        primary=primary,
        neutral=neutral,
    )
    order_invariance_passed = (
        reversed_case.candidate_incident_ids
        == tuple(reversed(primary_case.candidate_incident_ids))
        and reversed_case.selection_intake == primary_case.selection_intake
        and primary.actual_state == order_reversed.actual_state
        and primary.actual_representative_incident_ids
        == order_reversed.actual_representative_incident_ids
        and primary.contract_matches
        and order_reversed.contract_matches
    )
    failed_case_ids = tuple(
        outcome.case_id for outcome in outcomes if not outcome.contract_matches
    )
    return ProcedureAsymmetryComparisonMetrics(
        imported_fixture_asset_count=len(asset_payloads),
        runtime_case_count=len(runtime_cases),
        expected_outcome_count=len(expected_outcomes),
        contract_pass_rate=_ratio(
            len(outcomes) - len(failed_case_ids),
            len(outcomes),
        ),
        order_invariance_passed=order_invariance_passed,
        procedure_asymmetry_present=procedure_asymmetry_present,
        procedure_neutrality_passed=procedure_neutrality_passed,
        import_receipt_verified=(
            import_receipt.decision == "imported_test_only"
            and import_receipt.imported_fixture_path == FIXTURE_RELATIVE_PATH.as_posix()
        ),
        failed_case_ids=failed_case_ids,
    )


def _procedure_asymmetry_present(
    cards: Mapping[str, HistoricalIncidentCard],
) -> bool:
    procedure_favoured = cards[PROCEDURE_FAVOURED_NONWINNER_ID]
    typed_winner = cards[EXPECTED_WINNER_ID]
    return bool(
        set(procedure_favoured.linked_procedure_ids)
        - set(typed_winner.linked_procedure_ids)
    ) and bool(
        set(procedure_favoured.safe_procedure_ids)
        - set(typed_winner.safe_procedure_ids)
    ) and bool(
        set(typed_winner.unsafe_procedure_ids)
        - set(procedure_favoured.unsafe_procedure_ids)
    )


def _procedure_neutrality_passed(
    *,
    primary_cards: Mapping[str, HistoricalIncidentCard],
    neutral_cards: Mapping[str, HistoricalIncidentCard],
    primary: ProcedureAsymmetryComparisonOutcome,
    neutral: ProcedureAsymmetryComparisonOutcome,
) -> bool:
    typed_signatures_match = all(
        primary_cards[incident_id].selection_signature
        == neutral_cards[incident_id].selection_signature
        for incident_id in (PROCEDURE_FAVOURED_NONWINNER_ID, EXPECTED_WINNER_ID)
    )
    procedure_posture_changed = any(
        _procedure_posture(primary_cards[incident_id])
        != _procedure_posture(neutral_cards[incident_id])
        for incident_id in (PROCEDURE_FAVOURED_NONWINNER_ID, EXPECTED_WINNER_ID)
    )
    return (
        typed_signatures_match
        and procedure_posture_changed
        and primary.actual_state == neutral.actual_state
        and primary.actual_representative_incident_ids
        == neutral.actual_representative_incident_ids
        and primary.contract_matches
        and neutral.contract_matches
    )


def _procedure_posture(card: HistoricalIncidentCard) -> tuple[tuple[str, ...], ...]:
    return (
        tuple(sorted(card.linked_procedure_ids)),
        tuple(sorted(card.safe_procedure_ids)),
        tuple(sorted(card.unsafe_procedure_ids)),
    )


def _decide(
    metrics: ProcedureAsymmetryComparisonMetrics,
) -> tuple[ProcedureAsymmetryComparisonDecision, tuple[str, ...]]:
    if not metrics.import_receipt_verified:
        return (
            ProcedureAsymmetryComparisonDecision.INSUFFICIENT_EVIDENCE,
            ("The required write-once import receipt could not be verified.",),
        )
    blockers: list[str] = []
    if metrics.contract_pass_rate < 1.0:
        blockers.append("One or more isolated fixture cases failed exact outcome parity.")
    if not metrics.order_invariance_passed:
        blockers.append(
            "The primary and reversed-order cases did not preserve the same selected representative."
        )
    if not metrics.procedure_asymmetry_present:
        blockers.append(
            "The imported primary card set does not prove the required procedure-asymmetry precondition."
        )
    if not metrics.procedure_neutrality_passed:
        blockers.append(
            "The procedure-asymmetric and procedure-neutral card sets did not preserve the same typed-selection outcome."
        )
    if blockers:
        return ProcedureAsymmetryComparisonDecision.COMPARISON_BLOCKED, tuple(blockers)

    return (
        ProcedureAsymmetryComparisonDecision.COMPARISON_PASSED_ACTIVATION_BLOCKED,
        (
            "All three isolated fixture cases matched their reviewer-controlled expected outcomes.",
            "The reversed candidate order preserved the primary selected representative.",
            "Procedure posture changed between the adversarial and neutral card sets while the typed-selection outcome remained stable.",
            "Activation remains blocked because this is governed test-only evidence, not policy-integrated independent held-out evidence.",
        ),
    )


def _render_markdown(report: ProcedureAsymmetryComparisonReport) -> str:
    metrics = report.metrics
    lines = [
        "# Procedure-Asymmetry Fixture Comparison",
        "",
        "## Scope",
        "",
        "This write-once report re-verifies the imported test-only fixture and evaluates only the standalone strict-dominance selector.",
        "It does not load the active incident corpus, retrieval, held-out cases, procedures, or AntiAnchoringDecisionPolicy.",
        "",
        "## Decision",
        "",
        f"**Decision: {report.comparison_decision.value.upper()}**",
        "",
        "### Decision reasons",
        "",
    ]
    lines.extend(f"- {reason}" for reason in report.decision_reasons)
    lines.extend(
        [
            "",
            "## Comparison metrics",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Manifest-verified imported assets | {metrics.imported_fixture_asset_count} |",
            f"| Runtime cases | {metrics.runtime_case_count} |",
            f"| Expected outcomes | {metrics.expected_outcome_count} |",
            f"| Exact outcome contract pass rate | {metrics.contract_pass_rate} |",
            f"| Candidate-order invariance | {str(metrics.order_invariance_passed).lower()} |",
            f"| Procedure asymmetry present | {str(metrics.procedure_asymmetry_present).lower()} |",
            f"| Procedure-neutral control parity | {str(metrics.procedure_neutrality_passed).lower()} |",
            f"| Import receipt verified | {str(metrics.import_receipt_verified).lower()} |",
            "| Active policy changed | false |",
            "| Retrieval loaded | false |",
            "| Held-out loaded | false |",
            "| Selector activation claimed | false |",
            "",
            "## Case outcomes",
            "",
            "| Case | Card set | Expected | Actual | Contract |",
            "|---|---|---|---|---|",
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
        contract = "pass" if outcome.contract_matches else "blocked"
        lines.append(
            f"| {outcome.case_id} | {outcome.controlled_card_set_id} | "
            f"{expected} | {actual} | {contract} |"
        )
    lines.extend(["", "## Activation blockers", ""])
    lines.extend(f"- {blocker}" for blocker in report.activation_blockers)
    lines.extend(["", "## Non-claims", ""])
    lines.extend(f"- {claim}" for claim in report.non_claims)
    lines.append("")
    return "\n".join(lines)


def _read_json_path(path: Path, *, label: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ProcedureAsymmetryComparisonError(f"{label} is missing: {path}") from error
    except json.JSONDecodeError as error:
        raise ProcedureAsymmetryComparisonError(f"{label} is not valid JSON: {path}") from error


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0
