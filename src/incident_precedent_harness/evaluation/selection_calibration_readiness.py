"""Write-once calibration-readiness gate for representative selection.

This module evaluates only the standalone strict-dominance selector against its
dedicated selection-calibration fixtures. It never loads held-out fixtures, invokes
retrieval, changes AntiAnchoringDecisionPolicy, or activates selector output.
A calibration pass is deliberately insufficient to activate the selector.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from incident_precedent_harness.decisions.strict_dominance_selection import (
    RepresentativeSelectionResult,
    StrictDominanceRepresentativeSelector,
)
from incident_precedent_harness.domain.incident_data import HistoricalIncidentCard
from incident_precedent_harness.domain.incident_enums import IncidentFamily
from incident_precedent_harness.domain.selection_calibration import (
    RepresentativeSelectionCalibrationCase,
)
from incident_precedent_harness.evals.selection_calibration import (
    load_selection_calibration_cases,
)
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository

JSON_REPORT_RELATIVE_PATH = (
    Path("evidence_vault")
    / "reports"
    / "representative-selection-calibration-readiness.json"
)
MARKDOWN_REPORT_RELATIVE_PATH = (
    Path("docs")
    / "reports"
    / "representative-selection-calibration-readiness.md"
)


class SelectionReadinessDecision(str, Enum):
    """Possible decisions for the calibration-only selection boundary."""

    CALIBRATION_PASSED_ACTIVATION_BLOCKED = "calibration_passed_activation_blocked"
    CALIBRATION_BLOCKED = "calibration_blocked"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class SelectionCalibrationReadinessError(RuntimeError):
    """Raised when the readiness gate cannot produce trustworthy calibration evidence."""


class RepresentativeSelector(Protocol):
    """Minimal deterministic selector boundary used by the readiness gate."""

    def select(
        self,
        *,
        intake,
        candidate_incident_ids,
        incidents: tuple[HistoricalIncidentCard, ...],
    ) -> RepresentativeSelectionResult:
        """Return a standalone, non-authoritative selection result."""


class SelectionCalibrationCaseOutcome(BaseModel):
    """One fixed calibration result with no retrieval or policy authority."""

    model_config = ConfigDict(extra="forbid")

    selection_case_id: str = Field(pattern=r"^SEL-CAL-[0-9]{3}$")
    expected_state: str
    actual_state: str
    expected_representative_incident_ids: tuple[str, ...]
    actual_representative_incident_ids: tuple[str, ...]
    contract_matches: bool
    order_invariance_group: str | None = None
    order_variant: str | None = None


class SelectionCalibrationReadinessMetrics(BaseModel):
    """Inspectably bounded metrics for a selector that remains inactive."""

    model_config = ConfigDict(extra="forbid")

    selection_calibration_case_count: int = Field(ge=0)
    selection_contract_pass_rate: float = Field(ge=0, le=1)
    single_representative_case_count: int = Field(ge=0)
    explicit_tie_case_count: int = Field(ge=0)
    order_invariance_group_count: int = Field(ge=0)
    order_invariance_pass_rate: float | None = Field(default=None, ge=0, le=1)
    all_candidates_connection_pool_exhaustion: bool
    heldout_loaded: bool = False
    retrieval_loaded: bool = False
    active_policy_changed: bool = False
    selector_activation_claim: bool = False
    failed_case_ids: tuple[str, ...]


class SelectionCalibrationReadinessReport(BaseModel):
    """Write-once evidence that separates calibration success from activation."""

    model_config = ConfigDict(extra="forbid")

    report_kind: str = "representative_selection_calibration_readiness"
    generated_at: datetime
    contract_version: str = "representative-selection-v1"
    selector_name: str = "strict_dominance_representative_selector_v1"
    metrics: SelectionCalibrationReadinessMetrics
    decision: SelectionReadinessDecision
    decision_reasons: tuple[str, ...] = Field(min_length=1)
    outcomes: tuple[SelectionCalibrationCaseOutcome, ...] = Field(min_length=1)
    activation_blockers: tuple[str, ...] = Field(min_length=1)
    non_claims: tuple[str, ...] = Field(min_length=1)


def run_selection_calibration_readiness_gate(
    *,
    repository_root: Path,
    selector: RepresentativeSelector | None = None,
) -> SelectionCalibrationReadinessReport:
    """Evaluate fixed selector calibration and preserve an activation block.

    The loader is restricted to ``data/evals/selection_calibration``. This function
    does not import held-out evaluators, does not call retrieval, and cannot change
    the active policy.
    """

    root = repository_root.resolve()
    repository = JsonDatasetRepository(root)
    incidents = repository.load_incidents()
    cases = load_selection_calibration_cases(root)
    if not cases:
        raise SelectionCalibrationReadinessError(
            "selection calibration readiness requires at least one fixed case"
        )

    active_selector = selector or StrictDominanceRepresentativeSelector()
    incident_by_id = {incident.incident_id: incident for incident in incidents}
    outcomes: list[SelectionCalibrationCaseOutcome] = []

    for case in cases:
        _verify_case_scope(case=case, incident_by_id=incident_by_id)
        result = active_selector.select(
            intake=case.selection_intake,
            candidate_incident_ids=case.candidate_incident_ids,
            incidents=incidents,
        )
        expected_ids = tuple(case.expected_outcome.representative_incident_ids)
        actual_ids = tuple(result.representative_incident_ids)
        expected_state = case.expected_outcome.state.value
        actual_state = result.selection_state.value
        outcomes.append(
            SelectionCalibrationCaseOutcome(
                selection_case_id=case.selection_case_id,
                expected_state=expected_state,
                actual_state=actual_state,
                expected_representative_incident_ids=expected_ids,
                actual_representative_incident_ids=actual_ids,
                contract_matches=(
                    expected_state == actual_state and expected_ids == actual_ids
                ),
                order_invariance_group=case.order_invariance_group,
                order_variant=case.order_variant,
            )
        )

    outcome_tuple = tuple(outcomes)
    metrics = _build_metrics(outcomes=outcome_tuple, cases=cases, incident_by_id=incident_by_id)
    decision, reasons = _decide(metrics)
    return SelectionCalibrationReadinessReport(
        generated_at=datetime.now(UTC),
        metrics=metrics,
        decision=decision,
        decision_reasons=reasons,
        outcomes=outcome_tuple,
        activation_blockers=(
            "The strict-dominance selector is not wired into AntiAnchoringDecisionPolicy and remains shadow-only.",
            "Calibration fixtures are not independent held-out evidence for an activation change.",
            "The selector currently supports connection_pool_exhaustion cards only; active policy covers additional incident families.",
            "Any activation proposal requires a separate ADR, an independently authored future held-out tranche, and a new promotion gate.",
        ),
        non_claims=(
            "This report does not load the frozen held-out tranche or reuse EVAL-110 as a calibration fixture.",
            "This report does not invoke lexical retrieval, dense retrieval, semantic inference, or provider infrastructure.",
            "This report does not modify or activate AntiAnchoringDecisionPolicy.",
            "A calibration pass does not prove that activation will preserve held-out behavior, improve retrieval, authorize a procedure, or establish production readiness.",
        ),
    )


def write_selection_calibration_readiness_report(
    report: SelectionCalibrationReadinessReport,
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write the readiness evidence once and reject any overwrite attempt."""

    existing = tuple(path for path in (json_path, markdown_path) if path.exists())
    if existing:
        rendered = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            "Representative-selection calibration readiness evidence already exists "
            f"and will not be overwritten: {rendered}. Preserve this run; create a "
            "separately versioned follow-up after a documented contract change."
        )

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _verify_case_scope(
    *,
    case: RepresentativeSelectionCalibrationCase,
    incident_by_id: dict[str, HistoricalIncidentCard],
) -> None:
    for incident_id in case.candidate_incident_ids:
        incident = incident_by_id.get(incident_id)
        if incident is None:
            raise SelectionCalibrationReadinessError(
                f"{case.selection_case_id} references an unknown incident: {incident_id}"
            )
        if incident.incident_family is not IncidentFamily.CONNECTION_POOL_EXHAUSTION:
            raise SelectionCalibrationReadinessError(
                f"{case.selection_case_id} is outside the current selector scope: {incident_id}"
            )


def _build_metrics(
    *,
    outcomes: tuple[SelectionCalibrationCaseOutcome, ...],
    cases: tuple[RepresentativeSelectionCalibrationCase, ...],
    incident_by_id: dict[str, HistoricalIncidentCard],
) -> SelectionCalibrationReadinessMetrics:
    if not outcomes:
        return SelectionCalibrationReadinessMetrics(
            selection_calibration_case_count=0,
            selection_contract_pass_rate=0.0,
            single_representative_case_count=0,
            explicit_tie_case_count=0,
            order_invariance_group_count=0,
            order_invariance_pass_rate=None,
            all_candidates_connection_pool_exhaustion=False,
            failed_case_ids=(),
        )

    groups: dict[str, list[SelectionCalibrationCaseOutcome]] = defaultdict(list)
    for outcome in outcomes:
        if outcome.order_invariance_group is not None:
            groups[outcome.order_invariance_group].append(outcome)

    order_group_results: list[bool] = []
    for members in groups.values():
        if len(members) != 2:
            order_group_results.append(False)
            continue
        canonical = next(
            (member for member in members if member.order_variant == "canonical"),
            None,
        )
        reversed_case = next(
            (member for member in members if member.order_variant == "reversed"),
            None,
        )
        order_group_results.append(
            canonical is not None
            and reversed_case is not None
            and canonical.actual_state == reversed_case.actual_state
            and canonical.actual_representative_incident_ids
            == reversed_case.actual_representative_incident_ids
            and canonical.contract_matches
            and reversed_case.contract_matches
        )

    all_candidates_in_scope = all(
        incident_by_id[incident_id].incident_family
        is IncidentFamily.CONNECTION_POOL_EXHAUSTION
        for case in cases
        for incident_id in case.candidate_incident_ids
    )
    passed = sum(outcome.contract_matches for outcome in outcomes)
    return SelectionCalibrationReadinessMetrics(
        selection_calibration_case_count=len(outcomes),
        selection_contract_pass_rate=_ratio(passed, len(outcomes)),
        single_representative_case_count=sum(
            outcome.actual_state == "single_representative" for outcome in outcomes
        ),
        explicit_tie_case_count=sum(
            outcome.actual_state == "explicit_tie" for outcome in outcomes
        ),
        order_invariance_group_count=len(groups),
        order_invariance_pass_rate=(
            _ratio(sum(order_group_results), len(order_group_results))
            if order_group_results
            else None
        ),
        all_candidates_connection_pool_exhaustion=all_candidates_in_scope,
        failed_case_ids=tuple(
            outcome.selection_case_id
            for outcome in outcomes
            if not outcome.contract_matches
        ),
    )


def _decide(
    metrics: SelectionCalibrationReadinessMetrics,
) -> tuple[SelectionReadinessDecision, tuple[str, ...]]:
    if metrics.selection_calibration_case_count == 0:
        return (
            SelectionReadinessDecision.INSUFFICIENT_EVIDENCE,
            ("No selection-calibration cases were available to measure the selector.",),
        )
    if metrics.order_invariance_pass_rate is None:
        return (
            SelectionReadinessDecision.INSUFFICIENT_EVIDENCE,
            (
                "No fixed order-invariance pair was available, so rank-independence "
                "could not be measured.",
            ),
        )

    failures: list[str] = []
    if metrics.selection_contract_pass_rate < 1.0:
        failures.append(
            "One or more fixed selection-calibration cases violated the expected contract."
        )
    if metrics.order_invariance_pass_rate < 1.0:
        failures.append(
            "At least one fixed order-invariance group changed result across candidate order."
        )
    if not metrics.all_candidates_connection_pool_exhaustion:
        failures.append(
            "The calibration set contains candidates outside the selector's approved family scope."
        )
    if failures:
        return SelectionReadinessDecision.CALIBRATION_BLOCKED, tuple(failures)

    return (
        SelectionReadinessDecision.CALIBRATION_PASSED_ACTIVATION_BLOCKED,
        (
            "All fixed selection-calibration contracts passed.",
            "Fixed order-invariance groups produced identical results.",
            "Activation remains blocked because calibration is not independent held-out evidence and the selector is not wired into the active policy.",
        ),
    )


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _render_markdown(report: SelectionCalibrationReadinessReport) -> str:
    metrics = report.metrics
    lines = [
        "# Representative-Selection Calibration Readiness",
        "",
        "## Scope",
        "",
        "This write-once report evaluates the standalone strict-dominance selector only on dedicated selection-calibration fixtures.",
        "It does not load held-out evaluation fixtures, invoke retrieval or semantic inference, or activate selector output in the active anti-anchoring policy.",
        "",
        "## Decision",
        "",
        f"**Decision: {report.decision.value.upper()}**",
        "",
        "### Decision reasons",
        "",
    ]
    lines.extend(f"- {reason}" for reason in report.decision_reasons)
    lines.extend(
        [
            "",
            "## Calibration metrics",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Fixed selection-calibration cases | {metrics.selection_calibration_case_count} |",
            f"| Contract pass rate | {metrics.selection_contract_pass_rate} |",
            f"| Single-representative outcomes | {metrics.single_representative_case_count} |",
            f"| Explicit-tie outcomes | {metrics.explicit_tie_case_count} |",
            f"| Order-invariance groups | {metrics.order_invariance_group_count} |",
            f"| Order-invariance pass rate | {metrics.order_invariance_pass_rate if metrics.order_invariance_pass_rate is not None else 'not measured'} |",
            f"| All candidates in approved family scope | {str(metrics.all_candidates_connection_pool_exhaustion).lower()} |",
            f"| Held-out loaded | {str(metrics.heldout_loaded).lower()} |",
            f"| Retrieval loaded | {str(metrics.retrieval_loaded).lower()} |",
            f"| Active policy changed | {str(metrics.active_policy_changed).lower()} |",
            f"| Selector activation claimed | {str(metrics.selector_activation_claim).lower()} |",
            "",
            "## Case outcomes",
            "",
            "| Case | Expected | Actual | Contract | Order group |",
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
        lines.append(
            f"| {outcome.selection_case_id} | {expected} | {actual} | "
            f"{'pass' if outcome.contract_matches else 'block'} | "
            f"{outcome.order_invariance_group or 'none'} |"
        )
    lines.extend(["", "## Activation blockers", ""])
    lines.extend(f"- {blocker}" for blocker in report.activation_blockers)
    lines.extend(["", "## Non-claims", ""])
    lines.extend(f"- {claim}" for claim in report.non_claims)
    lines.append("")
    return "\n".join(lines)
