"""Write-once evaluation of the frozen held-out tranche.

This module intentionally evaluates a fixed keyword-plus-policy configuration. It
must not mutate the frozen fixture set, tune ranking, or change decision policy.
A blocked result is an evaluation outcome, not a runtime error.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

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
from incident_precedent_harness.retrieval.models import KeywordCandidate

HELDOUT_DIRECTORY = Path("data") / "evals" / "heldout"
FREEZE_MANIFEST_FILENAME = "HELDOUT_FREEZE_MANIFEST.json"
JSON_REPORT_RELATIVE_PATH = Path("evidence_vault") / "reports" / "heldout-tranche-01-keyword-policy.json"
MARKDOWN_REPORT_RELATIVE_PATH = Path("docs") / "reports" / "heldout-tranche-01-keyword-policy.md"


class HeldoutManifestIntegrityError(RuntimeError):
    """Raised before scoring when frozen-case integrity is not verifiable."""


class HeldoutFreezeManifest(BaseModel):
    """Minimal contract required to verify a frozen held-out tranche."""

    freeze_schema_version: str
    freeze_status: Literal["frozen"]
    frozen_on: str
    scope: str
    case_ids: tuple[str, ...] = Field(min_length=1)
    sha256_by_filename: dict[str, str] = Field(min_length=1)
    change_policy: str


class HeldoutFreezeVerification(BaseModel):
    """Traceable integrity result recorded with every held-out run."""

    manifest_path: str
    manifest_sha256: str
    scope: str
    case_count: int = Field(ge=1)
    verified_case_ids: tuple[str, ...]
    verified: bool = True


class EvaluatedConfiguration(BaseModel):
    """The exact provider-neutral configuration being measured."""

    retriever: str = "keyword_bm25_style_v1"
    decision_policy: str = "deterministic_anti_anchoring_policy_v1"
    top_k: int = Field(ge=1)
    corpus_incident_count: int = Field(ge=0)
    procedure_count: int = Field(ge=0)
    repository_revision: str | None = None


class HeldoutCaseOutcome(BaseModel):
    """One scored case with enough trace to review a gate decision."""

    eval_id: str
    expected_decision_state: EvidenceDecisionState
    actual_decision_state: EvidenceDecisionState
    ranked_candidate_ids: tuple[str, ...]
    retained_precedent_ids: tuple[str, ...]
    expected_acceptable_precedent_ids: tuple[str, ...]
    unexpected_retained_precedent_ids: tuple[str, ...]
    unsafe_precedent_ids: tuple[str, ...]
    expected_candidate_procedure_ids: tuple[str, ...]
    candidate_procedure_ids: tuple[str, ...]
    expected_missing_facts: tuple[str, ...]
    actual_missing_facts: tuple[str, ...]
    state_matches_expected: bool
    required_acceptable_precedents_present: bool
    unsafe_precedent_surfaced: bool
    candidate_procedure_contract_matches: bool
    missing_fact_contract_matches: bool
    abstention_contract_matches: bool
    case_contract_passed: bool
    failure_labels: tuple[str, ...]


class HeldoutEvaluationMetrics(BaseModel):
    """Metrics that make a pass/block decision inspectable."""

    scored_case_count: int = Field(ge=0)
    decision_state_accuracy: float = Field(ge=0, le=1)
    case_contract_pass_rate: float = Field(ge=0, le=1)
    acceptable_precedent_coverage: float | None = Field(default=None, ge=0, le=1)
    candidate_procedure_contract_accuracy: float = Field(ge=0, le=1)
    missing_fact_contract_accuracy: float = Field(ge=0, le=1)
    abstention_contract_accuracy: float | None = Field(default=None, ge=0, le=1)
    false_operational_match_count: int = Field(ge=0)
    unsafe_procedure_surfacing_count: int = Field(ge=0)
    unexpected_retained_precedent_count: int = Field(ge=0)
    blocked_case_ids: tuple[str, ...]


class HeldoutPromotionGate(BaseModel):
    """A strict, transparent gate for this frozen tranche only."""

    status: Literal["passed", "blocked"]
    required_decision_state_accuracy: float = 1.0
    required_case_contract_pass_rate: float = 1.0
    required_acceptable_precedent_coverage: float = 1.0
    required_candidate_procedure_contract_accuracy: float = 1.0
    required_missing_fact_contract_accuracy: float = 1.0
    required_abstention_contract_accuracy: float = 1.0
    maximum_false_operational_matches: int = 0
    maximum_unsafe_procedures: int = 0
    maximum_unexpected_retained_precedents: int = 0
    blocking_reasons: tuple[str, ...]


class HeldoutEvaluationReport(BaseModel):
    """Machine-readable, reviewable evidence from one frozen-tranche run."""

    report_kind: str = "heldout_keyword_policy_evaluation"
    generated_at: datetime
    freeze_verification: HeldoutFreezeVerification
    configuration: EvaluatedConfiguration
    metrics: HeldoutEvaluationMetrics
    promotion_gate: HeldoutPromotionGate
    outcomes: tuple[HeldoutCaseOutcome, ...]
    non_claims: tuple[str, ...] = Field(min_length=1)


def verify_heldout_freeze(repository_root: Path) -> HeldoutFreezeVerification:
    """Verify manifest status, file set, and every frozen case hash before scoring."""

    root = repository_root.resolve()
    heldout_directory = root / HELDOUT_DIRECTORY
    manifest_path = heldout_directory / FREEZE_MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise HeldoutManifestIntegrityError(
            f"Held-out freeze manifest is missing: {manifest_path}"
        )

    try:
        manifest = HeldoutFreezeManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as error:
        raise HeldoutManifestIntegrityError(
            "Held-out freeze manifest cannot be parsed as a valid frozen manifest."
        ) from error

    errors: list[str] = []
    manifest_filenames = set(manifest.sha256_by_filename)
    on_disk_filenames = {path.name for path in heldout_directory.glob("EVAL-*.json")}
    if on_disk_filenames != manifest_filenames:
        errors.append("held-out case file set differs from the frozen manifest")

    expected_ids = tuple(manifest.case_ids)
    manifest_ids = tuple(
        Path(filename).stem for filename in sorted(manifest.sha256_by_filename)
    )
    if set(expected_ids) != set(manifest_ids):
        errors.append("manifest case_ids differ from manifest filenames")

    for filename, expected_hash in manifest.sha256_by_filename.items():
        case_path = heldout_directory / filename
        if not case_path.is_file():
            errors.append(f"missing frozen case: {filename}")
            continue
        actual_hash = _sha256(case_path)
        if actual_hash != expected_hash:
            errors.append(f"hash mismatch for frozen case: {filename}")

    if errors:
        raise HeldoutManifestIntegrityError(
            "Held-out freeze verification failed: " + "; ".join(errors)
        )

    return HeldoutFreezeVerification(
        manifest_path=manifest_path.relative_to(root).as_posix(),
        manifest_sha256=_sha256(manifest_path),
        scope=manifest.scope,
        case_count=len(expected_ids),
        verified_case_ids=expected_ids,
    )


def run_frozen_heldout_evaluation(
    *,
    repository_root: Path,
    retriever: KeywordRetriever,
    policy: AntiAnchoringDecisionPolicy,
    incidents: tuple[HistoricalIncidentCard, ...],
    procedures: tuple[CandidateInvestigationProcedure, ...],
    cases: tuple[EvalCase, ...],
    top_k: int = 5,
) -> HeldoutEvaluationReport:
    """Score a verified held-out tranche without changing retrieval or policy behavior."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    root = repository_root.resolve()
    verification = verify_heldout_freeze(root)
    observed_case_ids = tuple(case.eval_id for case in cases)
    if set(observed_case_ids) != set(verification.verified_case_ids):
        raise HeldoutManifestIntegrityError(
            "Loaded held-out cases differ from the manifest-verified case IDs."
        )
    if any(case.split != "heldout" for case in cases):
        raise HeldoutManifestIntegrityError(
            "Held-out evaluator received a non-held-out case."
        )

    outcomes: list[HeldoutCaseOutcome] = []
    for case in cases:
        ranked: tuple[KeywordCandidate, ...] = ()
        if case.provider_available:
            ranked = retriever.rank(case.input_summary, top_k=top_k)
        result = policy.evaluate(
            intake=case,
            ranked_candidates=ranked,
            incidents=incidents,
            procedures=procedures,
        )
        outcomes.append(_outcome(case=case, ranked=ranked, result=result))

    outcome_tuple = tuple(outcomes)
    metrics = _metrics(outcome_tuple)
    gate = _promotion_gate(metrics)
    return HeldoutEvaluationReport(
        generated_at=datetime.now(UTC),
        freeze_verification=verification,
        configuration=EvaluatedConfiguration(
            top_k=top_k,
            corpus_incident_count=len(incidents),
            procedure_count=len(procedures),
            repository_revision=_resolve_git_revision(root),
        ),
        metrics=metrics,
        promotion_gate=gate,
        outcomes=outcome_tuple,
        non_claims=(
            "This is a 12-case held-out tranche, not the final planned 36-case evaluation set.",
            "A passed or blocked result applies only to the recorded keyword-plus-policy configuration.",
            "This report does not prove semantic retrieval quality, live SIE extraction readiness, customer-data readiness, or production incident-response safety.",
            "A blocked result is diagnostic evidence and must not be converted into a tuning loop by modifying frozen cases or their labels.",
        ),
    )


def write_heldout_report(
    report: HeldoutEvaluationReport,
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write report artifacts exactly once so later reruns cannot erase initial evidence."""

    existing = tuple(path for path in (json_path, markdown_path) if path.exists())
    if existing:
        rendered = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            "Held-out evidence already exists and will not be overwritten: "
            f"{rendered}. Preserve this run; create a documented comparison run instead."
        )

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _outcome(
    *,
    case: EvalCase,
    ranked: tuple[KeywordCandidate, ...],
    result: PolicyDecisionResult,
) -> HeldoutCaseOutcome:
    expected_precedents = tuple(case.acceptable_precedent_ids)
    retained = tuple(result.retained_precedent_ids)
    retained_set = set(retained)
    expected_set = set(expected_precedents)
    unsafe_set = set(case.unsafe_precedent_ids)
    actual_procedures = tuple(result.candidate_procedure_ids)
    expected_procedures = tuple(case.expected_candidate_procedure_ids)
    actual_missing = tuple(fact.value for fact in result.missing_critical_facts)
    expected_missing = tuple(fact.value for fact in case.expected_missing_facts)

    state_matches = result.decision_state is case.expected_decision_state
    required_precedents_present = expected_set.issubset(retained_set)
    unexpected_retained = tuple(sorted(retained_set - expected_set))
    unsafe_retained = tuple(sorted(retained_set & unsafe_set))
    procedure_matches = set(actual_procedures) == set(expected_procedures)
    missing_matches = set(actual_missing) == set(expected_missing)
    requires_empty_evidence = case.expected_decision_state in {
        EvidenceDecisionState.INSUFFICIENT_PRECEDENT,
        EvidenceDecisionState.PROVIDER_DEGRADED,
    }
    abstention_matches = (
        not requires_empty_evidence
        or (not retained and not actual_procedures)
    )

    failure_labels: list[str] = []
    if not state_matches:
        failure_labels.append("decision_state_mismatch")
    if not required_precedents_present:
        failure_labels.append("required_acceptable_precedent_missing")
    if unexpected_retained:
        failure_labels.append("unexpected_retained_precedent")
    if unsafe_retained:
        failure_labels.append("false_operational_match")
    if not procedure_matches:
        failure_labels.append("candidate_procedure_contract_mismatch")
    if not missing_matches:
        failure_labels.append("missing_fact_contract_mismatch")
    if not abstention_matches:
        failure_labels.append("abstention_contract_mismatch")

    return HeldoutCaseOutcome(
        eval_id=case.eval_id,
        expected_decision_state=case.expected_decision_state,
        actual_decision_state=result.decision_state,
        ranked_candidate_ids=tuple(candidate.incident_id for candidate in ranked),
        retained_precedent_ids=retained,
        expected_acceptable_precedent_ids=expected_precedents,
        unexpected_retained_precedent_ids=unexpected_retained,
        unsafe_precedent_ids=unsafe_retained,
        expected_candidate_procedure_ids=expected_procedures,
        candidate_procedure_ids=actual_procedures,
        expected_missing_facts=expected_missing,
        actual_missing_facts=actual_missing,
        state_matches_expected=state_matches,
        required_acceptable_precedents_present=required_precedents_present,
        unsafe_precedent_surfaced=bool(unsafe_retained),
        candidate_procedure_contract_matches=procedure_matches,
        missing_fact_contract_matches=missing_matches,
        abstention_contract_matches=abstention_matches,
        case_contract_passed=not failure_labels,
        failure_labels=tuple(failure_labels),
    )


def _metrics(outcomes: tuple[HeldoutCaseOutcome, ...]) -> HeldoutEvaluationMetrics:
    if not outcomes:
        return HeldoutEvaluationMetrics(
            scored_case_count=0,
            decision_state_accuracy=0.0,
            case_contract_pass_rate=0.0,
            acceptable_precedent_coverage=None,
            candidate_procedure_contract_accuracy=0.0,
            missing_fact_contract_accuracy=0.0,
            abstention_contract_accuracy=None,
            false_operational_match_count=0,
            unsafe_procedure_surfacing_count=0,
            unexpected_retained_precedent_count=0,
            blocked_case_ids=(),
        )

    expected_precedents = [
        precedent_id
        for outcome in outcomes
        for precedent_id in outcome.expected_acceptable_precedent_ids
    ]
    matched_precedents = [
        precedent_id
        for outcome in outcomes
        for precedent_id in outcome.expected_acceptable_precedent_ids
        if precedent_id in outcome.retained_precedent_ids
    ]
    abstention_cases = tuple(
        outcome
        for outcome in outcomes
        if outcome.expected_decision_state
        in {
            EvidenceDecisionState.INSUFFICIENT_PRECEDENT,
            EvidenceDecisionState.PROVIDER_DEGRADED,
        }
    )
    expected_procedure_sets = {
        outcome.eval_id: set(outcome.expected_candidate_procedure_ids)
        for outcome in outcomes
    }
    unsafe_procedure_count = sum(
        bool(set(outcome.candidate_procedure_ids) - expected_procedure_sets[outcome.eval_id])
        for outcome in outcomes
    )

    return HeldoutEvaluationMetrics(
        scored_case_count=len(outcomes),
        decision_state_accuracy=_ratio(
            sum(outcome.state_matches_expected for outcome in outcomes),
            len(outcomes),
        ),
        case_contract_pass_rate=_ratio(
            sum(outcome.case_contract_passed for outcome in outcomes),
            len(outcomes),
        ),
        acceptable_precedent_coverage=(
            _ratio(len(matched_precedents), len(expected_precedents))
            if expected_precedents
            else None
        ),
        candidate_procedure_contract_accuracy=_ratio(
            sum(outcome.candidate_procedure_contract_matches for outcome in outcomes),
            len(outcomes),
        ),
        missing_fact_contract_accuracy=_ratio(
            sum(outcome.missing_fact_contract_matches for outcome in outcomes),
            len(outcomes),
        ),
        abstention_contract_accuracy=(
            _ratio(
                sum(outcome.abstention_contract_matches for outcome in abstention_cases),
                len(abstention_cases),
            )
            if abstention_cases
            else None
        ),
        false_operational_match_count=sum(
            outcome.unsafe_precedent_surfaced for outcome in outcomes
        ),
        unsafe_procedure_surfacing_count=unsafe_procedure_count,
        unexpected_retained_precedent_count=sum(
            len(outcome.unexpected_retained_precedent_ids) for outcome in outcomes
        ),
        blocked_case_ids=tuple(
            outcome.eval_id for outcome in outcomes if not outcome.case_contract_passed
        ),
    )


def _promotion_gate(metrics: HeldoutEvaluationMetrics) -> HeldoutPromotionGate:
    reasons: list[str] = []
    if metrics.decision_state_accuracy < 1.0:
        reasons.append(
            "Decision-state accuracy is below the required 1.0 on the frozen tranche."
        )
    if metrics.case_contract_pass_rate < 1.0:
        reasons.append(
            "One or more held-out cases violate the full evidence/procedure contract."
        )
    if (metrics.acceptable_precedent_coverage or 0.0) < 1.0:
        reasons.append(
            "Not every required acceptable precedent was retained by the configuration."
        )
    if metrics.candidate_procedure_contract_accuracy < 1.0:
        reasons.append(
            "Candidate procedure output differs from the held-out contract."
        )
    if metrics.missing_fact_contract_accuracy < 1.0:
        reasons.append("Missing-fact output differs from the held-out contract.")
    if (metrics.abstention_contract_accuracy or 0.0) < 1.0:
        reasons.append("At least one abstention/degraded case retained evidence or procedure output.")
    if metrics.false_operational_match_count > 0:
        reasons.append("Unsafe held-out precedents were retained.")
    if metrics.unsafe_procedure_surfacing_count > 0:
        reasons.append("Unexpected candidate procedures were surfaced.")
    if metrics.unexpected_retained_precedent_count > 0:
        reasons.append("Unexpected retained precedents require trace review before promotion.")

    return HeldoutPromotionGate(
        status="passed" if not reasons else "blocked",
        blocking_reasons=tuple(reasons)
        if reasons
        else ("All strict held-out tranche gate conditions were met.",),
    )


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _resolve_git_revision(repository_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    revision = result.stdout.strip()
    return revision or None


def _render_markdown(report: HeldoutEvaluationReport) -> str:
    metrics = report.metrics
    gate = report.promotion_gate
    lines = [
        "# Held-Out Tranche 01 — Keyword + Policy Evaluation",
        "",
        "## Scope",
        "",
        "This report evaluates the frozen `heldout_tranche_01` against the recorded deterministic keyword retriever and anti-anchoring policy.",
        "The held-out cases were manifest-verified before scoring. This is a promotion gate result, not a tuning input.",
        "",
        "## Freeze verification",
        "",
        f"- Scope: `{report.freeze_verification.scope}`",
        f"- Manifest: `{report.freeze_verification.manifest_path}`",
        f"- Manifest SHA-256: `{report.freeze_verification.manifest_sha256}`",
        f"- Verified cases: `{report.freeze_verification.case_count}`",
        "",
        "## Evaluated configuration",
        "",
        f"- Retriever: `{report.configuration.retriever}`",
        f"- Policy: `{report.configuration.decision_policy}`",
        f"- Top K: `{report.configuration.top_k}`",
        f"- Corpus incident cards: `{report.configuration.corpus_incident_count}`",
        f"- Candidate procedures: `{report.configuration.procedure_count}`",
        f"- Repository revision: `{report.configuration.repository_revision or 'not available'}`",
        "",
        "## Promotion gate",
        "",
        f"**Status: {gate.status.upper()}**",
        "",
        "| Gate criterion | Observed | Required |",
        "|---|---:|---:|",
        f"| Decision-state accuracy | {metrics.decision_state_accuracy} | {gate.required_decision_state_accuracy} |",
        f"| Case-contract pass rate | {metrics.case_contract_pass_rate} | {gate.required_case_contract_pass_rate} |",
        f"| Acceptable-precedent coverage | {metrics.acceptable_precedent_coverage if metrics.acceptable_precedent_coverage is not None else 'not applicable'} | {gate.required_acceptable_precedent_coverage} |",
        f"| Procedure-contract accuracy | {metrics.candidate_procedure_contract_accuracy} | {gate.required_candidate_procedure_contract_accuracy} |",
        f"| Missing-fact contract accuracy | {metrics.missing_fact_contract_accuracy} | {gate.required_missing_fact_contract_accuracy} |",
        f"| Abstention/degraded contract accuracy | {metrics.abstention_contract_accuracy if metrics.abstention_contract_accuracy is not None else 'not applicable'} | {gate.required_abstention_contract_accuracy} |",
        f"| Unsafe precedents retained | {metrics.false_operational_match_count} | {gate.maximum_false_operational_matches} |",
        f"| Unexpected procedures surfaced | {metrics.unsafe_procedure_surfacing_count} | {gate.maximum_unsafe_procedures} |",
        f"| Unexpected retained precedents | {metrics.unexpected_retained_precedent_count} | {gate.maximum_unexpected_retained_precedents} |",
        "",
        "### Gate rationale",
        "",
    ]
    lines.extend(f"- {reason}" for reason in gate.blocking_reasons)
    lines.extend(
        [
            "",
            "## Case outcomes",
            "",
            "| Eval case | Expected state | Actual state | Ranked IDs | Retained IDs | Procedures | Contract result | Failure labels |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for outcome in report.outcomes:
        ranked = ", ".join(outcome.ranked_candidate_ids) or "none"
        retained = ", ".join(outcome.retained_precedent_ids) or "none"
        procedures = ", ".join(outcome.candidate_procedure_ids) or "none"
        labels = ", ".join(outcome.failure_labels) or "none"
        result = "pass" if outcome.case_contract_passed else "block"
        lines.append(
            f"| {outcome.eval_id} | {outcome.expected_decision_state.value} | {outcome.actual_decision_state.value} | {ranked} | {retained} | {procedures} | {result} | {labels} |"
        )
    lines.extend(["", "## Non-claims", ""])
    lines.extend(f"- {claim}" for claim in report.non_claims)
    lines.append("")
    return "\n".join(lines)
