"""Controlled activation-readiness evidence for conditional selection integration.

This is not a promotion gate. It verifies the narrow ADR-0033 integration
contract using source-grounded local incident cards and deterministic policy
inputs. Its only passing decision remains activation-blocked because no
selection-aware, end-to-end frozen policy promotion gate exists yet.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from incident_precedent_harness.decisions.conditional_representative_selection import (
    ConditionalRepresentativeSelectionPolicy,
    RepresentativeSelectionRefinementStatus,
)
from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.domain.incident_data import (
    EvalCase,
    ObservedVerificationFact,
    RepresentativeSelectionIntake,
)
from incident_precedent_harness.domain.incident_enums import (
    ChangeContext,
    EvidenceDecisionState,
    OperationalSignalFamily,
    RelayComponent,
    RelayService,
    RequiredVerificationFact,
    VerificationFactStatus,
)
from incident_precedent_harness.retrieval.models import KeywordCandidate
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository

JSON_REPORT_RELATIVE_PATH = (
    Path("evidence_vault")
    / "reports"
    / "conditional-representative-selection-activation-readiness.json"
)
MARKDOWN_REPORT_RELATIVE_PATH = (
    Path("docs")
    / "reports"
    / "conditional-representative-selection-activation-readiness.md"
)


class ActivationReadinessDecision(str, Enum):
    """Explicit decision for this narrow non-promotion readiness check."""

    IMPLEMENTATION_VALIDATED_ACTIVATION_BLOCKED = (
        "implementation_validated_activation_blocked"
    )
    BLOCKED = "blocked"


class ActivationReadinessCaseOutcome(BaseModel):
    """One fixed controlled integration case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    baseline_policy_state: str
    integrated_policy_state: str
    policy_state_unchanged: bool
    procedures_unchanged: bool
    missing_facts_unchanged: bool
    expected_refinement_status: str
    actual_refinement_status: str
    expected_displayed_representatives: tuple[str, ...]
    actual_displayed_representatives: tuple[str, ...]
    contract_matches: bool
    failure_labels: tuple[str, ...]


class ConditionalSelectionActivationReadinessReport(BaseModel):
    """Write-once local evidence for ADR-0033 implementation correctness."""

    model_config = ConfigDict(extra="forbid")

    report_kind: str = "conditional_representative_selection_activation_readiness"
    generated_at: datetime
    decision: ActivationReadinessDecision
    decision_reasons: tuple[str, ...] = Field(min_length=1)
    fixed_case_count: int
    contract_pass_rate: float = Field(ge=0, le=1)
    outcomes: tuple[ActivationReadinessCaseOutcome, ...]
    activation_blockers: tuple[str, ...] = Field(min_length=1)
    non_claims: tuple[str, ...] = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class _Control:
    case_id: str
    candidates: tuple[str, ...]
    intake: RepresentativeSelectionIntake
    expected_status: RepresentativeSelectionRefinementStatus
    expected_displayed: tuple[str, ...]
    failure_labels: tuple[str, ...]


def _eval_case() -> EvalCase:
    return EvalCase(
        eval_id="EVAL-999",
        split="calibration",
        input_summary=(
            "Database connection pool utilization and acquisition latency are confirmed "
            "elevated while active connections are high. Migration lock waits are contradicted."
        ),
        expected_decision_state=EvidenceDecisionState.EVIDENCE_FOUND,
        acceptable_precedent_ids=("INC-009",),
        expected_candidate_procedure_ids=("RB-003",),
        observed_facts=(
            ObservedVerificationFact(
                fact=RequiredVerificationFact.DATABASE_CONNECTION_POOL_UTILIZATION,
                status=VerificationFactStatus.CONFIRMED,
            ),
            ObservedVerificationFact(
                fact=RequiredVerificationFact.DATABASE_CONNECTION_ACQUIRE_LATENCY,
                status=VerificationFactStatus.CONFIRMED,
            ),
            ObservedVerificationFact(
                fact=RequiredVerificationFact.ACTIVE_DATABASE_CONNECTIONS,
                status=VerificationFactStatus.CONFIRMED,
            ),
            ObservedVerificationFact(
                fact=RequiredVerificationFact.MIGRATION_LOCK_WAITS,
                status=VerificationFactStatus.CONTRADICTED,
            ),
            ObservedVerificationFact(
                fact=RequiredVerificationFact.ERROR_RATE_BY_COMPONENT,
                status=VerificationFactStatus.CONFIRMED,
            ),
        ),
        failure_label_intent=("conditional_selection_integration",),
        acceptance_reason=(
            "Controlled post-admission selector integration check for the "
            "connection-pool family."
        ),
    )


def _controls() -> tuple[_Control, ...]:
    return (
        _Control(
            case_id="CSR-001-single-winner",
            candidates=("INC-010", "INC-009"),
            intake=RepresentativeSelectionIntake(
                service=RelayService.PAYMENTS_API,
                component=RelayComponent.POSTGRES_CLIENT_POOL,
                change_context=ChangeContext.NONE,
                operational_signal_families=(
                    OperationalSignalFamily.CONNECTION_POOL_PRESSURE,
                    OperationalSignalFamily.ACTIVE_CONNECTION_PRESSURE,
                ),
            ),
            expected_status=RepresentativeSelectionRefinementStatus.SINGLE_REPRESENTATIVE_APPLIED,
            expected_displayed=("INC-009",),
            failure_labels=(
                "dominance_relation_error",
                "retrieval_order_fallback",
                "policy_authority_mutation",
            ),
        ),
        _Control(
            case_id="CSR-002-explicit-tie",
            candidates=("INC-010", "INC-009"),
            intake=RepresentativeSelectionIntake(
                operational_signal_families=(
                    OperationalSignalFamily.CONNECTION_POOL_PRESSURE,
                ),
            ),
            expected_status=RepresentativeSelectionRefinementStatus.EXPLICIT_TIE_APPLIED,
            expected_displayed=("INC-009", "INC-010"),
            failure_labels=(
                "forced_winner_error",
                "candidate_order_dependence",
                "policy_authority_mutation",
            ),
        ),
        _Control(
            case_id="CSR-003-selection-not-requested",
            candidates=("INC-010", "INC-009"),
            intake=None,  # type: ignore[arg-type]
            expected_status=RepresentativeSelectionRefinementStatus.NOT_REQUESTED,
            expected_displayed=("INC-010",),
            failure_labels=("unexpected_selector_invocation",),
        ),
    )


def run_conditional_selection_activation_readiness(
    *,
    repository_root: Path,
) -> ConditionalSelectionActivationReadinessReport:
    """Evaluate fixed non-held-out integration controls without writing output."""

    repository = JsonDatasetRepository(repository_root)
    incidents = repository.load_incidents()
    procedures = repository.load_procedures()
    incident_by_id = {incident.incident_id: incident for incident in incidents}
    policy = AntiAnchoringDecisionPolicy()
    integration = ConditionalRepresentativeSelectionPolicy(policy)
    case = _eval_case()
    outcomes: list[ActivationReadinessCaseOutcome] = []

    for control in _controls():
        ranked_candidates = tuple(
            KeywordCandidate(
                incident_id=incident_id,
                rank=index,
                score=float(len(control.candidates) - index + 1),
                matched_terms=(),
            )
            for index, incident_id in enumerate(control.candidates, start=1)
        )
        baseline = policy.evaluate(
            intake=case,
            ranked_candidates=ranked_candidates,
            incidents=incidents,
            procedures=procedures,
        )
        integrated = integration.evaluate(
            intake=case,
            ranked_candidates=ranked_candidates,
            incidents=incidents,
            procedures=procedures,
            selection_intake=control.intake,
        )
        policy_unchanged = integrated.policy_decision == baseline
        outcome = ActivationReadinessCaseOutcome(
            case_id=control.case_id,
            baseline_policy_state=baseline.decision_state.value,
            integrated_policy_state=integrated.policy_decision.decision_state.value,
            policy_state_unchanged=(
                integrated.policy_decision.decision_state == baseline.decision_state
            ),
            procedures_unchanged=(
                integrated.policy_decision.candidate_procedure_ids
                == baseline.candidate_procedure_ids
            ),
            missing_facts_unchanged=(
                integrated.policy_decision.missing_critical_facts
                == baseline.missing_critical_facts
            ),
            expected_refinement_status=control.expected_status.value,
            actual_refinement_status=integrated.refinement.status.value,
            expected_displayed_representatives=control.expected_displayed,
            actual_displayed_representatives=(
                integrated.refinement.displayed_representative_ids
            ),
            contract_matches=(
                policy_unchanged
                and integrated.refinement.status is control.expected_status
                and integrated.refinement.displayed_representative_ids
                == control.expected_displayed
            ),
            failure_labels=control.failure_labels,
        )
        outcomes.append(outcome)

    pass_rate = sum(outcome.contract_matches for outcome in outcomes) / len(outcomes)
    decision = (
        ActivationReadinessDecision.IMPLEMENTATION_VALIDATED_ACTIVATION_BLOCKED
        if pass_rate == 1.0
        else ActivationReadinessDecision.BLOCKED
    )
    return ConditionalSelectionActivationReadinessReport(
        generated_at=datetime.now(UTC),
        decision=decision,
        decision_reasons=(
            (
                "All controlled integration cases preserved the complete policy "
                "decision while applying only the typed display-refinement contract."
            )
            if decision
            is ActivationReadinessDecision.IMPLEMENTATION_VALIDATED_ACTIVATION_BLOCKED
            else "At least one controlled integration contract failed.",
        ),
        fixed_case_count=len(outcomes),
        contract_pass_rate=pass_rate,
        outcomes=tuple(outcomes),
        activation_blockers=(
            "No selection-aware end-to-end frozen policy promotion gate has run.",
            "The active policy remains unchanged unless a caller explicitly supplies validated selection intake.",
            "This readiness report does not alter the frozen Tranche 02 receipt or comparison evidence.",
        ),
        non_claims=(
            "This report validates a local synthetic-data integration control, not production readiness.",
            "The selector does not set top-level policy state, missing facts, procedure eligibility, or execution authority.",
            "This report is not evidence that retrieval quality, incident diagnosis, or customer-data safety improved.",
        ),
    )


def write_conditional_selection_activation_readiness_report(
    *,
    report: ConditionalSelectionActivationReadinessReport,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write the activation-readiness evidence once and refuse overwrite."""

    existing = tuple(path for path in (json_path, markdown_path) if path.exists())
    if existing:
        raise FileExistsError(
            "conditional-selection activation-readiness evidence already exists and "
            "will not be overwritten: " + ", ".join(str(path) for path in existing)
        )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _render_markdown(report: ConditionalSelectionActivationReadinessReport) -> str:
    lines = [
        "# Conditional Representative-Selection Activation Readiness",
        "",
        "## Decision",
        "",
        f"`{report.decision.value}`",
        "",
        "## Fixed control results",
        "",
        "| Case | Policy unchanged | Refinement | Displayed representatives | Contract |",
        "|---|---:|---|---|---:|",
    ]
    for outcome in report.outcomes:
        lines.append(
            "| "
            f"{outcome.case_id} | "
            f"{str(outcome.policy_state_unchanged).lower()} | "
            f"{outcome.actual_refinement_status} | "
            f"{', '.join(outcome.actual_displayed_representatives) or 'none'} | "
            f"{str(outcome.contract_matches).lower()} |"
        )
    lines.extend(
        [
            "",
            "## Activation blockers",
            "",
            *[f"- {item}" for item in report.activation_blockers],
            "",
            "## Non-claims",
            "",
            *[f"- {item}" for item in report.non_claims],
            "",
        ]
    )
    return "\n".join(lines)
