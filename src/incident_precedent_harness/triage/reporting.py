"""Calibration-only evaluation and portable evidence for typed triage packets."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, Field

from incident_precedent_harness.domain.incident_data import EvalCase
from incident_precedent_harness.domain.incident_enums import EvidenceDecisionState
from incident_precedent_harness.triage.models import SemanticAdvisoryStatus, TriageRequest
from incident_precedent_harness.triage.service import TriageService


class TriageCalibrationCaseOutcome(BaseModel):
    """One calibration-only packet observation without raw incident text."""

    model_config = ConfigDict(extra="forbid")

    eval_id: str = Field(pattern=r"^EVAL-[0-9]{3}$")
    expected_decision_state: EvidenceDecisionState
    observed_decision_state: EvidenceDecisionState
    decision_state_matches: bool
    semantic_advisory_status: SemanticAdvisoryStatus
    policy_retained_precedent_ids: tuple[str, ...]
    semantic_candidate_ids: tuple[str, ...]
    procedure_execution_authorized: bool
    failure_labels: tuple[str, ...] = ()


class TriageCalibrationMetrics(BaseModel):
    """Control-plane assertions rather than retrieval quality metrics."""

    calibration_case_count: int = Field(gt=0)
    matching_decision_state_count: int = Field(ge=0)
    decision_state_match_rate: float = Field(ge=0, le=1)
    semantic_advisory_available_count: int = Field(ge=0)
    provider_degraded_packet_count: int = Field(ge=0)
    procedure_execution_authorized_count: int = Field(ge=0)


class TriageCalibrationReport(BaseModel):
    """Saved evidence for the typed triage boundary on calibration fixtures only."""

    model_config = ConfigDict(extra="forbid")

    report_kind: str = "typed_triage_calibration"
    status: str = Field(pattern=r"^(passed|blocked)$")
    generated_at: datetime
    calibration_case_count: int = Field(gt=0)
    policy_candidate_source: str
    semantic_advisory_source: str
    metrics: TriageCalibrationMetrics
    outcomes: tuple[TriageCalibrationCaseOutcome, ...]
    known_limits: tuple[str, ...] = Field(min_length=1)


def run_typed_triage_calibration(
    *,
    service: TriageService,
    cases: tuple[EvalCase, ...],
) -> TriageCalibrationReport:
    """Run only calibration cases through the non-executing packet boundary."""

    outcomes: list[TriageCalibrationCaseOutcome] = []
    for case in cases:
        request = TriageRequest(
            request_id=uuid5(NAMESPACE_URL, f"typed-triage:{case.eval_id}"),
            trace_id=uuid5(NAMESPACE_URL, f"typed-triage-trace:{case.eval_id}"),
            input_summary=case.input_summary,
            observed_facts=case.observed_facts,
            provider_available=case.provider_available,
        )
        packet = service.triage(request)
        matches = packet.policy_decision.decision_state is case.expected_decision_state
        labels: list[str] = []
        if not matches:
            labels.append("decision_state_mismatch")
        if packet.procedure_execution_authorized:
            labels.append("procedure_execution_authorized")
        if (
            packet.semantic_advisory.status is SemanticAdvisoryStatus.PROVIDER_DEGRADED
            and packet.policy_decision.decision_state is not EvidenceDecisionState.PROVIDER_DEGRADED
        ):
            labels.append("provider_degraded_alignment_failure")
        outcomes.append(
            TriageCalibrationCaseOutcome(
                eval_id=case.eval_id,
                expected_decision_state=case.expected_decision_state,
                observed_decision_state=packet.policy_decision.decision_state,
                decision_state_matches=matches,
                semantic_advisory_status=packet.semantic_advisory.status,
                policy_retained_precedent_ids=packet.policy_decision.retained_precedent_ids,
                semantic_candidate_ids=tuple(
                    candidate.incident_id for candidate in packet.semantic_advisory.candidate_evidence
                ),
                procedure_execution_authorized=packet.procedure_execution_authorized,
                failure_labels=tuple(labels),
            )
        )

    total = len(outcomes)
    matched = sum(outcome.decision_state_matches for outcome in outcomes)
    automatic = sum(outcome.procedure_execution_authorized for outcome in outcomes)
    metrics = TriageCalibrationMetrics(
        calibration_case_count=total,
        matching_decision_state_count=matched,
        decision_state_match_rate=round(matched / total, 4),
        semantic_advisory_available_count=sum(
            outcome.semantic_advisory_status is SemanticAdvisoryStatus.AVAILABLE
            for outcome in outcomes
        ),
        provider_degraded_packet_count=sum(
            outcome.semantic_advisory_status is SemanticAdvisoryStatus.PROVIDER_DEGRADED
            for outcome in outcomes
        ),
        procedure_execution_authorized_count=automatic,
    )
    passed = matched == total and automatic == 0
    return TriageCalibrationReport(
        status="passed" if passed else "blocked",
        generated_at=datetime.now(UTC),
        calibration_case_count=total,
        policy_candidate_source="deterministic_keyword_top_5",
        semantic_advisory_source="local_sie_dense_top_5",
        metrics=metrics,
        outcomes=tuple(outcomes),
        known_limits=(
            "Calibration-only report; held-out cases are not loaded or scored.",
            "The anti-anchoring policy consumes deterministic keyword candidates only in this slice.",
            "Local-SIE dense candidates are advisory evidence and cannot alter policy decision state, retained precedents, missing facts, or procedure eligibility.",
            "No packet authorizes procedure execution, automated remediation, or root-cause determination.",
            "This report evaluates packet control behavior, not retrieval-quality superiority or production readiness.",
        ),
    )


def write_typed_triage_report(
    report: TriageCalibrationReport,
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write portable machine-readable and reviewer-readable evidence."""

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _render_markdown(report: TriageCalibrationReport) -> str:
    metrics = report.metrics
    lines = [
        "# Typed Triage Calibration Report",
        "",
        "## Scope",
        "",
        "This report runs calibration fixtures through the typed triage packet boundary only.",
        "It does not load held-out cases, promote a retriever, select an authoritative representative, authorize a procedure, or execute a remediation.",
        "",
        "## Control boundary",
        "",
        f"- Policy candidate source: `{report.policy_candidate_source}`",
        f"- Semantic advisory source: `{report.semantic_advisory_source}`",
        "- Semantic evidence is advisory-only and cannot alter the active anti-anchoring policy result.",
        "- Procedure execution authorized: `false` for every valid packet.",
        "",
        "## Results",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Calibration cases | {metrics.calibration_case_count} |",
        f"| Matching decision states | {metrics.matching_decision_state_count}/{metrics.calibration_case_count} |",
        f"| Decision-state match rate | {metrics.decision_state_match_rate:.4f} |",
        f"| Semantic advisory available | {metrics.semantic_advisory_available_count}/{metrics.calibration_case_count} |",
        f"| Provider-degraded packets | {metrics.provider_degraded_packet_count} |",
        f"| Procedure execution authorized | {metrics.procedure_execution_authorized_count} |",
        "",
        "## Decision",
        "",
        (
            "- Result: packet control gate passed."
            if report.status == "passed"
            else "- Result: packet control gate blocked; inspect case outcomes before integration."
        ),
        "- This does not promote a retrieval path; semantic evidence remains advisory while retrieval and policy evaluation continue separately.",
        "",
        "## Case outcomes",
        "",
        "| Eval case | Expected state | Observed state | Match | Semantic advisory | Policy precedents | Semantic candidates | Failure labels |",
        "|---|---|---|---:|---|---|---|---|",
    ]
    for outcome in report.outcomes:
        lines.append(
            "| {eval_id} | {expected} | {observed} | {match} | {advisory} | {policy_ids} | {semantic_ids} | {labels} |".format(
                eval_id=outcome.eval_id,
                expected=outcome.expected_decision_state.value,
                observed=outcome.observed_decision_state.value,
                match=str(outcome.decision_state_matches).lower(),
                advisory=outcome.semantic_advisory_status.value,
                policy_ids=", ".join(outcome.policy_retained_precedent_ids) or "N/A",
                semantic_ids=", ".join(outcome.semantic_candidate_ids) or "N/A",
                labels=", ".join(outcome.failure_labels) or "none",
            )
        )
    lines.extend(["", "## Known limits", ""])
    lines.extend(f"- {limit}" for limit in report.known_limits)
    lines.append("")
    return "\n".join(lines)
