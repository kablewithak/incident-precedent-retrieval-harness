"""Write-once comparison of a documented held-out intervention against its baseline."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.domain.incident_data import (
    CandidateInvestigationProcedure,
    EvalCase,
    HistoricalIncidentCard,
)
from incident_precedent_harness.domain.incident_enums import EvidenceDecisionState
from incident_precedent_harness.evaluation.heldout import (
    HeldoutEvaluationMetrics,
    HeldoutEvaluationReport,
    HeldoutManifestIntegrityError,
    run_frozen_heldout_evaluation,
)
from incident_precedent_harness.retrieval.keyword import KeywordRetriever

BASELINE_JSON_RELATIVE_PATH = (
    Path("evidence_vault") / "reports" / "heldout-tranche-01-keyword-policy.json"
)
COMPARISON_JSON_RELATIVE_PATH = (
    Path("evidence_vault")
    / "reports"
    / "heldout-tranche-01-direct-signal-comparison.json"
)
COMPARISON_MARKDOWN_RELATIVE_PATH = (
    Path("docs") / "reports" / "heldout-tranche-01-direct-signal-comparison.md"
)
HANDOVER_MARKDOWN_RELATIVE_PATH = (
    Path("docs")
    / "handover"
    / "Incident_Precedent_Retrieval_Harness_Handover_002_Post_Intervention_Comparison.md"
)


class HeldoutComparisonIntegrityError(RuntimeError):
    """Raised when a comparison cannot be anchored to a valid baseline."""


class BaselineEvidenceReference(BaseModel):
    """Immutable reference to the pre-intervention held-out baseline."""

    report_path: str
    report_sha256: str
    repository_revision: str | None
    promotion_gate_status: Literal["passed", "blocked"]
    manifest_sha256: str


class HeldoutOutcomeDelta(BaseModel):
    """Case-level difference between immutable baseline and post-intervention result."""

    eval_id: str
    baseline_decision_state: EvidenceDecisionState
    comparison_decision_state: EvidenceDecisionState
    baseline_retained_precedent_ids: tuple[str, ...]
    comparison_retained_precedent_ids: tuple[str, ...]
    baseline_candidate_procedure_ids: tuple[str, ...]
    comparison_candidate_procedure_ids: tuple[str, ...]
    baseline_case_contract_passed: bool
    comparison_case_contract_passed: bool
    baseline_failure_labels: tuple[str, ...]
    comparison_failure_labels: tuple[str, ...]
    change_class: Literal[
        "improved",
        "regressed",
        "changed_not_promoted",
        "unchanged",
    ]
    changed_dimensions: tuple[str, ...]


class HeldoutComparisonSummary(BaseModel):
    """Counts that describe the effect of one predeclared intervention."""

    improved_case_ids: tuple[str, ...]
    regressed_case_ids: tuple[str, ...]
    changed_not_promoted_case_ids: tuple[str, ...]
    unchanged_case_ids: tuple[str, ...]
    conclusion: Literal[
        "promoted",
        "improved_but_blocked",
        "blocked_without_clear_improvement",
        "regressed",
    ]


class HeldoutComparisonReport(BaseModel):
    """A write-once, reviewer-readable intervention comparison."""

    report_kind: str = "heldout_direct_signal_intervention_comparison"
    generated_at: datetime
    intervention_id: str = "ADR-0008_connection_pool_direct_signal_admission"
    baseline_evidence: BaselineEvidenceReference
    baseline_metrics: HeldoutEvaluationMetrics
    comparison_run: HeldoutEvaluationReport
    comparison_summary: HeldoutComparisonSummary
    outcome_deltas: tuple[HeldoutOutcomeDelta, ...]
    non_claims: tuple[str, ...] = Field(min_length=1)


def build_heldout_direct_signal_comparison(
    *,
    repository_root: Path,
    retriever: KeywordRetriever,
    policy: AntiAnchoringDecisionPolicy,
    incidents: tuple[HistoricalIncidentCard, ...],
    procedures: tuple[CandidateInvestigationProcedure, ...],
    cases: tuple[EvalCase, ...],
    top_k: int = 5,
) -> HeldoutComparisonReport:
    """Run the predeclared comparison without mutating baseline or held-out fixtures."""

    root = repository_root.resolve()
    baseline_path = root / BASELINE_JSON_RELATIVE_PATH
    baseline = _load_baseline_report(baseline_path)

    try:
        comparison_run = run_frozen_heldout_evaluation(
            repository_root=root,
            retriever=retriever,
            policy=policy,
            incidents=incidents,
            procedures=procedures,
            cases=cases,
            top_k=top_k,
        )
    except HeldoutManifestIntegrityError as error:
        raise HeldoutComparisonIntegrityError(
            "Held-out comparison refused because frozen-tranche verification failed."
        ) from error

    if baseline.freeze_verification.manifest_sha256 != comparison_run.freeze_verification.manifest_sha256:
        raise HeldoutComparisonIntegrityError(
            "Comparison refused because the baseline and current run reference different held-out manifests."
        )
    if baseline.freeze_verification.verified_case_ids != comparison_run.freeze_verification.verified_case_ids:
        raise HeldoutComparisonIntegrityError(
            "Comparison refused because baseline and current run contain different held-out case IDs."
        )

    deltas = _build_deltas(baseline=baseline, comparison=comparison_run)
    summary = _build_summary(deltas=deltas, comparison=comparison_run)
    return HeldoutComparisonReport(
        generated_at=datetime.now(UTC),
        baseline_metrics=baseline.metrics,
        baseline_evidence=BaselineEvidenceReference(
            report_path=BASELINE_JSON_RELATIVE_PATH.as_posix(),
            report_sha256=_sha256(baseline_path),
            repository_revision=baseline.configuration.repository_revision,
            promotion_gate_status=baseline.promotion_gate.status,
            manifest_sha256=baseline.freeze_verification.manifest_sha256,
        ),
        comparison_run=comparison_run,
        comparison_summary=summary,
        outcome_deltas=deltas,
        non_claims=(
            "This comparison evaluates one predeclared deterministic policy intervention against the same frozen 12-case tranche.",
            "The frozen case inputs, labels, hashes, baseline evidence, lexical retriever, top-k setting, and promotion thresholds are not changed by this comparison.",
            "A comparison improvement does not prove semantic retrieval quality, live SIE extraction readiness, customer-data readiness, or production incident-response safety.",
            "A remaining blocked gate is not a license to tune on held-out labels; the next intervention must be justified through a separate calibration-only design step.",
        ),
    )


def write_heldout_direct_signal_comparison(
    report: HeldoutComparisonReport,
    *,
    json_path: Path,
    markdown_path: Path,
    handover_path: Path,
) -> None:
    """Persist one comparison report and its handover checkpoint exactly once."""

    existing = tuple(
        path for path in (json_path, markdown_path, handover_path) if path.exists()
    )
    if existing:
        rendered = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            "Held-out comparison evidence already exists and will not be overwritten: "
            f"{rendered}. Preserve this comparison and create a new documented experiment."
        )

    for path in (json_path, markdown_path, handover_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    handover_path.write_text(_render_handover(report), encoding="utf-8")


def _load_baseline_report(path: Path) -> HeldoutEvaluationReport:
    if not path.is_file():
        raise HeldoutComparisonIntegrityError(
            f"Held-out comparison requires the committed baseline artifact: {path}"
        )
    try:
        report = HeldoutEvaluationReport.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise HeldoutComparisonIntegrityError(
            "Held-out comparison baseline cannot be parsed as a valid held-out report."
        ) from error
    if report.report_kind != "heldout_keyword_policy_evaluation":
        raise HeldoutComparisonIntegrityError(
            "Held-out comparison baseline report kind is not the expected keyword-policy evaluation."
        )
    if not report.freeze_verification.verified:
        raise HeldoutComparisonIntegrityError(
            "Held-out comparison baseline did not record successful freeze verification."
        )
    return report


def _build_deltas(
    *,
    baseline: HeldoutEvaluationReport,
    comparison: HeldoutEvaluationReport,
) -> tuple[HeldoutOutcomeDelta, ...]:
    baseline_by_id = {outcome.eval_id: outcome for outcome in baseline.outcomes}
    comparison_by_id = {outcome.eval_id: outcome for outcome in comparison.outcomes}
    if set(baseline_by_id) != set(comparison_by_id):
        raise HeldoutComparisonIntegrityError(
            "Comparison refused because baseline and current report outcomes do not share the same case IDs."
        )

    deltas: list[HeldoutOutcomeDelta] = []
    for eval_id in sorted(baseline_by_id):
        prior = baseline_by_id[eval_id]
        current = comparison_by_id[eval_id]
        changed_dimensions = _changed_dimensions(prior=prior, current=current)
        change_class = _classify_change(prior=prior, current=current)
        deltas.append(
            HeldoutOutcomeDelta(
                eval_id=eval_id,
                baseline_decision_state=prior.actual_decision_state,
                comparison_decision_state=current.actual_decision_state,
                baseline_retained_precedent_ids=prior.retained_precedent_ids,
                comparison_retained_precedent_ids=current.retained_precedent_ids,
                baseline_candidate_procedure_ids=prior.candidate_procedure_ids,
                comparison_candidate_procedure_ids=current.candidate_procedure_ids,
                baseline_case_contract_passed=prior.case_contract_passed,
                comparison_case_contract_passed=current.case_contract_passed,
                baseline_failure_labels=prior.failure_labels,
                comparison_failure_labels=current.failure_labels,
                change_class=change_class,
                changed_dimensions=changed_dimensions,
            )
        )
    return tuple(deltas)


def _changed_dimensions(*, prior: object, current: object) -> tuple[str, ...]:
    dimensions: list[str] = []
    checks = (
        ("decision_state", prior.actual_decision_state, current.actual_decision_state),
        ("retained_precedents", prior.retained_precedent_ids, current.retained_precedent_ids),
        ("candidate_procedures", prior.candidate_procedure_ids, current.candidate_procedure_ids),
        ("missing_facts", prior.actual_missing_facts, current.actual_missing_facts),
        ("case_contract", prior.case_contract_passed, current.case_contract_passed),
        ("failure_labels", prior.failure_labels, current.failure_labels),
    )
    for name, before, after in checks:
        if before != after:
            dimensions.append(name)
    return tuple(dimensions)


def _classify_change(*, prior: object, current: object) -> Literal[
    "improved", "regressed", "changed_not_promoted", "unchanged"
]:
    if not prior.case_contract_passed and current.case_contract_passed:
        return "improved"
    if prior.case_contract_passed and not current.case_contract_passed:
        return "regressed"
    if prior.failure_labels and len(current.failure_labels) < len(prior.failure_labels):
        return "changed_not_promoted"
    if prior.failure_labels and len(current.failure_labels) > len(prior.failure_labels):
        return "regressed"
    if _changed_dimensions(prior=prior, current=current):
        return "changed_not_promoted"
    return "unchanged"


def _build_summary(
    *,
    deltas: tuple[HeldoutOutcomeDelta, ...],
    comparison: HeldoutEvaluationReport,
) -> HeldoutComparisonSummary:
    improved = tuple(delta.eval_id for delta in deltas if delta.change_class == "improved")
    regressed = tuple(delta.eval_id for delta in deltas if delta.change_class == "regressed")
    changed_not_promoted = tuple(
        delta.eval_id for delta in deltas if delta.change_class == "changed_not_promoted"
    )
    unchanged = tuple(delta.eval_id for delta in deltas if delta.change_class == "unchanged")

    if regressed:
        conclusion: Literal[
            "promoted",
            "improved_but_blocked",
            "blocked_without_clear_improvement",
            "regressed",
        ] = "regressed"
    elif comparison.promotion_gate.status == "passed":
        conclusion = "promoted"
    elif improved:
        conclusion = "improved_but_blocked"
    else:
        conclusion = "blocked_without_clear_improvement"

    return HeldoutComparisonSummary(
        improved_case_ids=improved,
        regressed_case_ids=regressed,
        changed_not_promoted_case_ids=changed_not_promoted,
        unchanged_case_ids=unchanged,
        conclusion=conclusion,
    )


def _render_markdown(report: HeldoutComparisonReport) -> str:
    baseline = report.baseline_evidence
    current = report.comparison_run
    baseline_metrics = _loadable_metric_table(report)
    summary = report.comparison_summary
    lines = [
        "# Held-Out Tranche 01 — Direct-Signal Intervention Comparison",
        "",
        "## Scope",
        "",
        "This report compares one predeclared calibration-validated policy intervention against the immutable keyword-plus-policy held-out baseline.",
        "The frozen inputs, labels, manifest, retriever, top-k setting, and gate thresholds are unchanged.",
        "",
        "## Evidence linkage",
        "",
        f"- Baseline report: `{baseline.report_path}`",
        f"- Baseline SHA-256: `{baseline.report_sha256}`",
        f"- Baseline repository revision: `{baseline.repository_revision or 'not recorded'}`",
        f"- Baseline gate: **{baseline.promotion_gate_status.upper()}**",
        f"- Frozen manifest SHA-256: `{baseline.manifest_sha256}`",
        f"- Comparison repository revision: `{current.configuration.repository_revision or 'not recorded'}`",
        f"- Comparison gate: **{current.promotion_gate.status.upper()}**",
        "",
        "## Metric comparison",
        "",
        "| Metric | Baseline | Comparison |",
        "|---|---:|---:|",
    ]
    for label, before, after in baseline_metrics:
        lines.append(f"| {label} | {before} | {after} |")

    lines.extend(
        [
            "",
            "## Case-level change",
            "",
            "| Eval case | Change | Baseline state | Comparison state | Baseline retained | Comparison retained |",
            "|---|---|---|---|---|---|",
        ]
    )
    for delta in report.outcome_deltas:
        if delta.change_class == "unchanged":
            continue
        lines.append(
            "| "
            f"{delta.eval_id} | {delta.change_class} | "
            f"{delta.baseline_decision_state.value} | {delta.comparison_decision_state.value} | "
            f"{', '.join(delta.baseline_retained_precedent_ids) or 'none'} | "
            f"{', '.join(delta.comparison_retained_precedent_ids) or 'none'} |"
        )
    if not any(delta.change_class != "unchanged" for delta in report.outcome_deltas):
        lines.append("| none | unchanged | — | — | — | — |")

    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"**{summary.conclusion.replace('_', ' ').upper()}**",
            "",
            f"- Improved cases: {', '.join(summary.improved_case_ids) or 'none'}",
            f"- Regressed cases: {', '.join(summary.regressed_case_ids) or 'none'}",
            f"- Changed but not promoted: {', '.join(summary.changed_not_promoted_case_ids) or 'none'}",
            f"- Remaining blocked cases: {', '.join(current.metrics.blocked_case_ids) or 'none'}",
            "",
            "## Non-claims",
            "",
        ]
    )
    lines.extend(f"- {claim}" for claim in report.non_claims)
    lines.append("")
    return "\n".join(lines)


def _loadable_metric_table(
    report: HeldoutComparisonReport,
) -> tuple[tuple[str, str, str], ...]:
    baseline_metrics = report.baseline_metrics
    current_metrics = report.comparison_run.metrics
    return (
        ("Decision-state accuracy", str(baseline_metrics.decision_state_accuracy), str(current_metrics.decision_state_accuracy)),
        ("Case-contract pass rate", str(baseline_metrics.case_contract_pass_rate), str(current_metrics.case_contract_pass_rate)),
        ("Acceptable-precedent coverage", _format_optional(baseline_metrics.acceptable_precedent_coverage), _format_optional(current_metrics.acceptable_precedent_coverage)),
        ("Procedure-contract accuracy", str(baseline_metrics.candidate_procedure_contract_accuracy), str(current_metrics.candidate_procedure_contract_accuracy)),
        ("False-operational matches", str(baseline_metrics.false_operational_match_count), str(current_metrics.false_operational_match_count)),
        ("Unexpected retained precedents", str(baseline_metrics.unexpected_retained_precedent_count), str(current_metrics.unexpected_retained_precedent_count)),
        ("Blocked cases", ", ".join(baseline_metrics.blocked_case_ids) or "none", ", ".join(current_metrics.blocked_case_ids) or "none"),
    )

def _render_handover(report: HeldoutComparisonReport) -> str:
    current = report.comparison_run
    summary = report.comparison_summary
    lines = [
        "# Incident Precedent Retrieval Harness — Handover 002",
        "",
        "## Boundary",
        "",
        "Post-intervention comparison boundary after ADR-0008. This handover is generated with the write-once comparison evidence; it is not a plan-only checkpoint.",
        "",
        "## Repository checkpoint",
        "",
        f"- Comparison configuration revision: `{current.configuration.repository_revision or 'not recorded'}`",
        f"- Frozen scope: `{current.freeze_verification.scope}`",
        f"- Held-out manifest SHA-256: `{current.freeze_verification.manifest_sha256}`",
        f"- Baseline evidence SHA-256: `{report.baseline_evidence.report_sha256}`",
        f"- Comparison gate: **{current.promotion_gate.status.upper()}**",
        f"- Comparison conclusion: **{summary.conclusion.replace('_', ' ').upper()}**",
        "",
        "## What changed",
        "",
        "ADR-0008 changed only connection-pool family admission: active database connections are contextual and cannot override two contradicted direct pool signals.",
        f"- Improved held-out cases: {', '.join(summary.improved_case_ids) or 'none'}",
        f"- Regressed held-out cases: {', '.join(summary.regressed_case_ids) or 'none'}",
        f"- Remaining blocked cases: {', '.join(current.metrics.blocked_case_ids) or 'none'}",
        "",
        "## Current evidence status",
        "",
        f"- Decision-state accuracy: `{current.metrics.decision_state_accuracy}`",
        f"- Case-contract pass rate: `{current.metrics.case_contract_pass_rate}`",
        f"- Acceptable-precedent coverage: `{_format_optional(current.metrics.acceptable_precedent_coverage)}`",
        f"- Unsafe precedents retained: `{current.metrics.false_operational_match_count}`",
        f"- Unexpected procedures surfaced: `{current.metrics.unsafe_procedure_surfacing_count}`",
        f"- Unexpected retained precedents: `{current.metrics.unexpected_retained_precedent_count}`",
        "",
        "## Architecture status",
        "",
        "```text",
        "structured synthetic intake facts",
        "  -> BM25-style local keyword retrieval",
        "  -> deterministic anti-anchoring policy",
        "  -> frozen held-out comparison gate",
        "```",
        "",
        "Local SIE encode and score capability were demonstrated earlier, but live extraction remains blocked. No SIE call, embedding, dense retrieval, or reranking is in the active evaluation path.",
        "",
        "## Remaining blocker",
        "",
        "The remaining held-out issue is within-family representative selection for connection-pool evidence. The current policy retains the first compatible candidate per family, coupling the selected evidence card to lexical rank. Do not patch this using incident-ID order, held-out labels, or raw lexical rank.",
        "",
        "## Next safe slice",
        "",
        "Define a reviewed within-family evidence-selection contract, create calibration-only diagnostics for that contract, and preserve the frozen held-out baseline and comparison artifacts unchanged until the calibration design is accepted.",
        "",
        "## Non-claims",
        "",
        "- This checkpoint does not prove semantic retrieval, reranking, extraction quality, customer-data readiness, or production safety.",
        "- A blocked comparison remains diagnostic evidence, not a reason to relax the gate or modify frozen labels.",
        "",
    ]
    return "\n".join(lines)


def _format_optional(value: float | None) -> str:
    return "not applicable" if value is None else str(value)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
