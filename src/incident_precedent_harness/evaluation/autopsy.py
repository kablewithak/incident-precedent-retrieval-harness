"""Trace-only autopsy for an immutable held-out baseline.

This module consumes the already committed held-out report, verifies the frozen
fixture manifest, and maps blocked outcomes back to typed incident and intake
facts. It does not rerun retrieval, alter policy, write evaluation results, or
modify frozen cases.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from incident_precedent_harness.domain.incident_data import EvalCase, HistoricalIncidentCard
from incident_precedent_harness.domain.incident_enums import (
    EvidenceDecisionState,
    IncidentFamily,
    RequiredVerificationFact,
    VerificationFactStatus,
)
from incident_precedent_harness.evaluation.heldout import (
    HELDOUT_DIRECTORY,
    HeldoutEvaluationReport,
    verify_heldout_freeze,
)

BASELINE_JSON_RELATIVE_PATH = (
    Path("evidence_vault") / "reports" / "heldout-tranche-01-keyword-policy.json"
)
AUTOPSY_JSON_RELATIVE_PATH = (
    Path("evidence_vault") / "reports" / "heldout-tranche-01-failure-autopsy.json"
)
AUTOPSY_MARKDOWN_RELATIVE_PATH = (
    Path("docs") / "reports" / "heldout-tranche-01-failure-autopsy.md"
)


class HeldoutBaselineIntegrityError(RuntimeError):
    """Raised when the baseline cannot safely be treated as immutable evidence."""


class FactDisposition(BaseModel):
    """One required fact and its recorded status for a candidate-card trace."""

    fact: RequiredVerificationFact
    status: VerificationFactStatus


class CandidateEvidenceTrace(BaseModel):
    """A fact-level trace for one ranked or retained historical incident."""

    incident_id: str
    incident_family: IncidentFamily
    ranking_position: int | None = Field(default=None, ge=1)
    retained: bool
    required_facts: tuple[FactDisposition, ...]
    confirmed_required_fact_count: int = Field(ge=0)
    contradicted_required_fact_count: int = Field(ge=0)
    unknown_required_fact_count: int = Field(ge=0)


class FailureAutopsyFinding(BaseModel):
    """One blocked held-out case with evidence and a non-patch conclusion."""

    eval_id: str
    expected_decision_state: EvidenceDecisionState
    actual_decision_state: EvidenceDecisionState
    failure_labels: tuple[str, ...] = Field(min_length=1)
    ranked_candidate_ids: tuple[str, ...]
    retained_precedent_ids: tuple[str, ...]
    expected_acceptable_precedent_ids: tuple[str, ...]
    unexpected_retained_precedent_ids: tuple[str, ...]
    candidate_traces: tuple[CandidateEvidenceTrace, ...] = Field(min_length=1)
    diagnosis_category: Literal[
        "false_conflict_from_contextual_signal",
        "within_family_representative_ambiguity",
        "trace_review_required",
    ]
    diagnosis: str = Field(min_length=1)
    intervention_boundary: str = Field(min_length=1)


class HeldoutFailureAutopsyReport(BaseModel):
    """A trace-only, write-once explanation of a blocked held-out baseline."""

    report_kind: str = "heldout_failure_autopsy"
    generated_at: datetime
    baseline_report_path: str
    baseline_report_sha256: str
    baseline_repository_revision: str | None
    heldout_manifest_path: str
    heldout_manifest_sha256: str
    verified_heldout_case_count: int = Field(ge=1)
    baseline_gate_status: Literal["blocked"]
    blocked_case_ids: tuple[str, ...] = Field(min_length=1)
    findings: tuple[FailureAutopsyFinding, ...] = Field(min_length=1)
    non_claims: tuple[str, ...] = Field(min_length=1)


def build_heldout_failure_autopsy(
    *,
    repository_root: Path,
    incidents: tuple[HistoricalIncidentCard, ...],
    cases: tuple[EvalCase, ...],
    baseline_relative_path: Path = BASELINE_JSON_RELATIVE_PATH,
) -> HeldoutFailureAutopsyReport:
    """Build a trace report from recorded baseline evidence without scoring anew."""

    root = repository_root.resolve()
    freeze = verify_heldout_freeze(root)
    baseline_path = root / baseline_relative_path
    baseline = _load_blocked_baseline(baseline_path)

    case_by_id = {case.eval_id: case for case in cases}
    incident_by_id = {incident.incident_id: incident for incident in incidents}
    if set(case_by_id) != set(freeze.verified_case_ids):
        raise HeldoutBaselineIntegrityError(
            "Autopsy cases differ from the manifest-verified held-out case IDs."
        )

    blocked_outcomes = tuple(
        outcome
        for outcome in baseline.outcomes
        if not outcome.case_contract_passed
    )
    if tuple(outcome.eval_id for outcome in blocked_outcomes) != baseline.metrics.blocked_case_ids:
        raise HeldoutBaselineIntegrityError(
            "Baseline blocked_case_ids do not match its case-level contract outcomes."
        )

    findings = tuple(
        _build_finding(
            outcome=outcome,
            case=case_by_id[outcome.eval_id],
            incident_by_id=incident_by_id,
        )
        for outcome in blocked_outcomes
    )

    return HeldoutFailureAutopsyReport(
        generated_at=datetime.now(UTC),
        baseline_report_path=baseline_relative_path.as_posix(),
        baseline_report_sha256=_sha256(baseline_path),
        baseline_repository_revision=baseline.configuration.repository_revision,
        heldout_manifest_path=freeze.manifest_path,
        heldout_manifest_sha256=freeze.manifest_sha256,
        verified_heldout_case_count=freeze.case_count,
        baseline_gate_status=baseline.promotion_gate.status,
        blocked_case_ids=baseline.metrics.blocked_case_ids,
        findings=findings,
        non_claims=(
            "This report reads recorded held-out evidence; it does not rerun retrieval or policy scoring.",
            "Frozen held-out cases, labels, hashes, ranking configuration, and decision policy are not modified by this autopsy.",
            "The intervention boundaries are hypotheses for calibration-only work, not proof that a fix will pass held-out evaluation.",
            "This report does not establish semantic retrieval quality, live SIE extraction readiness, customer-data readiness, or production incident-response safety.",
        ),
    )


def write_heldout_failure_autopsy(
    report: HeldoutFailureAutopsyReport,
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write one immutable autopsy evidence pair without overwriting prior trace."""

    existing = tuple(path for path in (json_path, markdown_path) if path.exists())
    if existing:
        rendered = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            "Held-out failure autopsy already exists and will not be overwritten: "
            f"{rendered}. Preserve this trace and create a separately versioned autopsy if needed."
        )

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _load_blocked_baseline(path: Path) -> HeldoutEvaluationReport:
    if not path.is_file():
        raise HeldoutBaselineIntegrityError(
            f"Committed held-out baseline is missing: {path}"
        )
    try:
        report = HeldoutEvaluationReport.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise HeldoutBaselineIntegrityError(
            "Committed held-out baseline cannot be parsed as a valid evaluation report."
        ) from error

    if report.promotion_gate.status != "blocked":
        raise HeldoutBaselineIntegrityError(
            "Failure autopsy requires a blocked held-out baseline; received a passing report."
        )
    if not report.freeze_verification.verified:
        raise HeldoutBaselineIntegrityError(
            "Failure autopsy requires a manifest-verified held-out baseline."
        )
    if not report.metrics.blocked_case_ids:
        raise HeldoutBaselineIntegrityError(
            "Failure autopsy requires at least one blocked held-out case."
        )
    return report


def _build_finding(
    *,
    outcome,
    case: EvalCase,
    incident_by_id: dict[str, HistoricalIncidentCard],
) -> FailureAutopsyFinding:
    candidate_ids = _unique_in_order(
        (*outcome.ranked_candidate_ids, *outcome.retained_precedent_ids)
    )
    candidate_traces = tuple(
        _candidate_trace(
            incident=incident_by_id[incident_id],
            case=case,
            ranking_position=_ranking_position(incident_id, outcome.ranked_candidate_ids),
            retained=incident_id in outcome.retained_precedent_ids,
        )
        for incident_id in candidate_ids
        if incident_id in incident_by_id
    )
    if not candidate_traces:
        raise HeldoutBaselineIntegrityError(
            f"Blocked case {outcome.eval_id} has no traceable incident candidates."
        )

    category, diagnosis, boundary = _diagnose(
        outcome=outcome,
        case=case,
        incident_by_id=incident_by_id,
        candidate_traces=candidate_traces,
    )
    return FailureAutopsyFinding(
        eval_id=outcome.eval_id,
        expected_decision_state=outcome.expected_decision_state,
        actual_decision_state=outcome.actual_decision_state,
        failure_labels=outcome.failure_labels,
        ranked_candidate_ids=outcome.ranked_candidate_ids,
        retained_precedent_ids=outcome.retained_precedent_ids,
        expected_acceptable_precedent_ids=outcome.expected_acceptable_precedent_ids,
        unexpected_retained_precedent_ids=outcome.unexpected_retained_precedent_ids,
        candidate_traces=candidate_traces,
        diagnosis_category=category,
        diagnosis=diagnosis,
        intervention_boundary=boundary,
    )


def _candidate_trace(
    *,
    incident: HistoricalIncidentCard,
    case: EvalCase,
    ranking_position: int | None,
    retained: bool,
) -> CandidateEvidenceTrace:
    status_by_fact = {observation.fact: observation.status for observation in case.observed_facts}
    dispositions = tuple(
        FactDisposition(
            fact=fact,
            status=status_by_fact.get(fact, VerificationFactStatus.UNKNOWN),
        )
        for fact in incident.required_verification_facts
    )
    return CandidateEvidenceTrace(
        incident_id=incident.incident_id,
        incident_family=incident.incident_family,
        ranking_position=ranking_position,
        retained=retained,
        required_facts=dispositions,
        confirmed_required_fact_count=sum(
            disposition.status is VerificationFactStatus.CONFIRMED
            for disposition in dispositions
        ),
        contradicted_required_fact_count=sum(
            disposition.status is VerificationFactStatus.CONTRADICTED
            for disposition in dispositions
        ),
        unknown_required_fact_count=sum(
            disposition.status is VerificationFactStatus.UNKNOWN
            for disposition in dispositions
        ),
    )


def _diagnose(
    *,
    outcome,
    case: EvalCase,
    incident_by_id: dict[str, HistoricalIncidentCard],
    candidate_traces: tuple[CandidateEvidenceTrace, ...],
) -> tuple[str, str, str]:
    direct_pool_facts = {
        RequiredVerificationFact.DATABASE_CONNECTION_POOL_UTILIZATION,
        RequiredVerificationFact.DATABASE_CONNECTION_ACQUIRE_LATENCY,
    }
    contextual_pool_fact = RequiredVerificationFact.ACTIVE_DATABASE_CONNECTIONS
    status_by_fact = {observation.fact: observation.status for observation in case.observed_facts}
    unexpected_cards = tuple(
        incident_by_id[incident_id]
        for incident_id in outcome.unexpected_retained_precedent_ids
        if incident_id in incident_by_id
    )

    if (
        outcome.expected_decision_state is EvidenceDecisionState.EVIDENCE_FOUND
        and outcome.actual_decision_state is EvidenceDecisionState.EVIDENCE_FOUND_WITH_CONFLICT
        and any(card.incident_family is IncidentFamily.CONNECTION_POOL_EXHAUSTION for card in unexpected_cards)
        and all(
            status_by_fact.get(fact) is VerificationFactStatus.CONTRADICTED
            for fact in direct_pool_facts
        )
        and status_by_fact.get(contextual_pool_fact) is VerificationFactStatus.CONFIRMED
    ):
        return (
            "false_conflict_from_contextual_signal",
            "A connection-pool precedent was retained even though both direct pool signals were contradicted. "
            "The remaining confirmed active-connection fact is contextual evidence, not sufficient direct evidence of pool exhaustion. "
            "That over-retention manufactured a conflict and withheld the expected migration-lock procedure.",
            "Calibration-only intervention: require at least one direct connection-pool signal "
            "(pool utilization or acquisition latency) before admitting the connection-pool family. "
            "Do not change frozen held-out cases or rerun this tranche until calibration regressions are reviewed.",
        )

    expected_cards = tuple(
        incident_by_id[incident_id]
        for incident_id in outcome.expected_acceptable_precedent_ids
        if incident_id in incident_by_id
    )
    unexpected_card_families = {card.incident_family for card in unexpected_cards}
    expected_card_families = {card.incident_family for card in expected_cards}
    if unexpected_card_families & expected_card_families:
        matching_traces = tuple(
            trace
            for trace in candidate_traces
            if trace.incident_family in unexpected_card_families & expected_card_families
        )
        return (
            "within_family_representative_ambiguity",
            "The decision state retained the intended incident-family direction, but lexical rank selected an unexpected representative within that same family. "
            "The current policy keeps the first compatible card per family, so its final evidence card is coupled to retriever order rather than a reviewed within-family selection contract. "
            f"Relevant fact-coverage traces: {_coverage_summary(matching_traces)}.",
            "Design intervention, not a tie-break patch: define a reviewed within-family evidence-selection contract or add a discriminative structured fact. "
            "Do not use incident ID order, raw lexical rank, or held-out labels as a hidden selector.",
        )

    return (
        "trace_review_required",
        "The recorded outcome violates the held-out contract, but the current trace does not meet a pre-approved narrow diagnosis pattern. "
        "It requires a separate design review before any policy or retrieval change.",
        "Preserve this baseline and add a calibration-only diagnostic case before implementing an intervention.",
    )


def _coverage_summary(traces: tuple[CandidateEvidenceTrace, ...]) -> str:
    if not traces:
        return "no matching family traces available"
    return "; ".join(
        f"{trace.incident_id}: confirmed={trace.confirmed_required_fact_count}, "
        f"contradicted={trace.contradicted_required_fact_count}, unknown={trace.unknown_required_fact_count}"
        for trace in traces
    )


def _ranking_position(incident_id: str, ranked_ids: tuple[str, ...]) -> int | None:
    try:
        return ranked_ids.index(incident_id) + 1
    except ValueError:
        return None


def _unique_in_order(values: tuple[str, ...]) -> tuple[str, ...]:
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return tuple(unique)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render_markdown(report: HeldoutFailureAutopsyReport) -> str:
    lines = [
        "# Held-Out Tranche 01 — Failure Autopsy",
        "",
        "## Scope",
        "",
        "This trace reads the committed blocked held-out baseline. It does not rerun retrieval or policy, modify frozen inputs, or claim an intervention result.",
        "",
        "## Baseline linkage",
        "",
        f"- Baseline report: `{report.baseline_report_path}`",
        f"- Baseline SHA-256: `{report.baseline_report_sha256}`",
        f"- Baseline repository revision: `{report.baseline_repository_revision or 'unavailable'}`",
        f"- Held-out manifest: `{report.heldout_manifest_path}`",
        f"- Held-out manifest SHA-256: `{report.heldout_manifest_sha256}`",
        f"- Verified frozen cases: `{report.verified_heldout_case_count}`",
        f"- Baseline gate: **{report.baseline_gate_status.upper()}**",
        "",
        "## Findings",
        "",
    ]
    for finding in report.findings:
        lines.extend(
            [
                f"### {finding.eval_id}: {finding.diagnosis_category}",
                "",
                f"- Expected state: `{finding.expected_decision_state.value}`",
                f"- Actual state: `{finding.actual_decision_state.value}`",
                f"- Failure labels: `{', '.join(finding.failure_labels)}`",
                f"- Ranked IDs: `{', '.join(finding.ranked_candidate_ids) or 'none'}`",
                f"- Retained IDs: `{', '.join(finding.retained_precedent_ids) or 'none'}`",
                f"- Expected acceptable IDs: `{', '.join(finding.expected_acceptable_precedent_ids) or 'none'}`",
                f"- Unexpected retained IDs: `{', '.join(finding.unexpected_retained_precedent_ids) or 'none'}`",
                "",
                "#### Candidate fact trace",
                "",
                "| Incident | Family | Rank | Retained | Confirmed required facts | Contradicted required facts | Unknown required facts |",
                "|---|---|---:|---:|---:|---:|---:|",
            ]
        )
        for trace in finding.candidate_traces:
            lines.append(
                f"| {trace.incident_id} | {trace.incident_family.value} | "
                f"{trace.ranking_position if trace.ranking_position is not None else '—'} | "
                f"{str(trace.retained).lower()} | {trace.confirmed_required_fact_count} | "
                f"{trace.contradicted_required_fact_count} | {trace.unknown_required_fact_count} |"
            )
        lines.extend(
            [
                "",
                "#### Diagnosis",
                "",
                finding.diagnosis,
                "",
                "#### Intervention boundary",
                "",
                finding.intervention_boundary,
                "",
            ]
        )
    lines.extend(["## Non-claims", ""])
    lines.extend(f"- {claim}" for claim in report.non_claims)
    lines.append("")
    return "\n".join(lines)
