"""Frozen end-to-end promotion gate for the advisory-only typed triage boundary.

This evaluator deliberately measures the current typed triage path without changing
retrieval, policy authority, held-out fixtures, or semantic-advisory behavior.
A blocked result is valid evidence. It is never a reason to alter frozen cases.
"""

from __future__ import annotations

import json
import math
import time
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, Field

from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.domain.incident_data import (
    CandidateInvestigationProcedure,
    EvalCase,
    HistoricalIncidentCard,
)
from incident_precedent_harness.domain.incident_enums import EvidenceDecisionState
from incident_precedent_harness.evaluation.heldout import (
    HeldoutEvaluationReport,
    HeldoutFreezeVerification,
    run_frozen_heldout_evaluation,
    verify_heldout_freeze,
)
from incident_precedent_harness.retrieval.keyword import KeywordRetriever
from incident_precedent_harness.triage.models import SemanticAdvisoryStatus, TriageRequest
from incident_precedent_harness.triage.service import TriageService

JSON_REPORT_RELATIVE_PATH = (
    Path("evidence_vault") / "reports" / "frozen-typed-triage-promotion-gate.json"
)
MARKDOWN_REPORT_RELATIVE_PATH = (
    Path("docs") / "reports" / "frozen-typed-triage-promotion-gate.md"
)
PROVISIONAL_P95_PIPELINE_LATENCY_BUDGET_MS = 1_500


class TriagePromotionDecision(str, Enum):
    """Possible decisions for the current advisory-only typed triage candidate."""

    PROMOTE_ADVISORY_ONLY = "promote_advisory_only"
    BLOCK = "block"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class FrozenTypedTriageGateError(RuntimeError):
    """Raised when the frozen typed-triage gate cannot construct trustworthy evidence."""


class BaselineSummary(BaseModel):
    """Minimal immutable comparison context from the current keyword-policy baseline."""

    model_config = ConfigDict(extra="forbid")

    report_kind: str
    promotion_status: str
    decision_state_accuracy: float = Field(ge=0, le=1)
    case_contract_pass_rate: float = Field(ge=0, le=1)
    blocked_case_ids: tuple[str, ...]
    top_k: int = Field(ge=1)


class TriagePromotionCaseOutcome(BaseModel):
    """Trace-safe comparison of one frozen case across baseline and typed triage."""

    model_config = ConfigDict(extra="forbid")

    eval_id: str = Field(pattern=r"^EVAL-[0-9]{3}$")
    expected_decision_state: EvidenceDecisionState
    baseline_decision_state: EvidenceDecisionState
    typed_triage_decision_state: EvidenceDecisionState
    typed_triage_matches_expected_state: bool
    policy_matches_baseline: bool
    policy_retained_precedent_ids: tuple[str, ...]
    policy_candidate_procedure_ids: tuple[str, ...]
    policy_missing_critical_facts: tuple[str, ...]
    semantic_advisory_status: SemanticAdvisoryStatus
    semantic_candidate_ids: tuple[str, ...]
    procedure_execution_authorized: bool
    provider_degraded_resolution_safe: bool
    pipeline_latency_ms: int = Field(ge=0)
    query_embedding_latency_ms: int | None = Field(default=None, ge=0)
    policy_failure_labels: tuple[str, ...] = ()
    failure_labels: tuple[str, ...] = ()


class FrozenTypedTriageMetrics(BaseModel):
    """Control, safety, advisory-availability, and latency metrics for the candidate."""

    model_config = ConfigDict(extra="forbid")

    heldout_case_count: int = Field(gt=0)
    typed_triage_expected_state_accuracy: float = Field(ge=0, le=1)
    policy_baseline_parity_rate: float = Field(ge=0, le=1)
    policy_case_contract_pass_rate: float = Field(ge=0, le=1)
    semantic_advisory_available_count: int = Field(ge=0)
    unexpected_semantic_degraded_count: int = Field(ge=0)
    provider_degraded_case_count: int = Field(ge=0)
    provider_degraded_safe_resolution_rate: float | None = Field(default=None, ge=0, le=1)
    procedure_execution_authorized_count: int = Field(ge=0)
    p50_pipeline_latency_ms: int | None = Field(default=None, ge=0)
    p95_pipeline_latency_ms: int | None = Field(default=None, ge=0)
    blocked_case_ids: tuple[str, ...]


class FrozenTypedTriagePromotionReport(BaseModel):
    """Write-once result for the frozen typed-triage promotion decision."""

    model_config = ConfigDict(extra="forbid")

    report_kind: str = "frozen_typed_triage_promotion_gate"
    generated_at: datetime
    freeze_verification: HeldoutFreezeVerification
    baseline: BaselineSummary
    candidate_name: str = "typed_triage_keyword_policy_plus_local_sie_dense_advisory_v1"
    policy_candidate_source: str = "deterministic_keyword_top_5"
    semantic_advisory_source: str = "local_sie_dense_top_5"
    provisional_p95_pipeline_latency_budget_ms: int = Field(
        default=PROVISIONAL_P95_PIPELINE_LATENCY_BUDGET_MS,
        ge=1,
    )
    metrics: FrozenTypedTriageMetrics
    decision: TriagePromotionDecision
    decision_reasons: tuple[str, ...] = Field(min_length=1)
    outcomes: tuple[TriagePromotionCaseOutcome, ...]
    non_claims: tuple[str, ...] = Field(min_length=1)


def run_frozen_typed_triage_promotion_gate(
    *,
    repository_root: Path,
    service: TriageService,
    incidents: tuple[HistoricalIncidentCard, ...],
    procedures: tuple[CandidateInvestigationProcedure, ...],
    cases: tuple[EvalCase, ...],
    policy_top_k: int = 5,
    provisional_p95_pipeline_latency_budget_ms: int = PROVISIONAL_P95_PIPELINE_LATENCY_BUDGET_MS,
) -> FrozenTypedTriagePromotionReport:
    """Compare frozen keyword-policy authority with typed advisory packets.

    The baseline is evaluated in-memory using the current deterministic keyword and
    policy configuration. No historical report is overwritten. The candidate must
    preserve that policy output exactly while separately reporting semantic advisory
    availability and latency.
    """

    if provisional_p95_pipeline_latency_budget_ms < 1:
        raise ValueError("provisional_p95_pipeline_latency_budget_ms must be at least 1")
    if policy_top_k != service.policy_top_k:
        raise FrozenTypedTriageGateError(
            "typed-triage gate policy_top_k must equal the service policy_top_k"
        )

    root = repository_root.resolve()
    verification = verify_heldout_freeze(root)
    _verify_loaded_cases(cases=cases, verification=verification)

    baseline_report = run_frozen_heldout_evaluation(
        repository_root=root,
        retriever=KeywordRetriever(incidents),
        policy=AntiAnchoringDecisionPolicy(),
        incidents=incidents,
        procedures=procedures,
        cases=cases,
        top_k=policy_top_k,
    )
    baseline_by_case = {outcome.eval_id: outcome for outcome in baseline_report.outcomes}

    outcomes: list[TriagePromotionCaseOutcome] = []
    for case in cases:
        baseline_outcome = baseline_by_case.get(case.eval_id)
        if baseline_outcome is None:
            raise FrozenTypedTriageGateError(
                f"baseline did not produce an outcome for frozen case {case.eval_id}"
            )

        request = TriageRequest(
            request_id=uuid5(NAMESPACE_URL, f"frozen-typed-triage:{case.eval_id}"),
            trace_id=uuid5(NAMESPACE_URL, f"frozen-typed-triage-trace:{case.eval_id}"),
            input_summary=case.input_summary,
            observed_facts=case.observed_facts,
            provider_available=case.provider_available,
        )

        started_at = time.perf_counter()
        packet = service.triage(request)
        pipeline_latency_ms = int(round((time.perf_counter() - started_at) * 1_000))

        policy = packet.policy_decision
        policy_missing_facts = tuple(fact.value for fact in policy.missing_critical_facts)
        baseline_missing_facts = tuple(baseline_outcome.actual_missing_facts)
        policy_matches_baseline = (
            policy.decision_state is baseline_outcome.actual_decision_state
            and tuple(policy.retained_precedent_ids)
            == tuple(baseline_outcome.retained_precedent_ids)
            and tuple(policy.candidate_procedure_ids)
            == tuple(baseline_outcome.candidate_procedure_ids)
            and policy_missing_facts == baseline_missing_facts
        )

        expected_state_match = policy.decision_state is case.expected_decision_state
        semantic_candidate_ids = tuple(
            candidate.incident_id for candidate in packet.semantic_advisory.candidate_evidence
        )
        degraded_safe = _provider_degraded_resolution_is_safe(
            case=case,
            packet=packet,
        )

        labels = list(baseline_outcome.failure_labels)
        if not expected_state_match:
            labels.append("typed_triage_decision_state_mismatch")
        if not policy_matches_baseline:
            labels.append("policy_authority_parity_failure")
        if packet.procedure_execution_authorized:
            labels.append("procedure_execution_authorized")
        if case.provider_available:
            if packet.semantic_advisory.status is not SemanticAdvisoryStatus.AVAILABLE:
                labels.append("unexpected_semantic_provider_degraded")
            elif not semantic_candidate_ids:
                labels.append("semantic_advisory_missing_candidates")
            elif packet.semantic_advisory.query_embedding_latency_ms is None:
                labels.append("semantic_advisory_missing_latency")
        elif not degraded_safe:
            labels.append("provider_degraded_fail_closed_violation")

        outcomes.append(
            TriagePromotionCaseOutcome(
                eval_id=case.eval_id,
                expected_decision_state=case.expected_decision_state,
                baseline_decision_state=baseline_outcome.actual_decision_state,
                typed_triage_decision_state=policy.decision_state,
                typed_triage_matches_expected_state=expected_state_match,
                policy_matches_baseline=policy_matches_baseline,
                policy_retained_precedent_ids=tuple(policy.retained_precedent_ids),
                policy_candidate_procedure_ids=tuple(policy.candidate_procedure_ids),
                policy_missing_critical_facts=policy_missing_facts,
                semantic_advisory_status=packet.semantic_advisory.status,
                semantic_candidate_ids=semantic_candidate_ids,
                procedure_execution_authorized=packet.procedure_execution_authorized,
                provider_degraded_resolution_safe=degraded_safe,
                pipeline_latency_ms=pipeline_latency_ms,
                query_embedding_latency_ms=packet.semantic_advisory.query_embedding_latency_ms,
                policy_failure_labels=tuple(baseline_outcome.failure_labels),
                failure_labels=tuple(labels),
            )
        )

    outcome_tuple = tuple(outcomes)
    metrics = _build_metrics(outcome_tuple)
    baseline = _summarize_baseline(baseline_report)
    decision, reasons = _decide(
        baseline=baseline,
        metrics=metrics,
        latency_budget_ms=provisional_p95_pipeline_latency_budget_ms,
    )

    return FrozenTypedTriagePromotionReport(
        generated_at=datetime.now(UTC),
        freeze_verification=verification,
        baseline=baseline,
        provisional_p95_pipeline_latency_budget_ms=provisional_p95_pipeline_latency_budget_ms,
        metrics=metrics,
        decision=decision,
        decision_reasons=reasons,
        outcomes=outcome_tuple,
        non_claims=(
            "This is a frozen 12-case tranche, not the final planned 36-case held-out evaluation set.",
            "The semantic advisory remains non-authoritative; it cannot alter the active keyword-policy decision, retained precedents, missing facts, or procedure eligibility.",
            "A promote_advisory_only decision does not promote a semantic retriever, diagnose root cause, authorize a procedure, or establish production readiness.",
            "A blocked or insufficient-evidence result is evidence, not a reason to tune held-out inputs, labels, thresholds, ranking behavior, or policy rules.",
            "This local synthetic-data run does not establish customer-data validation, production provider reliability, load behavior, or production incident-response safety.",
        ),
    )


def write_frozen_typed_triage_promotion_report(
    report: FrozenTypedTriagePromotionReport,
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write one immutable evidence pair and refuse to overwrite it."""

    existing = tuple(path for path in (json_path, markdown_path) if path.exists())
    if existing:
        rendered = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            "Frozen typed-triage promotion evidence already exists and will not be overwritten: "
            f"{rendered}. Preserve the original result; create a separately named follow-up "
            "evaluation only after a documented change."
        )

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _verify_loaded_cases(
    *,
    cases: tuple[EvalCase, ...],
    verification: HeldoutFreezeVerification,
) -> None:
    observed_ids = tuple(case.eval_id for case in cases)
    if set(observed_ids) != set(verification.verified_case_ids):
        raise FrozenTypedTriageGateError(
            "loaded held-out cases differ from manifest-verified case IDs"
        )
    if any(case.split != "heldout" for case in cases):
        raise FrozenTypedTriageGateError(
            "frozen typed-triage gate received a non-held-out case"
        )


def _provider_degraded_resolution_is_safe(*, case: EvalCase, packet) -> bool:  # type: ignore[no-untyped-def]
    """Return the fail-closed invariant for fixture-declared provider degradation."""

    if case.provider_available:
        return False
    return (
        packet.semantic_advisory.status is SemanticAdvisoryStatus.PROVIDER_DEGRADED
        and packet.policy_decision.decision_state is EvidenceDecisionState.PROVIDER_DEGRADED
        and not packet.semantic_advisory.candidate_evidence
        and not packet.policy_decision.retained_precedent_ids
        and not packet.policy_decision.candidate_procedure_ids
        and packet.procedure_execution_authorized is False
    )


def _build_metrics(
    outcomes: tuple[TriagePromotionCaseOutcome, ...],
) -> FrozenTypedTriageMetrics:
    if not outcomes:
        raise FrozenTypedTriageGateError("frozen typed-triage gate produced no outcomes")

    provider_degraded_outcomes = tuple(
        outcome for outcome in outcomes
        if outcome.expected_decision_state is EvidenceDecisionState.PROVIDER_DEGRADED
    )
    available_latencies = tuple(
        outcome.pipeline_latency_ms
        for outcome in outcomes
        if outcome.semantic_advisory_status is SemanticAdvisoryStatus.AVAILABLE
    )

    return FrozenTypedTriageMetrics(
        heldout_case_count=len(outcomes),
        typed_triage_expected_state_accuracy=_ratio(
            sum(outcome.typed_triage_matches_expected_state for outcome in outcomes),
            len(outcomes),
        ),
        policy_baseline_parity_rate=_ratio(
            sum(outcome.policy_matches_baseline for outcome in outcomes),
            len(outcomes),
        ),
        policy_case_contract_pass_rate=_ratio(
            sum(not outcome.policy_failure_labels for outcome in outcomes),
            len(outcomes),
        ),
        semantic_advisory_available_count=sum(
            outcome.semantic_advisory_status is SemanticAdvisoryStatus.AVAILABLE
            for outcome in outcomes
        ),
        unexpected_semantic_degraded_count=sum(
            outcome.expected_decision_state is not EvidenceDecisionState.PROVIDER_DEGRADED
            and outcome.semantic_advisory_status is SemanticAdvisoryStatus.PROVIDER_DEGRADED
            for outcome in outcomes
        ),
        provider_degraded_case_count=len(provider_degraded_outcomes),
        provider_degraded_safe_resolution_rate=(
            _ratio(
                sum(
                    outcome.provider_degraded_resolution_safe
                    for outcome in provider_degraded_outcomes
                ),
                len(provider_degraded_outcomes),
            )
            if provider_degraded_outcomes
            else None
        ),
        procedure_execution_authorized_count=sum(
            outcome.procedure_execution_authorized for outcome in outcomes
        ),
        p50_pipeline_latency_ms=_percentile(available_latencies, 0.50),
        p95_pipeline_latency_ms=_percentile(available_latencies, 0.95),
        blocked_case_ids=tuple(
            outcome.eval_id for outcome in outcomes if outcome.failure_labels
        ),
    )


def _summarize_baseline(report: HeldoutEvaluationReport) -> BaselineSummary:
    return BaselineSummary(
        report_kind=report.report_kind,
        promotion_status=report.promotion_gate.status,
        decision_state_accuracy=report.metrics.decision_state_accuracy,
        case_contract_pass_rate=report.metrics.case_contract_pass_rate,
        blocked_case_ids=report.metrics.blocked_case_ids,
        top_k=report.configuration.top_k,
    )


def _decide(
    *,
    baseline: BaselineSummary,
    metrics: FrozenTypedTriageMetrics,
    latency_budget_ms: int,
) -> tuple[TriagePromotionDecision, tuple[str, ...]]:
    """Decide conservatively; safety failure blocks, missing required evidence abstains."""

    blocking_reasons: list[str] = []
    insufficient_reasons: list[str] = []

    if baseline.promotion_status != "passed":
        blocking_reasons.append(
            "The underlying frozen keyword-plus-policy baseline is blocked; the typed "
            "advisory wrapper cannot promote a blocked policy path."
        )
    if metrics.typed_triage_expected_state_accuracy < 1.0:
        blocking_reasons.append(
            "Typed-triage decision-state behavior differs from one or more frozen expectations."
        )
    if metrics.policy_baseline_parity_rate < 1.0:
        blocking_reasons.append(
            "Semantic advisory evidence changed policy authority or policy output."
        )
    if metrics.policy_case_contract_pass_rate < 1.0:
        blocking_reasons.append(
            "The underlying policy violates one or more frozen evidence, procedure, "
            "or missing-fact contracts."
        )
    if metrics.procedure_execution_authorized_count > 0:
        blocking_reasons.append(
            "One or more packets authorized procedure execution, which is forbidden."
        )
    if metrics.unexpected_semantic_degraded_count > 0:
        blocking_reasons.append(
            "A provider-available frozen case returned degraded semantic advisory evidence."
        )
    if metrics.provider_degraded_safe_resolution_rate is None:
        insufficient_reasons.append(
            "The frozen tranche contains no provider-degraded case, so fail-closed "
            "provider behavior cannot be evidenced."
        )
    elif metrics.provider_degraded_safe_resolution_rate < 1.0:
        blocking_reasons.append(
            "The provider-degraded case did not fail closed with empty candidate evidence "
            "and no candidate procedures."
        )
    if metrics.p50_pipeline_latency_ms is None or metrics.p95_pipeline_latency_ms is None:
        insufficient_reasons.append(
            "No semantic-advisory pipeline latency samples were recorded."
        )
    elif metrics.p95_pipeline_latency_ms > latency_budget_ms:
        blocking_reasons.append(
            "Observed p95 end-to-end typed-triage latency exceeds the provisional "
            f"{latency_budget_ms} ms budget."
        )

    if blocking_reasons:
        return TriagePromotionDecision.BLOCK, tuple(blocking_reasons)
    if insufficient_reasons:
        return TriagePromotionDecision.INSUFFICIENT_EVIDENCE, tuple(insufficient_reasons)
    return (
        TriagePromotionDecision.PROMOTE_ADVISORY_ONLY,
        (
            "The frozen control gate preserved policy authority, passed the recorded "
            "safety invariants, and remained within the provisional latency budget. "
            "Promotion is advisory-only and does not promote semantic retrieval as "
            "decision authority.",
        ),
    )


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _percentile(values: tuple[int, ...], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    position = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[position]


def _render_markdown(report: FrozenTypedTriagePromotionReport) -> str:
    metrics = report.metrics
    baseline = report.baseline
    lines = [
        "# Frozen Typed-Triage Promotion Gate",
        "",
        "## Scope",
        "",
        "This write-once report compares the frozen deterministic keyword-plus-policy "
        "baseline with the current typed triage packet boundary.",
        "The semantic layer remains advisory-only. It must not change policy authority, "
        "retained precedent IDs, missing facts, or candidate procedure eligibility.",
        "",
        "## Freeze verification",
        "",
        f"- Scope: `{report.freeze_verification.scope}`",
        f"- Manifest: `{report.freeze_verification.manifest_path}`",
        f"- Manifest SHA-256: `{report.freeze_verification.manifest_sha256}`",
        f"- Verified frozen cases: `{report.freeze_verification.case_count}`",
        "",
        "## Baseline comparison",
        "",
        f"- Baseline report kind: `{baseline.report_kind}`",
        f"- Baseline promotion status: `{baseline.promotion_status}`",
        f"- Baseline decision-state accuracy: `{baseline.decision_state_accuracy}`",
        f"- Baseline case-contract pass rate: `{baseline.case_contract_pass_rate}`",
        f"- Baseline blocked cases: `{', '.join(baseline.blocked_case_ids) or 'none'}`",
        "",
        "## Candidate boundary",
        "",
        f"- Policy candidate source: `{report.policy_candidate_source}`",
        f"- Semantic advisory source: `{report.semantic_advisory_source}`",
        "- Procedure execution authorization: `false` by contract.",
        f"- Provisional p95 end-to-end latency budget: `{report.provisional_p95_pipeline_latency_budget_ms} ms`",
        "",
        "## Gate decision",
        "",
        f"**Decision: {report.decision.value.upper()}**",
        "",
        "### Rationale",
        "",
    ]
    lines.extend(f"- {reason}" for reason in report.decision_reasons)
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Frozen held-out cases | {metrics.heldout_case_count} |",
            f"| Typed-triage expected-state accuracy | {metrics.typed_triage_expected_state_accuracy} |",
            f"| Policy baseline parity | {metrics.policy_baseline_parity_rate} |",
            f"| Policy case-contract pass rate | {metrics.policy_case_contract_pass_rate} |",
            f"| Semantic advisory available | {metrics.semantic_advisory_available_count}/{metrics.heldout_case_count} |",
            f"| Unexpected semantic degraded | {metrics.unexpected_semantic_degraded_count} |",
            f"| Provider-degraded cases | {metrics.provider_degraded_case_count} |",
            f"| Provider-degraded safe resolution rate | {metrics.provider_degraded_safe_resolution_rate if metrics.provider_degraded_safe_resolution_rate is not None else 'not available'} |",
            f"| Procedure execution authorized | {metrics.procedure_execution_authorized_count} |",
            f"| P50 end-to-end latency | {metrics.p50_pipeline_latency_ms if metrics.p50_pipeline_latency_ms is not None else 'not available'} ms |",
            f"| P95 end-to-end latency | {metrics.p95_pipeline_latency_ms if metrics.p95_pipeline_latency_ms is not None else 'not available'} ms |",
            f"| Blocked cases | {', '.join(metrics.blocked_case_ids) or 'none'} |",
            "",
            "## Case outcomes",
            "",
            "| Eval case | Expected | Baseline | Typed triage | Policy parity | Semantic advisory | Procedures authorized | Pipeline latency | Failure labels |",
            "|---|---|---|---|---:|---|---:|---:|---|",
        ]
    )
    for outcome in report.outcomes:
        labels = ", ".join(outcome.failure_labels) or "none"
        lines.append(
            "| {eval_id} | {expected} | {baseline} | {typed} | {parity} | {advisory} | {authorized} | {latency} ms | {labels} |".format(
                eval_id=outcome.eval_id,
                expected=outcome.expected_decision_state.value,
                baseline=outcome.baseline_decision_state.value,
                typed=outcome.typed_triage_decision_state.value,
                parity=str(outcome.policy_matches_baseline).lower(),
                advisory=outcome.semantic_advisory_status.value,
                authorized=str(outcome.procedure_execution_authorized).lower(),
                latency=outcome.pipeline_latency_ms,
                labels=labels,
            )
        )
    lines.extend(["", "## Non-claims", ""])
    lines.extend(f"- {claim}" for claim in report.non_claims)
    lines.append("")
    return "\n".join(lines)
