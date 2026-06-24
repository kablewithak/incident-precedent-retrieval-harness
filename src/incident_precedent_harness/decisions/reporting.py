"""Calibration-only reporting for deterministic anti-anchoring policy."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from incident_precedent_harness.decisions.models import PolicyDecisionResult
from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.domain.incident_data import (
    CandidateInvestigationProcedure,
    EvalCase,
    HistoricalIncidentCard,
)
from incident_precedent_harness.domain.incident_enums import EvidenceDecisionState
from incident_precedent_harness.retrieval.keyword import KeywordRetriever


class PolicyCaseOutcome(BaseModel):
    eval_id: str
    expected_decision_state: EvidenceDecisionState
    actual_decision_state: EvidenceDecisionState
    expected_missing_facts: tuple[str, ...]
    actual_missing_facts: tuple[str, ...]
    retained_precedent_ids: tuple[str, ...]
    candidate_procedure_ids: tuple[str, ...]
    state_matches_expected: bool
    unsafe_precedent_surfaced: bool
    unsafe_procedure_surfaced: bool


class PolicyCalibrationMetrics(BaseModel):
    scored_case_count: int = Field(ge=0)
    decision_state_accuracy: float = Field(ge=0, le=1)
    false_operational_match_count: int = Field(ge=0)
    unsafe_procedure_surfacing_count: int = Field(ge=0)
    no_precedent_abstention_accuracy: float | None = Field(default=None, ge=0, le=1)
    conflict_state_accuracy: float | None = Field(default=None, ge=0, le=1)
    missing_fact_exact_match_rate: float | None = Field(default=None, ge=0, le=1)


class PolicyCalibrationReport(BaseModel):
    report_kind: str = "anti_anchoring_policy_calibration"
    generated_at: datetime
    corpus_incident_count: int = Field(ge=0)
    calibration_case_count: int = Field(ge=0)
    top_k: int = Field(ge=1)
    metrics: PolicyCalibrationMetrics
    outcomes: tuple[PolicyCaseOutcome, ...]
    known_limits: tuple[str, ...] = Field(min_length=1)


def run_policy_calibration(
    *,
    retriever: KeywordRetriever,
    policy: AntiAnchoringDecisionPolicy,
    incidents: tuple[HistoricalIncidentCard, ...],
    procedures: tuple[CandidateInvestigationProcedure, ...],
    cases: tuple[EvalCase, ...],
    top_k: int = 5,
) -> PolicyCalibrationReport:
    outcomes: list[PolicyCaseOutcome] = []
    for case in cases:
        ranked = retriever.rank(case.input_summary, top_k=top_k)
        result = policy.evaluate(
            intake=case,
            ranked_candidates=ranked,
            incidents=incidents,
            procedures=procedures,
        )
        outcomes.append(_outcome(case=case, result=result))
    outcome_tuple = tuple(outcomes)
    return PolicyCalibrationReport(
        generated_at=datetime.now(UTC),
        corpus_incident_count=len(incidents),
        calibration_case_count=len(cases),
        top_k=top_k,
        metrics=_metrics(outcome_tuple),
        outcomes=outcome_tuple,
        known_limits=(
            "Calibration-only report; held-out cases are not loaded or scored.",
            "Policy uses explicit structured evaluation facts; it does not perform free-text extraction.",
            "This prototype supports only the three authored incident families.",
            "Candidate procedures remain non-executable investigation artifacts.",
            "No semantic-provider, dense-retrieval, reranking, or warm-latency claim is made.",
        ),
    )


def write_report(report: PolicyCalibrationReport, *, json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _outcome(*, case: EvalCase, result: PolicyDecisionResult) -> PolicyCaseOutcome:
    actual_missing = tuple(fact.value for fact in result.missing_critical_facts)
    expected_missing = tuple(fact.value for fact in case.expected_missing_facts)
    retained = result.retained_precedent_ids
    unsafe_precedent_surfaced = bool(set(retained).intersection(case.unsafe_precedent_ids))
    expected_procedures = set(case.expected_candidate_procedure_ids)
    unsafe_procedure_surfaced = bool(
        result.candidate_procedure_ids
        and set(result.candidate_procedure_ids) != expected_procedures
    )
    return PolicyCaseOutcome(
        eval_id=case.eval_id,
        expected_decision_state=case.expected_decision_state,
        actual_decision_state=result.decision_state,
        expected_missing_facts=expected_missing,
        actual_missing_facts=actual_missing,
        retained_precedent_ids=retained,
        candidate_procedure_ids=result.candidate_procedure_ids,
        state_matches_expected=result.decision_state is case.expected_decision_state,
        unsafe_precedent_surfaced=unsafe_precedent_surfaced,
        unsafe_procedure_surfaced=unsafe_procedure_surfaced,
    )


def _metrics(outcomes: tuple[PolicyCaseOutcome, ...]) -> PolicyCalibrationMetrics:
    state_matches = sum(outcome.state_matches_expected for outcome in outcomes)
    no_precedent = tuple(
        outcome
        for outcome in outcomes
        if outcome.expected_decision_state is EvidenceDecisionState.INSUFFICIENT_PRECEDENT
    )
    conflict = tuple(
        outcome
        for outcome in outcomes
        if outcome.expected_decision_state is EvidenceDecisionState.EVIDENCE_FOUND_WITH_CONFLICT
    )
    missing_fact_cases = tuple(
        outcome
        for outcome in outcomes
        if outcome.expected_decision_state is EvidenceDecisionState.MISSING_CRITICAL_FACTS
    )
    return PolicyCalibrationMetrics(
        scored_case_count=len(outcomes),
        decision_state_accuracy=round(state_matches / len(outcomes), 4) if outcomes else 0.0,
        false_operational_match_count=sum(outcome.unsafe_precedent_surfaced for outcome in outcomes),
        unsafe_procedure_surfacing_count=sum(outcome.unsafe_procedure_surfaced for outcome in outcomes),
        no_precedent_abstention_accuracy=_group_accuracy(
            no_precedent,
            EvidenceDecisionState.INSUFFICIENT_PRECEDENT,
        ),
        conflict_state_accuracy=_group_accuracy(
            conflict,
            EvidenceDecisionState.EVIDENCE_FOUND_WITH_CONFLICT,
        ),
        missing_fact_exact_match_rate=(
            round(
                sum(
                    set(outcome.expected_missing_facts) == set(outcome.actual_missing_facts)
                    for outcome in missing_fact_cases
                )
                / len(missing_fact_cases),
                4,
            )
            if missing_fact_cases
            else None
        ),
    )


def _group_accuracy(
    outcomes: tuple[PolicyCaseOutcome, ...],
    expected: EvidenceDecisionState,
) -> float | None:
    if not outcomes:
        return None
    return round(
        sum(outcome.actual_decision_state is expected for outcome in outcomes) / len(outcomes),
        4,
    )


def _render_markdown(report: PolicyCalibrationReport) -> str:
    metrics = report.metrics
    lines = [
        "# Anti-Anchoring Policy Calibration Report",
        "",
        "## Scope",
        "",
        "This report evaluates deterministic compatibility, abstention, missing-fact, conflict, and procedure gates on calibration fixtures only.",
        "It is not a semantic-retrieval or production-safety claim.",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Decision-state accuracy | {metrics.decision_state_accuracy} |",
        f"| False-operational matches surfaced | {metrics.false_operational_match_count} |",
        f"| Unsafe procedures surfaced | {metrics.unsafe_procedure_surfacing_count} |",
        f"| No-precedent abstention accuracy | {metrics.no_precedent_abstention_accuracy if metrics.no_precedent_abstention_accuracy is not None else 'not applicable'} |",
        f"| Conflict-state accuracy | {metrics.conflict_state_accuracy if metrics.conflict_state_accuracy is not None else 'not applicable'} |",
        f"| Missing-fact exact-match rate | {metrics.missing_fact_exact_match_rate if metrics.missing_fact_exact_match_rate is not None else 'not applicable'} |",
        "",
        "## Case outcomes",
        "",
        "| Eval case | Expected | Actual | Retained precedents | Candidate procedures | Missing facts | Unsafe precedent | Unsafe procedure |",
        "|---|---|---|---|---|---|---:|---:|",
    ]
    for outcome in report.outcomes:
        lines.append(
            "| "
            f"{outcome.eval_id} | {outcome.expected_decision_state.value} | {outcome.actual_decision_state.value} | "
            f"{', '.join(outcome.retained_precedent_ids) or 'none'} | "
            f"{', '.join(outcome.candidate_procedure_ids) or 'none'} | "
            f"{', '.join(outcome.actual_missing_facts) or 'none'} | "
            f"{str(outcome.unsafe_precedent_surfaced).lower()} | "
            f"{str(outcome.unsafe_procedure_surfaced).lower()} |"
        )
    lines.extend(["", "## Known limits", ""])
    lines.extend(f"- {limit}" for limit in report.known_limits)
    lines.append("")
    return "\n".join(lines)
