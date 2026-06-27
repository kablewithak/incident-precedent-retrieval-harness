"""Write-once, no-mutation autopsy for the frozen EVAL-110 selection divergence.

This module reads already-recorded held-out and typed-triage evidence after verifying
HELDOUT_FREEZE_MANIFEST.json. It does not rerun retrieval, invoke SIE, alter policy,
or modify a frozen fixture. The output is a diagnostic verdict, not a remediation.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from incident_precedent_harness.domain.incident_data import EvalCase, HistoricalIncidentCard
from incident_precedent_harness.domain.incident_enums import (
    EvidenceDecisionState,
    IncidentFamily,
    OperationalSignalFamily,
    RequiredVerificationFact,
    VerificationFactStatus,
)
from incident_precedent_harness.evaluation.heldout import (
    HeldoutEvaluationReport,
    HeldoutFreezeVerification,
    verify_heldout_freeze,
)
from incident_precedent_harness.evaluation.typed_triage_promotion import (
    FrozenTypedTriagePromotionReport,
)

TARGET_EVAL_ID = "EVAL-110"
BASELINE_JSON_RELATIVE_PATH = (
    Path("evidence_vault") / "reports" / "heldout-tranche-01-keyword-policy.json"
)
PROMOTION_JSON_RELATIVE_PATH = (
    Path("evidence_vault") / "reports" / "frozen-typed-triage-promotion-gate.json"
)
AUTOPSY_JSON_RELATIVE_PATH = (
    Path("evidence_vault") / "reports" / "eval-110-representative-selection-autopsy.json"
)
AUTOPSY_MARKDOWN_RELATIVE_PATH = (
    Path("docs") / "reports" / "eval-110-representative-selection-autopsy.md"
)


class Eval110AutopsyVerdict(str, Enum):
    """Diagnostic verdicts only; none authorizes a policy or fixture change."""

    POLICY_SELECTION_DEFECT = "policy_selection_defect"
    EXPECTED_CONTRACT_DEFECT = "expected_contract_defect"
    UNDOCUMENTED_CONFLICT_RULE = "undocumented_conflict_rule"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class Eval110RepresentativeSelectionAutopsyError(RuntimeError):
    """Raised when the evidence chain is incomplete, inconsistent, or mutable."""


class RequiredFactTrace(BaseModel):
    """Recorded observed status for a candidate card's required verification fact."""

    model_config = ConfigDict(extra="forbid")

    fact: RequiredVerificationFact
    status: VerificationFactStatus


class CandidateSelectionTrace(BaseModel):
    """Trace-safe typed facts for a ranked, retained, or expected candidate card."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(pattern=r"^INC-[0-9]{3}$")
    incident_family: IncidentFamily
    ranked_position: int | None = Field(default=None, ge=1)
    retained_by_policy: bool
    expected_acceptable: bool
    required_fact_trace: tuple[RequiredFactTrace, ...]
    confirmed_required_fact_count: int = Field(ge=0)
    contradicted_required_fact_count: int = Field(ge=0)
    unknown_required_fact_count: int = Field(ge=0)
    selection_signature_present: bool
    signature_service: str | None = None
    signature_component: str | None = None
    signature_change_context: str | None = None
    signature_signal_families: tuple[OperationalSignalFamily, ...] = ()


class Eval110PromotionParityEvidence(BaseModel):
    """Cross-artifact proof that typed triage did not alter policy authority."""

    model_config = ConfigDict(extra="forbid")

    policy_matches_baseline: bool
    typed_triage_matches_expected_state: bool
    typed_triage_decision_state: EvidenceDecisionState
    procedure_execution_authorized: bool
    semantic_advisory_available: bool


class Eval110RepresentativeSelectionAutopsyReport(BaseModel):
    """Immutable diagnostic evidence for EVAL-110 only."""

    model_config = ConfigDict(extra="forbid")

    report_kind: str = "eval_110_representative_selection_autopsy"
    generated_at: datetime
    target_eval_id: str = TARGET_EVAL_ID
    freeze_verification: HeldoutFreezeVerification
    baseline_report_path: str
    baseline_report_sha256: str
    promotion_report_path: str
    promotion_report_sha256: str
    expected_decision_state: EvidenceDecisionState
    baseline_decision_state: EvidenceDecisionState
    ranked_candidate_ids: tuple[str, ...]
    retained_precedent_ids: tuple[str, ...]
    expected_acceptable_precedent_ids: tuple[str, ...]
    omitted_required_precedent_ids: tuple[str, ...]
    unexpected_retained_precedent_ids: tuple[str, ...]
    failure_labels: tuple[str, ...]
    promotion_parity: Eval110PromotionParityEvidence
    candidate_traces: tuple[CandidateSelectionTrace, ...] = Field(min_length=1)
    verdict: Eval110AutopsyVerdict
    verdict_reasons: tuple[str, ...] = Field(min_length=1)
    remediation_boundary: str = Field(min_length=1)
    non_claims: tuple[str, ...] = Field(min_length=1)


def build_eval_110_representative_selection_autopsy(
    *,
    repository_root: Path,
    incidents: tuple[HistoricalIncidentCard, ...],
    cases: tuple[EvalCase, ...],
    baseline_relative_path: Path = BASELINE_JSON_RELATIVE_PATH,
    promotion_relative_path: Path = PROMOTION_JSON_RELATIVE_PATH,
) -> Eval110RepresentativeSelectionAutopsyReport:
    """Read frozen evidence and issue a no-mutation verdict for EVAL-110.

    The baseline provides ranked and retained policy evidence. The promotion report
    proves that the typed packet preserved those policy outputs. Neither report is
    recomputed here: the autopsy remains independent of retrieval and provider state.
    """

    root = repository_root.resolve()
    freeze = verify_heldout_freeze(root)
    case = _load_target_case(cases=cases, verification=freeze)
    baseline_path = _resolve_report_path(root, baseline_relative_path)
    promotion_path = _resolve_report_path(root, promotion_relative_path)
    baseline = _load_baseline(baseline_path)
    promotion = _load_promotion(promotion_path)
    baseline_outcome = _find_baseline_outcome(baseline)
    promotion_outcome = _find_promotion_outcome(promotion)

    _verify_evidence_chain(
        freeze=freeze,
        case=case,
        baseline=baseline,
        baseline_outcome=baseline_outcome,
        promotion=promotion,
        promotion_outcome=promotion_outcome,
    )

    incident_by_id = {incident.incident_id: incident for incident in incidents}
    candidate_ids = _unique_in_order(
        (
            *baseline_outcome.ranked_candidate_ids,
            *baseline_outcome.retained_precedent_ids,
            *baseline_outcome.expected_acceptable_precedent_ids,
        )
    )
    missing_cards = [incident_id for incident_id in candidate_ids if incident_id not in incident_by_id]
    if missing_cards:
        raise Eval110RepresentativeSelectionAutopsyError(
            "EVAL-110 evidence references unknown incident cards: "
            + ", ".join(sorted(missing_cards))
        )

    traces = tuple(
        _build_candidate_trace(
            incident=incident_by_id[incident_id],
            case=case,
            ranked_candidate_ids=baseline_outcome.ranked_candidate_ids,
            retained_ids=baseline_outcome.retained_precedent_ids,
            expected_ids=baseline_outcome.expected_acceptable_precedent_ids,
        )
        for incident_id in candidate_ids
    )
    omitted = tuple(
        incident_id
        for incident_id in baseline_outcome.expected_acceptable_precedent_ids
        if incident_id not in baseline_outcome.retained_precedent_ids
    )
    unexpected = tuple(
        incident_id
        for incident_id in baseline_outcome.retained_precedent_ids
        if incident_id not in baseline_outcome.expected_acceptable_precedent_ids
    )
    verdict, reasons, boundary = _determine_verdict(
        baseline_outcome=baseline_outcome,
        incident_by_id=incident_by_id,
        omitted_required_ids=omitted,
        unexpected_retained_ids=unexpected,
    )

    return Eval110RepresentativeSelectionAutopsyReport(
        generated_at=datetime.now(UTC),
        freeze_verification=freeze,
        baseline_report_path=_display_path(root, baseline_path),
        baseline_report_sha256=_sha256(baseline_path),
        promotion_report_path=_display_path(root, promotion_path),
        promotion_report_sha256=_sha256(promotion_path),
        expected_decision_state=case.expected_decision_state,
        baseline_decision_state=baseline_outcome.actual_decision_state,
        ranked_candidate_ids=baseline_outcome.ranked_candidate_ids,
        retained_precedent_ids=baseline_outcome.retained_precedent_ids,
        expected_acceptable_precedent_ids=baseline_outcome.expected_acceptable_precedent_ids,
        omitted_required_precedent_ids=omitted,
        unexpected_retained_precedent_ids=unexpected,
        failure_labels=baseline_outcome.failure_labels,
        promotion_parity=Eval110PromotionParityEvidence(
            policy_matches_baseline=promotion_outcome.policy_matches_baseline,
            typed_triage_matches_expected_state=promotion_outcome.typed_triage_matches_expected_state,
            typed_triage_decision_state=promotion_outcome.typed_triage_decision_state,
            procedure_execution_authorized=promotion_outcome.procedure_execution_authorized,
            semantic_advisory_available=promotion_outcome.semantic_advisory_status.value == "available",
        ),
        candidate_traces=traces,
        verdict=verdict,
        verdict_reasons=reasons,
        remediation_boundary=boundary,
        non_claims=(
            "This autopsy reads recorded frozen evidence; it does not rerun retrieval, policy, or semantic inference.",
            "The held-out fixture, labels, hashes, candidate ordering, policy rules, procedure eligibility, and semantic-advisory authority are unchanged.",
            "The verdict is a diagnostic classification, not proof that any remediation will pass the frozen tranche.",
            "No procedure is authorized, and no production, customer-data, or incident-response safety claim follows from this report.",
        ),
    )


def write_eval_110_representative_selection_autopsy(
    report: Eval110RepresentativeSelectionAutopsyReport,
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write the evidence pair once; preserve the first diagnostic record."""

    existing = tuple(path for path in (json_path, markdown_path) if path.exists())
    if existing:
        rendered = ", ".join(str(path) for path in existing)
        raise FileExistsError(
            "EVAL-110 representative-selection autopsy already exists and will not be "
            f"overwritten: {rendered}. Preserve the diagnostic record; create a separately "
            "versioned follow-up only after a documented change."
        )

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _load_target_case(
    *,
    cases: tuple[EvalCase, ...],
    verification: HeldoutFreezeVerification,
) -> EvalCase:
    case_by_id = {case.eval_id: case for case in cases}
    if set(case_by_id) != set(verification.verified_case_ids):
        raise Eval110RepresentativeSelectionAutopsyError(
            "loaded held-out cases differ from the manifest-verified case IDs"
        )
    case = case_by_id.get(TARGET_EVAL_ID)
    if case is None:
        raise Eval110RepresentativeSelectionAutopsyError("EVAL-110 is absent from held-out cases")
    if case.split != "heldout":
        raise Eval110RepresentativeSelectionAutopsyError("EVAL-110 is not a held-out case")
    if case.expected_decision_state is not EvidenceDecisionState.EVIDENCE_FOUND_WITH_CONFLICT:
        raise Eval110RepresentativeSelectionAutopsyError(
            "EVAL-110 expected decision state is not evidence_found_with_conflict"
        )
    return case


def _load_baseline(path: Path) -> HeldoutEvaluationReport:
    if not path.is_file():
        raise Eval110RepresentativeSelectionAutopsyError(
            f"required held-out baseline report is missing: {path}"
        )
    try:
        report = HeldoutEvaluationReport.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Eval110RepresentativeSelectionAutopsyError(
            "required held-out baseline report cannot be parsed"
        ) from error
    if report.promotion_gate.status != "blocked":
        raise Eval110RepresentativeSelectionAutopsyError(
            "EVAL-110 autopsy requires a blocked held-out baseline report"
        )
    return report


def _load_promotion(path: Path) -> FrozenTypedTriagePromotionReport:
    if not path.is_file():
        raise Eval110RepresentativeSelectionAutopsyError(
            f"required frozen typed-triage promotion report is missing: {path}"
        )
    try:
        return FrozenTypedTriagePromotionReport.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Eval110RepresentativeSelectionAutopsyError(
            "required frozen typed-triage promotion report cannot be parsed"
        ) from error


def _find_baseline_outcome(report: HeldoutEvaluationReport):
    matches = tuple(outcome for outcome in report.outcomes if outcome.eval_id == TARGET_EVAL_ID)
    if len(matches) != 1:
        raise Eval110RepresentativeSelectionAutopsyError(
            "held-out baseline must contain exactly one EVAL-110 outcome"
        )
    return matches[0]


def _find_promotion_outcome(report: FrozenTypedTriagePromotionReport):
    matches = tuple(outcome for outcome in report.outcomes if outcome.eval_id == TARGET_EVAL_ID)
    if len(matches) != 1:
        raise Eval110RepresentativeSelectionAutopsyError(
            "typed-triage promotion report must contain exactly one EVAL-110 outcome"
        )
    return matches[0]


def _verify_evidence_chain(
    *,
    freeze: HeldoutFreezeVerification,
    case: EvalCase,
    baseline: HeldoutEvaluationReport,
    baseline_outcome,
    promotion: FrozenTypedTriagePromotionReport,
    promotion_outcome,
) -> None:
    if not baseline.freeze_verification.verified:
        raise Eval110RepresentativeSelectionAutopsyError(
            "held-out baseline was not manifest-verified"
        )
    if baseline.freeze_verification.manifest_sha256 != freeze.manifest_sha256:
        raise Eval110RepresentativeSelectionAutopsyError(
            "held-out baseline manifest hash does not match current verified freeze"
        )
    if promotion.freeze_verification.manifest_sha256 != freeze.manifest_sha256:
        raise Eval110RepresentativeSelectionAutopsyError(
            "typed-triage promotion manifest hash does not match current verified freeze"
        )
    if baseline_outcome.expected_decision_state is not case.expected_decision_state:
        raise Eval110RepresentativeSelectionAutopsyError(
            "baseline expected decision state does not match EVAL-110 fixture"
        )
    if baseline_outcome.actual_decision_state is not case.expected_decision_state:
        raise Eval110RepresentativeSelectionAutopsyError(
            "baseline EVAL-110 decision state diverges from the frozen expectation"
        )
    required_labels = {
        "required_acceptable_precedent_missing",
        "unexpected_retained_precedent",
    }
    if baseline_outcome.case_contract_passed or not required_labels.issubset(
        set(baseline_outcome.failure_labels)
    ):
        raise Eval110RepresentativeSelectionAutopsyError(
            "baseline EVAL-110 is not the expected representative-selection contract failure"
        )
    if not promotion_outcome.policy_matches_baseline:
        raise Eval110RepresentativeSelectionAutopsyError(
            "typed-triage policy output does not match the held-out baseline"
        )
    if not promotion_outcome.typed_triage_matches_expected_state:
        raise Eval110RepresentativeSelectionAutopsyError(
            "typed-triage EVAL-110 state does not match the frozen expectation"
        )
    if promotion_outcome.procedure_execution_authorized:
        raise Eval110RepresentativeSelectionAutopsyError(
            "typed-triage report records forbidden procedure execution authorization"
        )
    if promotion_outcome.baseline_decision_state is not baseline_outcome.actual_decision_state:
        raise Eval110RepresentativeSelectionAutopsyError(
            "typed-triage baseline state does not match held-out baseline evidence"
        )
    if tuple(promotion_outcome.policy_retained_precedent_ids) != tuple(
        baseline_outcome.retained_precedent_ids
    ):
        raise Eval110RepresentativeSelectionAutopsyError(
            "typed-triage retained precedents do not match held-out baseline evidence"
        )
    if tuple(promotion_outcome.policy_candidate_procedure_ids) != tuple(
        baseline_outcome.candidate_procedure_ids
    ):
        raise Eval110RepresentativeSelectionAutopsyError(
            "typed-triage candidate procedures do not match held-out baseline evidence"
        )


def _build_candidate_trace(
    *,
    incident: HistoricalIncidentCard,
    case: EvalCase,
    ranked_candidate_ids: tuple[str, ...],
    retained_ids: tuple[str, ...],
    expected_ids: tuple[str, ...],
) -> CandidateSelectionTrace:
    status_by_fact = {observation.fact: observation.status for observation in case.observed_facts}
    required_fact_trace = tuple(
        RequiredFactTrace(
            fact=fact,
            status=status_by_fact.get(fact, VerificationFactStatus.UNKNOWN),
        )
        for fact in incident.required_verification_facts
    )
    signature = incident.selection_signature
    return CandidateSelectionTrace(
        incident_id=incident.incident_id,
        incident_family=incident.incident_family,
        ranked_position=_ranking_position(incident.incident_id, ranked_candidate_ids),
        retained_by_policy=incident.incident_id in retained_ids,
        expected_acceptable=incident.incident_id in expected_ids,
        required_fact_trace=required_fact_trace,
        confirmed_required_fact_count=sum(
            trace.status is VerificationFactStatus.CONFIRMED for trace in required_fact_trace
        ),
        contradicted_required_fact_count=sum(
            trace.status is VerificationFactStatus.CONTRADICTED for trace in required_fact_trace
        ),
        unknown_required_fact_count=sum(
            trace.status is VerificationFactStatus.UNKNOWN for trace in required_fact_trace
        ),
        selection_signature_present=signature is not None,
        signature_service=signature.service.value if signature is not None else None,
        signature_component=signature.component.value if signature is not None else None,
        signature_change_context=signature.change_context.value if signature is not None else None,
        signature_signal_families=(
            tuple(signal.signal_family for signal in signature.operational_signals)
            if signature is not None
            else ()
        ),
    )


def _determine_verdict(
    *,
    baseline_outcome,
    incident_by_id: dict[str, HistoricalIncidentCard],
    omitted_required_ids: tuple[str, ...],
    unexpected_retained_ids: tuple[str, ...],
) -> tuple[Eval110AutopsyVerdict, tuple[str, ...], str]:
    if not omitted_required_ids or not unexpected_retained_ids:
        return (
            Eval110AutopsyVerdict.INSUFFICIENT_EVIDENCE,
            (
                "The expected missing-versus-unexpected representative divergence was not present in recorded EVAL-110 evidence.",
            ),
            "Preserve the report and perform a design review before proposing any policy or contract change.",
        )

    ranked_positions = {
        incident_id: position
        for position, incident_id in enumerate(baseline_outcome.ranked_candidate_ids, start=1)
    }
    same_family_replacements: list[tuple[HistoricalIncidentCard, HistoricalIncidentCard]] = []
    for unexpected_id in unexpected_retained_ids:
        for omitted_id in omitted_required_ids:
            unexpected = incident_by_id[unexpected_id]
            omitted = incident_by_id[omitted_id]
            if unexpected.incident_family is omitted.incident_family:
                same_family_replacements.append((unexpected, omitted))

    if same_family_replacements:
        unexpected, omitted = same_family_replacements[0]
        unexpected_rank = ranked_positions.get(unexpected.incident_id)
        omitted_rank = ranked_positions.get(omitted.incident_id)
        if (
            unexpected_rank is not None
            and omitted_rank is not None
            and unexpected_rank < omitted_rank
        ):
            return (
                Eval110AutopsyVerdict.UNDOCUMENTED_CONFLICT_RULE,
                (
                    f"The active policy retained higher-ranked {unexpected.incident_id} while the frozen contract required {omitted.incident_id}; both are {unexpected.incident_family.value} cards.",
                    "The recorded decision state remains correct, so the divergence is within-family representative selection rather than conflict-state detection.",
                    "The current active path suppresses later compatible candidates in the same family, making the retained representative depend on fixed retrieval order without an active reviewed selection rule.",
                ),
                "Do not patch ranks, incident IDs, retrieval order, held-out labels, or active policy on this branch. "
                "A separate calibration-only design slice must define and evaluate a typed within-family representative-selection contract before any activation proposal.",
            )

    return (
        Eval110AutopsyVerdict.INSUFFICIENT_EVIDENCE,
        (
            "Recorded EVAL-110 evidence proves a representative-selection contract divergence, but it does not meet the narrow same-family higher-rank diagnosis pattern.",
        ),
        "Preserve the report and add a calibration-only diagnostic case before proposing any policy or expected-contract change.",
    )


def _resolve_report_path(root: Path, value: Path) -> Path:
    return value if value.is_absolute() else root / value


def _display_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


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


def _render_markdown(report: Eval110RepresentativeSelectionAutopsyReport) -> str:
    lines = [
        "# EVAL-110 — Representative-Selection Autopsy",
        "",
        "## Scope",
        "",
        "This report reads recorded frozen baseline and typed-triage promotion evidence. It does not rerun retrieval, policy, or semantic inference and does not modify held-out inputs or active policy behavior.",
        "",
        "## Evidence chain",
        "",
        f"- Held-out manifest: `{report.freeze_verification.manifest_path}`",
        f"- Held-out manifest SHA-256: `{report.freeze_verification.manifest_sha256}`",
        f"- Verified frozen cases: `{report.freeze_verification.case_count}`",
        f"- Baseline report: `{report.baseline_report_path}`",
        f"- Baseline SHA-256: `{report.baseline_report_sha256}`",
        f"- Typed-triage promotion report: `{report.promotion_report_path}`",
        f"- Typed-triage promotion SHA-256: `{report.promotion_report_sha256}`",
        "",
        "## Recorded divergence",
        "",
        f"- Expected state: `{report.expected_decision_state.value}`",
        f"- Baseline state: `{report.baseline_decision_state.value}`",
        f"- Ranked candidate IDs: `{', '.join(report.ranked_candidate_ids)}`",
        f"- Retained precedent IDs: `{', '.join(report.retained_precedent_ids)}`",
        f"- Expected acceptable IDs: `{', '.join(report.expected_acceptable_precedent_ids)}`",
        f"- Omitted required IDs: `{', '.join(report.omitted_required_precedent_ids) or 'none'}`",
        f"- Unexpected retained IDs: `{', '.join(report.unexpected_retained_precedent_ids) or 'none'}`",
        f"- Failure labels: `{', '.join(report.failure_labels) or 'none'}`",
        "",
        "## Typed-triage authority parity",
        "",
        f"- Policy matches baseline: `{str(report.promotion_parity.policy_matches_baseline).lower()}`",
        f"- Typed state matches frozen expectation: `{str(report.promotion_parity.typed_triage_matches_expected_state).lower()}`",
        f"- Typed decision state: `{report.promotion_parity.typed_triage_decision_state.value}`",
        f"- Semantic advisory available: `{str(report.promotion_parity.semantic_advisory_available).lower()}`",
        f"- Procedure execution authorized: `{str(report.promotion_parity.procedure_execution_authorized).lower()}`",
        "",
        "## Candidate trace",
        "",
        "| Incident | Family | Rank | Retained | Expected acceptable | Confirmed facts | Contradicted facts | Unknown facts | Signature signals |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for trace in report.candidate_traces:
        signal_families = ", ".join(signal.value for signal in trace.signature_signal_families) or "none"
        lines.append(
            f"| {trace.incident_id} | {trace.incident_family.value} | "
            f"{trace.ranked_position if trace.ranked_position is not None else '—'} | "
            f"{str(trace.retained_by_policy).lower()} | "
            f"{str(trace.expected_acceptable).lower()} | "
            f"{trace.confirmed_required_fact_count} | {trace.contradicted_required_fact_count} | "
            f"{trace.unknown_required_fact_count} | {signal_families} |"
        )
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"**{report.verdict.value.upper()}**",
            "",
            "### Reasons",
            "",
        ]
    )
    lines.extend(f"- {reason}" for reason in report.verdict_reasons)
    lines.extend(
        [
            "",
            "### Remediation boundary",
            "",
            report.remediation_boundary,
            "",
            "## Non-claims",
            "",
        ]
    )
    lines.extend(f"- {claim}" for claim in report.non_claims)
    lines.append("")
    return "\n".join(lines)
