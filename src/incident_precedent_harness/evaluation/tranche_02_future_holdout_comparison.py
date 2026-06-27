"""Write-once comparison gate for frozen future-held-out Tranche 02.

The gate consumes only the immutable Tranche 02 fixture, its freeze manifest and
freeze receipt, plus the exact source-card bytes declared by evaluator-only
grounding records. It executes the isolated strict-dominance selector only for
the ten cases whose frozen contracts explicitly permit selector execution.

It does not import the active AntiAnchoringDecisionPolicy, retrieval, procedures,
Tranche 01 evaluation assets, or the procedure-asymmetry fixture. A passing
comparison remains activation-blocked because policy integration and a separate
activation decision are outside this boundary.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from incident_precedent_harness.decisions.strict_dominance_selection import (
    RepresentativeSelectionResult,
    RepresentativeSelectionState,
    StrictDominanceRepresentativeSelector,
)
from incident_precedent_harness.domain.incident_data import (
    HistoricalIncidentCard,
    RepresentativeSelectionIntake,
)

FROZEN_FIXTURE_RELATIVE_PATH = (
    Path("data") / "evals" / "heldout" / "tranche_02_future_heldout"
)
FREEZE_MANIFEST_FILENAME = "TRANCHE_02_FUTURE_HELDOUT_FREEZE_MANIFEST.json"
FREEZE_RECEIPT_RELATIVE_PATH = (
    Path("evidence_vault") / "reports" / "tranche-02-future-heldout-freeze.json"
)
JSON_REPORT_RELATIVE_PATH = (
    Path("evidence_vault") / "reports" / "tranche-02-future-heldout-comparison.json"
)
MARKDOWN_REPORT_RELATIVE_PATH = (
    Path("docs") / "reports" / "tranche-02-future-heldout-comparison.md"
)
EXPECTED_CASE_IDS = tuple(f"SEL-T02-FH-{number:03d}" for number in range(1, 13))
VALID_SELECTOR_CASE_IDS = EXPECTED_CASE_IDS[:10]
PRE_SELECTOR_REJECTION_CASE_IDS = EXPECTED_CASE_IDS[10:]
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


class Tranche02FutureHeldoutComparisonError(RuntimeError):
    """Raised when frozen Tranche 02 evidence cannot be trusted for comparison."""


class Tranche02FutureHeldoutComparisonDecision(str, Enum):
    """Decisions produced by this isolated comparison gate."""

    COMPARISON_PASSED_ACTIVATION_BLOCKED = "comparison_passed_activation_blocked"
    COMPARISON_BLOCKED = "comparison_blocked"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class Selector(Protocol):
    """Minimal protocol for the isolated representative selector."""

    def select(
        self,
        *,
        intake: RepresentativeSelectionIntake,
        candidate_incident_ids: tuple[str, ...],
        incidents: tuple[HistoricalIncidentCard, ...],
    ) -> RepresentativeSelectionResult:
        """Return a deterministic representative-selection result."""


class FrozenAsset(BaseModel):
    """One manifest-pinned frozen runtime or evaluator-only asset."""

    model_config = ConfigDict(extra="forbid")

    relative_path: str = Field(min_length=1)
    byte_count: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    asset_group: str = Field(pattern=r"^(runtime_inputs|expected_outcomes)$")


class PreSelectorCaseCheck(BaseModel):
    """A pre-selector check recorded by the governed freeze operation."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^SEL-T02-FH-[0-9]{3}$")
    expected_outcome_kind: str
    validation_status: str = Field(pattern=r"^(valid|invalid_expected)$")
    validation_boundary: str
    expected_error_class: str | None = None
    selector_execution_permitted: bool


class FreezeManifest(BaseModel):
    """Subset of the immutable freeze manifest required by this gate."""

    model_config = ConfigDict(extra="ignore")

    manifest_kind: str
    freeze_status: str
    source_acceptance_decision: str
    accepted_case_ids: tuple[str, ...]
    runtime_case_count: int
    expected_outcome_count: int
    source_archive_asset_count: int
    frozen_asset_inventory: tuple[FrozenAsset, ...]
    frozen_aggregate_hashes: dict[str, str]
    pre_selector_checks: tuple[PreSelectorCaseCheck, ...]
    selector_loaded: bool
    active_policy_loaded: bool
    retrieval_loaded: bool
    procedures_loaded: bool
    existing_heldout_loaded: bool
    procedure_asymmetry_fixture_loaded: bool
    selector_activation_authorized: bool


class FreezeReceipt(BaseModel):
    """Write-once receipt proving that this exact fixture was governedly frozen."""

    model_config = ConfigDict(extra="ignore")

    report_kind: str
    decision: str
    frozen_fixture_path: str
    freeze_manifest_path: str
    freeze_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    runtime_case_count: int
    expected_outcome_count: int
    source_archive_asset_count: int
    selector_loaded: bool
    active_policy_loaded: bool
    retrieval_loaded: bool
    selector_activation_authorized: bool


class FrozenRuntimeCase(BaseModel):
    """Runtime input deliberately separated from evaluator-controlled outcomes."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^SEL-T02-FH-[0-9]{3}$")
    contract_version: str
    selection_intake: dict[str, Any]
    candidate_incident_ids: tuple[str, ...] = Field(min_length=2, max_length=4)
    candidate_pool_family: str


class PreSelectorValidation(BaseModel):
    """Evaluator-only declaration of whether selector execution is permitted."""

    model_config = ConfigDict(extra="forbid")

    must_pass_before_selector: bool
    expected_status: str = Field(pattern=r"^(valid|invalid)$")
    validation_boundary: str | None = None
    expected_error_class: str | None = None
    selector_execution_permitted: bool | None = None


class GroundingCard(BaseModel):
    """One exact source-card declaration used to make a frozen case reproducible."""

    model_config = ConfigDict(extra="forbid")

    source_card_id: str = Field(pattern=r"^INC-[0-9]{3}$")
    source_card_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    incident_family: str
    selection_signature_present: bool


class SourceGrounding(BaseModel):
    """Evaluator-only source-card grounding for one frozen case."""

    model_config = ConfigDict(extra="forbid")

    source_corpus: str
    source_cards: tuple[GroundingCard, ...] = Field(min_length=2)
    grounding_note: str


class ExpectedOutcome(BaseModel):
    """Evaluator-controlled oracle; never supplied to selector runtime."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^SEL-T02-FH-[0-9]{3}$")
    expected_outcome_kind: str = Field(
        pattern=r"^(single_representative|explicit_tie|invalid_input)$"
    )
    expected_representative_ids: tuple[str, ...]
    expected_non_dominated_ids: tuple[str, ...]
    expected_reason_codes: dict[str, Any]
    pre_selector_validation: PreSelectorValidation
    source_grounding: SourceGrounding
    acceptance_reason: str
    failure_label_intent: tuple[str, ...]
    diagnostic_explanation: str
    proposal_status: str
    order_reversal_invariant: dict[str, Any] | None = None


class ComparisonOutcome(BaseModel):
    """One case result, including explicit non-execution for negative controls."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^SEL-T02-FH-[0-9]{3}$")
    selector_execution_permitted: bool
    expected_outcome_kind: str
    expected_representative_ids: tuple[str, ...]
    expected_non_dominated_ids: tuple[str, ...]
    actual_selection_state: str | None = None
    actual_representative_ids: tuple[str, ...] = ()
    actual_non_dominated_ids: tuple[str, ...] = ()
    pre_selector_boundary: str | None = None
    expected_error_class: str | None = None
    contract_matches: bool
    mismatch_reason: str | None = None


class ComparisonMetrics(BaseModel):
    """Bounded result metrics for one frozen selector comparison."""

    model_config = ConfigDict(extra="forbid")

    frozen_asset_count: int = Field(ge=0)
    source_card_count: int = Field(ge=0)
    valid_selector_case_count: int = Field(ge=0)
    pre_selector_rejection_case_count: int = Field(ge=0)
    valid_case_contract_pass_rate: float = Field(ge=0, le=1)
    pre_selector_rejections_passed: bool
    order_invariance_passed: bool
    source_card_hashes_verified: bool
    freeze_manifest_verified: bool
    freeze_receipt_verified: bool
    failed_case_ids: tuple[str, ...] = ()
    selector_loaded: bool = True
    active_policy_loaded: bool = False
    retrieval_loaded: bool = False
    procedures_loaded: bool = False
    existing_heldout_loaded: bool = False
    procedure_asymmetry_fixture_loaded: bool = False
    selector_activation_authorized: bool = False


class Tranche02FutureHeldoutComparisonReport(BaseModel):
    """Write-once report for the predeclared frozen comparison."""

    model_config = ConfigDict(extra="forbid")

    report_kind: str = "tranche_02_future_heldout_comparison"
    generated_at: datetime
    comparison_decision: Tranche02FutureHeldoutComparisonDecision
    decision_reasons: tuple[str, ...] = Field(min_length=1)
    frozen_fixture_path: str
    freeze_manifest_path: str
    freeze_receipt_path: str
    metrics: ComparisonMetrics
    outcomes: tuple[ComparisonOutcome, ...] = Field(min_length=1)
    activation_blockers: tuple[str, ...] = Field(min_length=1)
    non_claims: tuple[str, ...] = Field(min_length=1)


IncidentCardLoader = Callable[[Path], HistoricalIncidentCard]


def run_tranche_02_future_heldout_comparison(
    *,
    repository_root: Path,
    selector: Selector | None = None,
    incident_card_loader: IncidentCardLoader | None = None,
) -> Tranche02FutureHeldoutComparisonReport:
    """Run exactly one frozen comparison without changing any runtime behavior.

    Integrity failures raise before selector execution. A selector mismatch is a
    legitimate measured result and returns ``comparison_blocked`` for report
    persistence and review.
    """

    root = repository_root.resolve()
    fixture_root = root / FROZEN_FIXTURE_RELATIVE_PATH
    freeze_manifest_path = fixture_root / FREEZE_MANIFEST_FILENAME
    freeze_manifest_bytes = _read_required_bytes(freeze_manifest_path)
    freeze_manifest = _load_freeze_manifest(freeze_manifest_bytes, freeze_manifest_path)
    freeze_receipt = _load_freeze_receipt(root)

    _verify_freeze_receipt(
        receipt=freeze_receipt,
        freeze_manifest_bytes=freeze_manifest_bytes,
    )
    _verify_freeze_manifest(freeze_manifest)
    frozen_payloads = _verify_frozen_asset_integrity(
        fixture_root=fixture_root,
        manifest=freeze_manifest,
    )

    runtime_cases, expected_outcomes = _load_frozen_cases(
        payloads=frozen_payloads,
        manifest=freeze_manifest,
    )
    _validate_runtime_outcome_separation(
        runtime_cases=runtime_cases,
        expected_outcomes=expected_outcomes,
    )

    loader = incident_card_loader or _load_historical_incident_card
    selector_instance = selector or StrictDominanceRepresentativeSelector()
    loaded_cards: dict[str, HistoricalIncidentCard] = {}
    outcomes: list[ComparisonOutcome] = []

    for case_id in EXPECTED_CASE_IDS:
        runtime_case = runtime_cases[case_id]
        expected = expected_outcomes[case_id]
        case_cards = _load_and_verify_source_cards(
            root=root,
            runtime_case=runtime_case,
            expected=expected,
            loader=loader,
            loaded_cards=loaded_cards,
        )
        if case_id in PRE_SELECTOR_REJECTION_CASE_IDS:
            outcomes.append(
                _evaluate_pre_selector_rejection(
                    runtime_case=runtime_case,
                    expected=expected,
                    cards=case_cards,
                )
            )
            continue
        outcomes.append(
            _evaluate_valid_selector_case(
                selector=selector_instance,
                runtime_case=runtime_case,
                expected=expected,
                cards=case_cards,
            )
        )

    order_invariance_passed = _validate_order_invariance(
        runtime_cases=runtime_cases,
        expected_outcomes=expected_outcomes,
        outcomes=tuple(outcomes),
    )
    metrics = _build_metrics(
        outcomes=tuple(outcomes),
        order_invariance_passed=order_invariance_passed,
        frozen_asset_count=len(frozen_payloads),
        source_card_count=len(loaded_cards),
    )
    decision, reasons = _decide(metrics)
    return Tranche02FutureHeldoutComparisonReport(
        generated_at=datetime.now(UTC),
        comparison_decision=decision,
        decision_reasons=reasons,
        frozen_fixture_path=FROZEN_FIXTURE_RELATIVE_PATH.as_posix(),
        freeze_manifest_path=(
            FROZEN_FIXTURE_RELATIVE_PATH / FREEZE_MANIFEST_FILENAME
        ).as_posix(),
        freeze_receipt_path=FREEZE_RECEIPT_RELATIVE_PATH.as_posix(),
        metrics=metrics,
        outcomes=tuple(outcomes),
        activation_blockers=(
            "The strict-dominance selector remains disconnected from AntiAnchoringDecisionPolicy.",
            "No activation ADR or active-policy integration review has authorized selector activation.",
            "This frozen comparison does not establish decision-state, procedure-withholding, provider-degraded, retrieval, or production safety for an integrated runtime path.",
        ),
        non_claims=(
            "Expected outcomes are evaluator-only oracles and are never supplied to selector invocation.",
            "This comparison does not alter retrieval, active policy, procedures, Tranche 01, provider behavior, or any production-facing decision path.",
            "A passing comparison does not authorize procedure execution, production use, customer-data validation, or automated incident response.",
        ),
    )


def write_tranche_02_future_heldout_comparison_report(
    *,
    report: Tranche02FutureHeldoutComparisonReport,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Persist one comparison receipt and refuse any overwrite."""

    existing = tuple(path for path in (json_path, markdown_path) if path.exists())
    if existing:
        raise FileExistsError(
            "Tranche 02 future-heldout comparison evidence already exists and will not "
            "be overwritten: " + ", ".join(str(path) for path in existing)
        )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _load_freeze_manifest(payload: bytes, path: Path) -> FreezeManifest:
    try:
        return FreezeManifest.model_validate_json(payload)
    except ValidationError as error:
        raise Tranche02FutureHeldoutComparisonError(
            f"freeze manifest is invalid: {path}"
        ) from error


def _load_freeze_receipt(root: Path) -> FreezeReceipt:
    path = root / FREEZE_RECEIPT_RELATIVE_PATH
    try:
        return FreezeReceipt.model_validate_json(_read_required_bytes(path))
    except ValidationError as error:
        raise Tranche02FutureHeldoutComparisonError(
            f"freeze receipt is invalid: {path}"
        ) from error


def _verify_freeze_receipt(*, receipt: FreezeReceipt, freeze_manifest_bytes: bytes) -> None:
    if receipt.report_kind != "tranche_02_future_heldout_freeze":
        raise Tranche02FutureHeldoutComparisonError("freeze receipt kind is invalid")
    if receipt.decision != "frozen_test_only":
        raise Tranche02FutureHeldoutComparisonError("freeze receipt does not record frozen_test_only")
    if receipt.frozen_fixture_path != FROZEN_FIXTURE_RELATIVE_PATH.as_posix():
        raise Tranche02FutureHeldoutComparisonError("freeze receipt fixture path is invalid")
    expected_manifest_path = (
        FROZEN_FIXTURE_RELATIVE_PATH / FREEZE_MANIFEST_FILENAME
    ).as_posix()
    if receipt.freeze_manifest_path != expected_manifest_path:
        raise Tranche02FutureHeldoutComparisonError("freeze receipt manifest path is invalid")
    if receipt.freeze_manifest_sha256 != _sha256(freeze_manifest_bytes):
        raise Tranche02FutureHeldoutComparisonError(
            "freeze receipt does not match the current freeze manifest SHA-256"
        )
    if (
        receipt.runtime_case_count != 12
        or receipt.expected_outcome_count != 12
        or receipt.source_archive_asset_count != 27
    ):
        raise Tranche02FutureHeldoutComparisonError("freeze receipt counts are invalid")
    if any(
        (
            receipt.selector_loaded,
            receipt.active_policy_loaded,
            receipt.retrieval_loaded,
            receipt.selector_activation_authorized,
        )
    ):
        raise Tranche02FutureHeldoutComparisonError(
            "freeze receipt declares a prohibited runtime dependency or activation state"
        )


def _verify_freeze_manifest(manifest: FreezeManifest) -> None:
    if manifest.manifest_kind != "tranche_02_future_heldout_freeze_manifest":
        raise Tranche02FutureHeldoutComparisonError("freeze manifest kind is invalid")
    if manifest.freeze_status != "frozen_test_only_not_active":
        raise Tranche02FutureHeldoutComparisonError("freeze manifest status is invalid")
    if (
        manifest.source_acceptance_decision
        != "accepted_for_governed_future_tranche_freeze"
    ):
        raise Tranche02FutureHeldoutComparisonError(
            "freeze manifest acceptance decision is invalid"
        )
    if manifest.accepted_case_ids != EXPECTED_CASE_IDS:
        raise Tranche02FutureHeldoutComparisonError(
            "freeze manifest accepted cases do not match Tranche 02 contract"
        )
    if (
        manifest.runtime_case_count != 12
        or manifest.expected_outcome_count != 12
        or manifest.source_archive_asset_count != 27
    ):
        raise Tranche02FutureHeldoutComparisonError("freeze manifest counts are invalid")
    if any(
        (
            manifest.selector_loaded,
            manifest.active_policy_loaded,
            manifest.retrieval_loaded,
            manifest.procedures_loaded,
            manifest.existing_heldout_loaded,
            manifest.procedure_asymmetry_fixture_loaded,
            manifest.selector_activation_authorized,
        )
    ):
        raise Tranche02FutureHeldoutComparisonError(
            "freeze manifest declares a prohibited dependency or activation state"
        )

    checks = {check.case_id: check for check in manifest.pre_selector_checks}
    if tuple(checks) != EXPECTED_CASE_IDS:
        raise Tranche02FutureHeldoutComparisonError(
            "freeze manifest pre-selector check set is invalid"
        )
    for case_id in VALID_SELECTOR_CASE_IDS:
        check = checks[case_id]
        if check.validation_status != "valid" or not check.selector_execution_permitted:
            raise Tranche02FutureHeldoutComparisonError(
                f"valid comparison case is not selector-permitted: {case_id}"
            )
    for case_id, error_class in (
        ("SEL-T02-FH-011", "duplicate_operational_signal_family"),
        ("SEL-T02-FH-012", "cross_family_candidate_pool_rejected"),
    ):
        check = checks[case_id]
        if (
            check.validation_status != "invalid_expected"
            or check.selector_execution_permitted
            or check.expected_error_class != error_class
        ):
            raise Tranche02FutureHeldoutComparisonError(
                f"negative pre-selector control is invalid: {case_id}"
            )


def _verify_frozen_asset_integrity(
    *,
    fixture_root: Path,
    manifest: FreezeManifest,
) -> dict[str, bytes]:
    expected_paths = {
        *[f"inputs/cases/{case_id}.json" for case_id in EXPECTED_CASE_IDS],
        *[f"expected_outcomes/{case_id}.json" for case_id in EXPECTED_CASE_IDS],
    }
    inventory = {asset.relative_path: asset for asset in manifest.frozen_asset_inventory}
    if set(inventory) != expected_paths or len(inventory) != 24:
        raise Tranche02FutureHeldoutComparisonError(
            "freeze manifest asset inventory does not match the exact 24 frozen case assets"
        )

    observed_paths = {
        path.relative_to(fixture_root).as_posix()
        for path in fixture_root.rglob("*")
        if path.is_file()
    }
    allowed_paths = expected_paths | {FREEZE_MANIFEST_FILENAME}
    if observed_paths != allowed_paths:
        raise Tranche02FutureHeldoutComparisonError(
            "frozen fixture file set differs from the governed freeze manifest"
        )

    payloads: dict[str, bytes] = {}
    for relative_path, asset in inventory.items():
        payload = _read_required_bytes(fixture_root / relative_path)
        if len(payload) != asset.byte_count:
            raise Tranche02FutureHeldoutComparisonError(
                f"frozen asset byte count mismatch: {relative_path}"
            )
        if _sha256(payload) != asset.sha256:
            raise Tranche02FutureHeldoutComparisonError(
                f"frozen asset SHA-256 mismatch: {relative_path}"
            )
        expected_group = (
            "runtime_inputs"
            if relative_path.startswith("inputs/cases/")
            else "expected_outcomes"
        )
        if asset.asset_group != expected_group:
            raise Tranche02FutureHeldoutComparisonError(
                f"frozen asset group mismatch: {relative_path}"
            )
        payloads[relative_path] = payload

    aggregates = manifest.frozen_aggregate_hashes
    expected_aggregate_names = {
        "runtime_inputs",
        "expected_outcomes",
        "all_frozen_assets",
    }
    if set(aggregates) != expected_aggregate_names:
        raise Tranche02FutureHeldoutComparisonError("freeze aggregate set is invalid")
    for aggregate_name, assets in (
        (
            "runtime_inputs",
            tuple(asset for asset in inventory.values() if asset.asset_group == "runtime_inputs"),
        ),
        (
            "expected_outcomes",
            tuple(asset for asset in inventory.values() if asset.asset_group == "expected_outcomes"),
        ),
        ("all_frozen_assets", tuple(inventory.values())),
    ):
        if aggregates[aggregate_name] != _aggregate_hash(assets):
            raise Tranche02FutureHeldoutComparisonError(
                f"freeze aggregate SHA-256 mismatch: {aggregate_name}"
            )
    return payloads


def _load_frozen_cases(
    *,
    payloads: Mapping[str, bytes],
    manifest: FreezeManifest,
) -> tuple[dict[str, FrozenRuntimeCase], dict[str, ExpectedOutcome]]:
    runtime_cases: dict[str, FrozenRuntimeCase] = {}
    outcomes: dict[str, ExpectedOutcome] = {}
    for case_id in EXPECTED_CASE_IDS:
        runtime_path = f"inputs/cases/{case_id}.json"
        outcome_path = f"expected_outcomes/{case_id}.json"
        runtime_raw = _load_json_object(payloads[runtime_path], runtime_path)
        forbidden = FORBIDDEN_RUNTIME_KEYS & set(runtime_raw)
        if forbidden:
            raise Tranche02FutureHeldoutComparisonError(
                "runtime input contains evaluator-only outcome fields for "
                f"{case_id}: {', '.join(sorted(forbidden))}"
            )
        try:
            runtime_case = FrozenRuntimeCase.model_validate(runtime_raw)
            expected_outcome = ExpectedOutcome.model_validate_json(payloads[outcome_path])
        except ValidationError as error:
            raise Tranche02FutureHeldoutComparisonError(
                f"frozen case contract is invalid: {case_id}"
            ) from error
        if (
            runtime_case.case_id != case_id
            or expected_outcome.case_id != case_id
            or runtime_case.contract_version != "tranche-02-selection-v1"
        ):
            raise Tranche02FutureHeldoutComparisonError(
                f"frozen case identity or contract version is invalid: {case_id}"
            )
        runtime_cases[case_id] = runtime_case
        outcomes[case_id] = expected_outcome

    if tuple(runtime_cases) != manifest.accepted_case_ids or tuple(outcomes) != manifest.accepted_case_ids:
        raise Tranche02FutureHeldoutComparisonError(
            "frozen case sets differ from accepted freeze manifest cases"
        )
    return runtime_cases, outcomes


def _validate_runtime_outcome_separation(
    *,
    runtime_cases: Mapping[str, FrozenRuntimeCase],
    expected_outcomes: Mapping[str, ExpectedOutcome],
) -> None:
    for case_id in EXPECTED_CASE_IDS:
        runtime_case = runtime_cases[case_id]
        expected = expected_outcomes[case_id]
        if runtime_case.case_id != expected.case_id:
            raise Tranche02FutureHeldoutComparisonError(
                f"runtime/outcome case ID mismatch: {case_id}"
            )
        if expected.expected_reason_codes.get("classification") != "evaluator-diagnostic-only":
            raise Tranche02FutureHeldoutComparisonError(
                f"expected reason codes are not evaluator-only: {case_id}"
            )
        notice = expected.expected_reason_codes.get("non_runtime_notice")
        if not isinstance(notice, str) or "must not be loaded by runtime selector code" not in notice:
            raise Tranche02FutureHeldoutComparisonError(
                f"expected reason-code non-runtime notice is invalid: {case_id}"
            )


def _load_and_verify_source_cards(
    *,
    root: Path,
    runtime_case: FrozenRuntimeCase,
    expected: ExpectedOutcome,
    loader: IncidentCardLoader,
    loaded_cards: dict[str, HistoricalIncidentCard],
) -> tuple[HistoricalIncidentCard, ...]:
    grounding_ids = tuple(card.source_card_id for card in expected.source_grounding.source_cards)
    if grounding_ids != runtime_case.candidate_incident_ids:
        raise Tranche02FutureHeldoutComparisonError(
            f"source grounding order differs from runtime candidates: {runtime_case.case_id}"
        )

    cards: list[HistoricalIncidentCard] = []
    for grounding in expected.source_grounding.source_cards:
        source_path = root / "data" / "incidents" / f"{grounding.source_card_id}.json"
        raw = _read_required_bytes(source_path)
        if _sha256(raw) != grounding.source_card_sha256:
            raise Tranche02FutureHeldoutComparisonError(
                "source-card SHA-256 mismatch for "
                f"{runtime_case.case_id}/{grounding.source_card_id}"
            )
        card = loaded_cards.get(grounding.source_card_id)
        if card is None:
            card = loader(source_path)
            loaded_cards[grounding.source_card_id] = card
        if _value(card.incident_id) != grounding.source_card_id:
            raise Tranche02FutureHeldoutComparisonError(
                f"loaded source card ID is invalid: {grounding.source_card_id}"
            )
        if _value(card.incident_family) != grounding.incident_family:
            raise Tranche02FutureHeldoutComparisonError(
                f"source-card family differs from frozen grounding: {grounding.source_card_id}"
            )
        if bool(card.selection_signature) != grounding.selection_signature_present:
            raise Tranche02FutureHeldoutComparisonError(
                f"source-card selection signature differs from frozen grounding: {grounding.source_card_id}"
            )
        cards.append(card)
    return tuple(cards)


def _evaluate_pre_selector_rejection(
    *,
    runtime_case: FrozenRuntimeCase,
    expected: ExpectedOutcome,
    cards: tuple[HistoricalIncidentCard, ...],
) -> ComparisonOutcome:
    validation = expected.pre_selector_validation
    if (
        validation.expected_status != "invalid"
        or validation.must_pass_before_selector
        or validation.selector_execution_permitted is not False
        or not validation.expected_error_class
        or not validation.validation_boundary
    ):
        raise Tranche02FutureHeldoutComparisonError(
            f"negative pre-selector declaration is invalid: {runtime_case.case_id}"
        )

    if runtime_case.case_id == "SEL-T02-FH-011":
        if (
            validation.validation_boundary != "RepresentativeSelectionIntake"
            or validation.expected_error_class != "duplicate_operational_signal_family"
        ):
            raise Tranche02FutureHeldoutComparisonError(
                "FH-011 negative contract is invalid"
            )
        try:
            RepresentativeSelectionIntake.model_validate(runtime_case.selection_intake)
        except ValidationError as error:
            if "must not repeat" not in str(error):
                raise Tranche02FutureHeldoutComparisonError(
                    "FH-011 failed intake validation for an unexpected reason"
                ) from error
            return ComparisonOutcome(
                case_id=runtime_case.case_id,
                selector_execution_permitted=False,
                expected_outcome_kind=expected.expected_outcome_kind,
                expected_representative_ids=expected.expected_representative_ids,
                expected_non_dominated_ids=expected.expected_non_dominated_ids,
                pre_selector_boundary=validation.validation_boundary,
                expected_error_class=validation.expected_error_class,
                contract_matches=True,
            )
        raise Tranche02FutureHeldoutComparisonError(
            "FH-011 reached selector comparison despite duplicate intake signals"
        )

    if runtime_case.case_id == "SEL-T02-FH-012":
        if (
            validation.validation_boundary != "candidate_pool_family"
            or validation.expected_error_class != "cross_family_candidate_pool_rejected"
        ):
            raise Tranche02FutureHeldoutComparisonError(
                "FH-012 negative contract is invalid"
            )
        try:
            RepresentativeSelectionIntake.model_validate(runtime_case.selection_intake)
        except ValidationError as error:
            raise Tranche02FutureHeldoutComparisonError(
                "FH-012 typed intake must validate before mixed-family rejection"
            ) from error
        families = {_value(card.incident_family) for card in cards}
        if len(families) <= 1:
            raise Tranche02FutureHeldoutComparisonError(
                "FH-012 must remain a genuinely mixed-family candidate pool"
            )
        if runtime_case.candidate_pool_family not in families:
            raise Tranche02FutureHeldoutComparisonError(
                "FH-012 candidate pool declaration must name one family in the mixed pool"
            )
        return ComparisonOutcome(
            case_id=runtime_case.case_id,
            selector_execution_permitted=False,
            expected_outcome_kind=expected.expected_outcome_kind,
            expected_representative_ids=expected.expected_representative_ids,
            expected_non_dominated_ids=expected.expected_non_dominated_ids,
            pre_selector_boundary=validation.validation_boundary,
            expected_error_class=validation.expected_error_class,
            contract_matches=True,
        )

    raise Tranche02FutureHeldoutComparisonError(
        f"unexpected negative pre-selector case: {runtime_case.case_id}"
    )


def _evaluate_valid_selector_case(
    *,
    selector: Selector,
    runtime_case: FrozenRuntimeCase,
    expected: ExpectedOutcome,
    cards: tuple[HistoricalIncidentCard, ...],
) -> ComparisonOutcome:
    validation = expected.pre_selector_validation
    if (
        validation.expected_status != "valid"
        or validation.must_pass_before_selector is not True
        or validation.selector_execution_permitted is not None
    ):
        raise Tranche02FutureHeldoutComparisonError(
            f"valid selector declaration is invalid: {runtime_case.case_id}"
        )
    if runtime_case.candidate_pool_family != "connection_pool_exhaustion":
        raise Tranche02FutureHeldoutComparisonError(
            f"selector-permitted case uses unsupported family: {runtime_case.case_id}"
        )
    try:
        intake = RepresentativeSelectionIntake.model_validate(runtime_case.selection_intake)
    except ValidationError as error:
        raise Tranche02FutureHeldoutComparisonError(
            f"valid case fails typed selection intake validation: {runtime_case.case_id}"
        ) from error
    if any(_value(card.incident_family) != runtime_case.candidate_pool_family for card in cards):
        raise Tranche02FutureHeldoutComparisonError(
            f"selector-permitted candidate pool is not same-family: {runtime_case.case_id}"
        )
    if any(card.selection_signature is None for card in cards):
        raise Tranche02FutureHeldoutComparisonError(
            f"selector-permitted candidate lacks signature: {runtime_case.case_id}"
        )

    result = selector.select(
        intake=intake,
        candidate_incident_ids=runtime_case.candidate_incident_ids,
        incidents=cards,
    )
    actual_state = result.selection_state.value
    actual_ids = tuple(result.representative_incident_ids)
    actual_non_dominated = actual_ids
    expected_ids = (
        expected.expected_representative_ids
        if expected.expected_outcome_kind == "single_representative"
        else expected.expected_non_dominated_ids
    )
    expected_state = expected.expected_outcome_kind
    trace_ids = {item.incident_id for item in result.candidate_evidence}
    trace_matches_candidates = trace_ids == set(runtime_case.candidate_incident_ids)
    contract_matches = (
        actual_state == expected_state
        and actual_ids == expected_ids
        and actual_non_dominated == expected.expected_non_dominated_ids
        and trace_matches_candidates
    )
    mismatch_parts: list[str] = []
    if actual_state != expected_state:
        mismatch_parts.append(f"state expected={expected_state} actual={actual_state}")
    if actual_ids != expected_ids:
        mismatch_parts.append(f"representatives expected={expected_ids} actual={actual_ids}")
    if not trace_matches_candidates:
        mismatch_parts.append("selector trace does not cover exactly the frozen candidates")
    return ComparisonOutcome(
        case_id=runtime_case.case_id,
        selector_execution_permitted=True,
        expected_outcome_kind=expected.expected_outcome_kind,
        expected_representative_ids=expected.expected_representative_ids,
        expected_non_dominated_ids=expected.expected_non_dominated_ids,
        actual_selection_state=actual_state,
        actual_representative_ids=actual_ids,
        actual_non_dominated_ids=actual_non_dominated,
        contract_matches=contract_matches,
        mismatch_reason="; ".join(mismatch_parts) if mismatch_parts else None,
    )


def _validate_order_invariance(
    *,
    runtime_cases: Mapping[str, FrozenRuntimeCase],
    expected_outcomes: Mapping[str, ExpectedOutcome],
    outcomes: tuple[ComparisonOutcome, ...],
) -> bool:
    first_case = runtime_cases["SEL-T02-FH-001"]
    second_case = runtime_cases["SEL-T02-FH-002"]
    first_expected = expected_outcomes[first_case.case_id]
    second_expected = expected_outcomes[second_case.case_id]
    first_actual = _outcome_by_id(outcomes, first_case.case_id)
    second_actual = _outcome_by_id(outcomes, second_case.case_id)

    if tuple(reversed(first_case.candidate_incident_ids)) != second_case.candidate_incident_ids:
        raise Tranche02FutureHeldoutComparisonError(
            "FH-001/FH-002 no longer form exact candidate-order reversals"
        )
    if (
        first_case.selection_intake != second_case.selection_intake
        or first_case.candidate_pool_family != second_case.candidate_pool_family
        or first_expected.expected_outcome_kind != second_expected.expected_outcome_kind
        or first_expected.expected_representative_ids
        != second_expected.expected_representative_ids
        or first_expected.expected_non_dominated_ids
        != second_expected.expected_non_dominated_ids
    ):
        raise Tranche02FutureHeldoutComparisonError(
            "FH-001/FH-002 differ beyond candidate serialization order"
        )
    return (
        first_actual.contract_matches
        and second_actual.contract_matches
        and first_actual.actual_selection_state == second_actual.actual_selection_state
        and first_actual.actual_representative_ids == second_actual.actual_representative_ids
        and first_actual.actual_non_dominated_ids == second_actual.actual_non_dominated_ids
    )


def _build_metrics(
    *,
    outcomes: tuple[ComparisonOutcome, ...],
    order_invariance_passed: bool,
    frozen_asset_count: int,
    source_card_count: int,
) -> ComparisonMetrics:
    valid = tuple(
        outcome for outcome in outcomes if outcome.selector_execution_permitted
    )
    negative = tuple(
        outcome for outcome in outcomes if not outcome.selector_execution_permitted
    )
    failed_case_ids = tuple(
        outcome.case_id for outcome in outcomes if not outcome.contract_matches
    )
    valid_pass_count = sum(outcome.contract_matches for outcome in valid)
    return ComparisonMetrics(
        frozen_asset_count=frozen_asset_count,
        source_card_count=source_card_count,
        valid_selector_case_count=len(valid),
        pre_selector_rejection_case_count=len(negative),
        valid_case_contract_pass_rate=(
            valid_pass_count / len(valid) if valid else 0.0
        ),
        pre_selector_rejections_passed=all(
            outcome.contract_matches for outcome in negative
        ),
        order_invariance_passed=order_invariance_passed,
        source_card_hashes_verified=True,
        freeze_manifest_verified=True,
        freeze_receipt_verified=True,
        failed_case_ids=failed_case_ids,
    )


def _decide(
    metrics: ComparisonMetrics,
) -> tuple[Tranche02FutureHeldoutComparisonDecision, tuple[str, ...]]:
    if (
        metrics.valid_selector_case_count != 10
        or metrics.pre_selector_rejection_case_count != 2
    ):
        return (
            Tranche02FutureHeldoutComparisonDecision.INSUFFICIENT_EVIDENCE,
            (
                "The frozen tranche does not expose the required 10 selector cases and 2 pre-selector controls.",
            ),
        )
    if (
        metrics.valid_case_contract_pass_rate != 1.0
        or not metrics.pre_selector_rejections_passed
        or not metrics.order_invariance_passed
    ):
        return (
            Tranche02FutureHeldoutComparisonDecision.COMPARISON_BLOCKED,
            (
                "The isolated selector did not satisfy every evaluator-controlled frozen Tranche 02 contract.",
            ),
        )
    return (
        Tranche02FutureHeldoutComparisonDecision.COMPARISON_PASSED_ACTIVATION_BLOCKED,
        (
            "All ten selector-permitted cases matched evaluator-only frozen outcomes.",
            "Both negative controls rejected before selector execution.",
            "The exact order-reversal pair produced the same selection result.",
            "Activation remains blocked because this gate does not integrate the selector into active policy or authorize a runtime behavior change.",
        ),
    )


def _render_markdown(report: Tranche02FutureHeldoutComparisonReport) -> str:
    lines = [
        "# Tranche 02 Future-Held-Out Comparison",
        "",
        "## Decision",
        "",
        f"`{report.comparison_decision.value}`",
        "",
        "## Frozen evidence",
        "",
        f"- Frozen fixture: `{report.frozen_fixture_path}`",
        f"- Freeze manifest: `{report.freeze_manifest_path}`",
        f"- Freeze receipt: `{report.freeze_receipt_path}`",
        "",
        "## Metrics",
        "",
        f"- Valid selector cases: `{report.metrics.valid_selector_case_count}`",
        f"- Pre-selector rejection controls: `{report.metrics.pre_selector_rejection_case_count}`",
        f"- Valid-case contract pass rate: `{report.metrics.valid_case_contract_pass_rate:.2f}`",
        f"- Order invariance: `{str(report.metrics.order_invariance_passed).lower()}`",
        f"- Source-card hashes verified: `{str(report.metrics.source_card_hashes_verified).lower()}`",
        f"- Failed cases: `{', '.join(report.metrics.failed_case_ids) or 'none'}`",
        "",
        "## Case outcomes",
        "",
        "| Case | Selector executed | Expected | Actual | Contract match |",
        "|---|---:|---|---|---:|",
    ]
    for outcome in report.outcomes:
        actual = outcome.actual_selection_state or "pre-selector rejection"
        lines.append(
            "| "
            f"{outcome.case_id} | {str(outcome.selector_execution_permitted).lower()} | "
            f"{outcome.expected_outcome_kind} | {actual} | "
            f"{str(outcome.contract_matches).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Activation blockers",
            "",
            *[f"- {blocker}" for blocker in report.activation_blockers],
            "",
            "## Non-claims",
            "",
            *[f"- {claim}" for claim in report.non_claims],
            "",
        ]
    )
    return "\n".join(lines)


def _load_historical_incident_card(path: Path) -> HistoricalIncidentCard:
    try:
        return HistoricalIncidentCard.model_validate_json(_read_required_bytes(path))
    except ValidationError as error:
        raise Tranche02FutureHeldoutComparisonError(
            f"source incident card is invalid: {path}"
        ) from error


def _aggregate_hash(assets: tuple[FrozenAsset, ...]) -> str:
    lines = "".join(
        f"{asset.sha256}  {asset.byte_count}  {asset.relative_path}\n"
        for asset in sorted(assets, key=lambda item: item.relative_path)
    )
    return _sha256(lines.encode("utf-8"))


def _load_json_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Tranche02FutureHeldoutComparisonError(
            f"invalid JSON for {label}"
        ) from error
    if not isinstance(value, dict):
        raise Tranche02FutureHeldoutComparisonError(
            f"JSON object required for {label}"
        )
    return value


def _read_required_bytes(path: Path) -> bytes:
    if not path.is_file():
        raise Tranche02FutureHeldoutComparisonError(f"required evidence is missing: {path}")
    return path.read_bytes()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _value(value: Any) -> str:
    return getattr(value, "value", value)


def _outcome_by_id(
    outcomes: tuple[ComparisonOutcome, ...],
    case_id: str,
) -> ComparisonOutcome:
    for outcome in outcomes:
        if outcome.case_id == case_id:
            return outcome
    raise Tranche02FutureHeldoutComparisonError(
        f"comparison outcome is missing: {case_id}"
    )
