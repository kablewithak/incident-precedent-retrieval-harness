"""Deterministic anti-anchoring policy with trace-only selection observation.

The normal policy result remains the active contract. ``evaluate_with_shadow``
retains the complete compatibility-admitted pool only for typed, trace-only
representative-selection observation. It cannot alter policy states, retained
precedent IDs, missing facts, or procedure eligibility.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from incident_precedent_harness.decisions.models import (
    CandidatePolicyAssessment,
    FamilyAdmissionSet,
    FamilyRepresentativeSelectionTrace,
    PolicyDecisionResult,
    PolicyShadowEvaluationResult,
    PolicyShadowRequest,
    ShadowSelectionState,
)
from incident_precedent_harness.decisions.strict_dominance_selection import (
    RepresentativeSelectionState,
    SelectionInputError,
    StrictDominanceRepresentativeSelector,
)
from incident_precedent_harness.domain.incident_data import (
    CandidateInvestigationProcedure,
    EvalCase,
    HistoricalIncidentCard,
)
from incident_precedent_harness.domain.incident_enums import (
    EvidenceDecisionState,
    IncidentFamily,
    RequiredVerificationFact,
    VerificationFactStatus,
)
from incident_precedent_harness.retrieval.models import KeywordCandidate


@dataclass(frozen=True, slots=True)
class _PolicyEvaluationArtifacts:
    """Private core result used to keep normal and shadow calls behaviorally aligned."""

    policy_result: PolicyDecisionResult
    family_admission_sets: tuple[FamilyAdmissionSet, ...]


class AntiAnchoringDecisionPolicy:
    """Apply compatibility, missing-fact, conflict, and procedure gates.

    This remains a deterministic prototype for the current three-family
    calibration corpus. The shadow method adds no active decision authority.
    """

    def evaluate(
        self,
        *,
        intake: EvalCase,
        ranked_candidates: tuple[KeywordCandidate, ...],
        incidents: tuple[HistoricalIncidentCard, ...],
        procedures: tuple[CandidateInvestigationProcedure, ...],
    ) -> PolicyDecisionResult:
        """Return the unchanged active policy contract."""
        return self._evaluate_core(
            intake=intake,
            ranked_candidates=ranked_candidates,
            incidents=incidents,
            procedures=procedures,
        ).policy_result

    def evaluate_with_shadow(
        self,
        *,
        intake: EvalCase,
        ranked_candidates: tuple[KeywordCandidate, ...],
        incidents: tuple[HistoricalIncidentCard, ...],
        procedures: tuple[CandidateInvestigationProcedure, ...],
        shadow_request: PolicyShadowRequest | None = None,
    ) -> PolicyShadowEvaluationResult:
        """Return the active result plus non-authoritative selection observations.

        ``shadow_request`` must supply explicit typed selection evidence. The
        method never derives selection evidence from ``EvalCase.input_summary``,
        retrieval scores, ranks, procedure metadata, or evaluation labels.
        """
        artifacts = self._evaluate_core(
            intake=intake,
            ranked_candidates=ranked_candidates,
            incidents=incidents,
            procedures=procedures,
        )
        request = shadow_request or PolicyShadowRequest()
        traces = self._build_shadow_traces(
            admission_sets=artifacts.family_admission_sets,
            incidents=incidents,
            shadow_request=request,
        )
        return PolicyShadowEvaluationResult(
            policy_result=artifacts.policy_result,
            family_admission_sets=artifacts.family_admission_sets,
            selection_traces=traces,
        )

    def _evaluate_core(
        self,
        *,
        intake: EvalCase,
        ranked_candidates: tuple[KeywordCandidate, ...],
        incidents: tuple[HistoricalIncidentCard, ...],
        procedures: tuple[CandidateInvestigationProcedure, ...],
    ) -> _PolicyEvaluationArtifacts:
        if not intake.provider_available:
            return _PolicyEvaluationArtifacts(
                policy_result=PolicyDecisionResult(
                    decision_state=EvidenceDecisionState.PROVIDER_DEGRADED,
                    assessments=(),
                    safety_notes=(
                        "Required provider capability is unavailable; normal evidence presentation is blocked.",
                    ),
                ),
                family_admission_sets=(),
            )

        incident_by_id = {incident.incident_id: incident for incident in incidents}
        status_by_fact = {
            observation.fact: observation.status
            for observation in intake.observed_facts
        }
        assessments: list[CandidatePolicyAssessment] = []
        retained_cards: list[HistoricalIncidentCard] = []
        admitted_cards_by_family: dict[IncidentFamily, list[HistoricalIncidentCard]] = defaultdict(list)

        retained_families: set[IncidentFamily] = set()
        for candidate in ranked_candidates:
            incident = incident_by_id.get(candidate.incident_id)
            if incident is None:
                continue
            assessment = self._assess_candidate(
                incident=incident,
                input_summary=intake.input_summary,
                status_by_fact=status_by_fact,
            )
            if assessment.retained:
                admitted_cards_by_family[incident.incident_family].append(incident)

            # This branch intentionally preserves the legacy public policy
            # contract. Shadow traces inspect the pre-suppression admission pool;
            # they never replace this first-compatible representative behavior.
            if assessment.retained and incident.incident_family in retained_families:
                assessment = assessment.model_copy(
                    update={
                        "retained": False,
                        "missing_facts": (),
                        "reasons": (
                            "A higher-ranked candidate already represents this compatible incident family.",
                        ),
                    }
                )
            elif assessment.retained:
                retained_families.add(incident.incident_family)
                retained_cards.append(incident)
            assessments.append(assessment)

        family_admission_sets = tuple(
            FamilyAdmissionSet(
                incident_family=incident_family,
                admitted_candidate_ids=tuple(
                    sorted(card.incident_id for card in admitted_cards)
                ),
            )
            for incident_family, admitted_cards in sorted(
                admitted_cards_by_family.items(),
                key=lambda item: item[0].value,
            )
        )

        if not retained_cards:
            return _PolicyEvaluationArtifacts(
                policy_result=PolicyDecisionResult(
                    decision_state=EvidenceDecisionState.INSUFFICIENT_PRECEDENT,
                    assessments=tuple(assessments),
                    safety_notes=(
                        "No ranked precedent satisfied the deterministic compatibility gate.",
                        "Candidate investigation procedures are blocked when precedent is insufficient.",
                    ),
                ),
                family_admission_sets=family_admission_sets,
            )

        procedure_by_id = {procedure.procedure_id: procedure for procedure in procedures}
        missing_facts = self._missing_facts_for_cards(
            retained_cards=tuple(retained_cards),
            procedure_by_id=procedure_by_id,
            status_by_fact=status_by_fact,
        )
        eligible_procedures = self._eligible_procedures(
            retained_cards=tuple(retained_cards),
            procedure_by_id=procedure_by_id,
            status_by_fact=status_by_fact,
        )
        distinct_families = {incident.incident_family for incident in retained_cards}

        if len(distinct_families) > 1:
            result = PolicyDecisionResult(
                decision_state=EvidenceDecisionState.EVIDENCE_FOUND_WITH_CONFLICT,
                retained_precedent_ids=tuple(card.incident_id for card in retained_cards),
                missing_critical_facts=missing_facts,
                conflict_summary=(
                    "Multiple operationally plausible precedent families remain; no procedure is preferred."
                ),
                assessments=tuple(assessments),
                safety_notes=(
                    "Competing evidence must be reviewed by a human responder.",
                    "Candidate procedures are withheld while plausible paths diverge.",
                ),
            )
        elif missing_facts:
            result = PolicyDecisionResult(
                decision_state=EvidenceDecisionState.MISSING_CRITICAL_FACTS,
                retained_precedent_ids=tuple(card.incident_id for card in retained_cards),
                missing_critical_facts=missing_facts,
                assessments=tuple(assessments),
                safety_notes=(
                    "Plausible historical evidence exists, but critical verification facts are unknown.",
                    "Candidate procedures are withheld until required facts are known.",
                ),
            )
        else:
            result = PolicyDecisionResult(
                decision_state=EvidenceDecisionState.EVIDENCE_FOUND,
                retained_precedent_ids=tuple(card.incident_id for card in retained_cards),
                candidate_procedure_ids=eligible_procedures,
                assessments=tuple(assessments),
                safety_notes=(
                    "Historical incidents are candidate evidence, not a diagnosis or remediation instruction.",
                ),
            )

        return _PolicyEvaluationArtifacts(
            policy_result=result,
            family_admission_sets=family_admission_sets,
        )

    def _build_shadow_traces(
        self,
        *,
        admission_sets: tuple[FamilyAdmissionSet, ...],
        incidents: tuple[HistoricalIncidentCard, ...],
        shadow_request: PolicyShadowRequest,
    ) -> tuple[FamilyRepresentativeSelectionTrace, ...]:
        selector = StrictDominanceRepresentativeSelector()
        traces: list[FamilyRepresentativeSelectionTrace] = []
        for admission_set in admission_sets:
            selection_intake = shadow_request.selection_intake_for(
                admission_set.incident_family
            )
            candidate_ids = admission_set.admitted_candidate_ids
            if len(candidate_ids) == 1:
                traces.append(
                    FamilyRepresentativeSelectionTrace(
                        incident_family=admission_set.incident_family,
                        admitted_candidate_ids=candidate_ids,
                        selection_intake_present=selection_intake is not None,
                        selector_invoked=False,
                        selection_state=ShadowSelectionState.NOT_APPLICABLE_SINGLE_CANDIDATE,
                        unavailable_reason=(
                            "Strict-dominance selection is not applicable because this family has one policy-admitted candidate."
                        ),
                    )
                )
                continue

            if selection_intake is None:
                traces.append(
                    FamilyRepresentativeSelectionTrace(
                        incident_family=admission_set.incident_family,
                        admitted_candidate_ids=candidate_ids,
                        selection_intake_present=False,
                        selector_invoked=False,
                        selection_state=ShadowSelectionState.UNAVAILABLE,
                        unavailable_reason=(
                            "Typed representative-selection intake was not supplied for this policy-admitted family."
                        ),
                    )
                )
                continue

            if admission_set.incident_family is not IncidentFamily.CONNECTION_POOL_EXHAUSTION:
                traces.append(
                    FamilyRepresentativeSelectionTrace(
                        incident_family=admission_set.incident_family,
                        admitted_candidate_ids=candidate_ids,
                        selection_intake_present=True,
                        selector_invoked=False,
                        selection_state=ShadowSelectionState.UNAVAILABLE,
                        unavailable_reason=(
                            "Strict-dominance selection is not supported for this policy-admitted incident family."
                        ),
                    )
                )
                continue

            try:
                selection_result = selector.select(
                    intake=selection_intake,
                    candidate_incident_ids=candidate_ids,
                    incidents=incidents,
                )
            except SelectionInputError:
                traces.append(
                    FamilyRepresentativeSelectionTrace(
                        incident_family=admission_set.incident_family,
                        admitted_candidate_ids=candidate_ids,
                        selection_intake_present=True,
                        selector_invoked=False,
                        selection_state=ShadowSelectionState.UNAVAILABLE,
                        unavailable_reason=(
                            "Schema-derived representative selection was unavailable for one or more policy-admitted cards."
                        ),
                    )
                )
                continue

            traces.append(
                FamilyRepresentativeSelectionTrace(
                    incident_family=admission_set.incident_family,
                    admitted_candidate_ids=candidate_ids,
                    selection_intake_present=True,
                    selector_invoked=True,
                    selection_state=_shadow_state_from_selection_result(
                        selection_result.selection_state
                    ),
                    representative_incident_ids=selection_result.representative_incident_ids,
                    candidate_evidence=selection_result.candidate_evidence,
                )
            )
        return tuple(traces)

    def _assess_candidate(
        self,
        *,
        incident: HistoricalIncidentCard,
        input_summary: str,
        status_by_fact: dict[RequiredVerificationFact, VerificationFactStatus],
    ) -> CandidatePolicyAssessment:
        family_support, family_reason, contradicted = _family_compatibility(
            incident_family=incident.incident_family,
            input_summary=input_summary,
            status_by_fact=status_by_fact,
        )
        missing = tuple(
            fact
            for fact in incident.required_verification_facts
            if status_by_fact.get(fact, VerificationFactStatus.UNKNOWN)
            is VerificationFactStatus.UNKNOWN
        )
        retained = family_support and not contradicted
        reasons = [family_reason]
        if contradicted:
            reasons.append("A family-defining observation contradicts this precedent.")
        elif missing:
            reasons.append("The precedent remains plausible but requires verification facts.")
        else:
            reasons.append("Required facts are known and do not contradict this precedent.")
        return CandidatePolicyAssessment(
            incident_id=incident.incident_id,
            incident_family=incident.incident_family,
            retained=retained,
            missing_facts=missing if retained else (),
            contradicted_facts=contradicted,
            reasons=tuple(reasons),
        )

    def _missing_facts_for_cards(
        self,
        *,
        retained_cards: tuple[HistoricalIncidentCard, ...],
        procedure_by_id: dict[str, CandidateInvestigationProcedure],
        status_by_fact: dict[RequiredVerificationFact, VerificationFactStatus],
    ) -> tuple[RequiredVerificationFact, ...]:
        required_facts: set[RequiredVerificationFact] = set()
        for card in retained_cards:
            required_facts.update(card.required_verification_facts)
            for procedure_id in card.safe_procedure_ids:
                procedure = procedure_by_id.get(procedure_id)
                if procedure is not None:
                    required_facts.update(procedure.verification_prerequisites)
        return _unique_sorted(
            fact
            for fact in required_facts
            if status_by_fact.get(fact, VerificationFactStatus.UNKNOWN)
            is VerificationFactStatus.UNKNOWN
        )

    def _eligible_procedures(
        self,
        *,
        retained_cards: tuple[HistoricalIncidentCard, ...],
        procedure_by_id: dict[str, CandidateInvestigationProcedure],
        status_by_fact: dict[RequiredVerificationFact, VerificationFactStatus],
    ) -> tuple[str, ...]:
        eligible: list[str] = []
        for card in retained_cards:
            for procedure_id in card.safe_procedure_ids:
                procedure = procedure_by_id.get(procedure_id)
                if procedure is None or procedure.status.value != "current":
                    continue
                if card.incident_family not in procedure.applicable_incident_families:
                    continue
                if card.incident_family in procedure.not_applicable_when:
                    continue
                if any(
                    status_by_fact.get(fact, VerificationFactStatus.UNKNOWN)
                    is VerificationFactStatus.UNKNOWN
                    for fact in procedure.verification_prerequisites
                ):
                    continue
                if procedure_id not in eligible:
                    eligible.append(procedure_id)
        return tuple(eligible)


def _shadow_state_from_selection_result(
    selection_state: RepresentativeSelectionState,
) -> ShadowSelectionState:
    return {
        RepresentativeSelectionState.SINGLE_REPRESENTATIVE: ShadowSelectionState.SINGLE_REPRESENTATIVE,
        RepresentativeSelectionState.EXPLICIT_TIE: ShadowSelectionState.EXPLICIT_TIE,
    }[selection_state]


def _family_compatibility(
    *,
    incident_family: IncidentFamily,
    input_summary: str,
    status_by_fact: dict[RequiredVerificationFact, VerificationFactStatus],
) -> tuple[bool, str, tuple[RequiredVerificationFact, ...]]:
    summary = input_summary.lower()
    status = lambda fact: status_by_fact.get(fact, VerificationFactStatus.UNKNOWN)

    if incident_family is IncidentFamily.QUEUE_BACKLOG_CONSUMER_FAILURE:
        contradictions = tuple(
            fact
            for fact in (
                RequiredVerificationFact.QUEUE_DEPTH,
                RequiredVerificationFact.CONSUMER_ERROR_RATE,
            )
            if status(fact) is VerificationFactStatus.CONTRADICTED
        )
        supported = any(
            status(fact) is VerificationFactStatus.CONFIRMED
            for fact in (
                RequiredVerificationFact.QUEUE_DEPTH,
                RequiredVerificationFact.CONSUMER_ERROR_RATE,
                RequiredVerificationFact.WORKER_DEPLOYMENT_VERSION,
            )
        )
        return (
            supported and not contradictions,
            "Queue-consumer compatibility checked from structured queue and consumer facts.",
            contradictions,
        )

    if incident_family is IncidentFamily.DATABASE_MIGRATION_LOCK_CONTENTION:
        migration_phrase = any(
            phrase in summary
            for phrase in (
                "migration began",
                "migration started",
                "schema migration",
                "migration window began",
            )
        )
        contradictions = (
            (RequiredVerificationFact.MIGRATION_LOCK_WAITS,)
            if status(RequiredVerificationFact.MIGRATION_LOCK_WAITS)
            is VerificationFactStatus.CONTRADICTED
            else ()
        )
        supported = (
            migration_phrase
            or status(RequiredVerificationFact.MIGRATION_LOCK_WAITS)
            is VerificationFactStatus.CONFIRMED
        )
        return (
            supported and not contradictions,
            "Migration-lock compatibility checked from declared migration context and lock-wait facts.",
            contradictions,
        )

    if incident_family is IncidentFamily.CONNECTION_POOL_EXHAUSTION:
        direct_pool_signals = (
            RequiredVerificationFact.DATABASE_CONNECTION_POOL_UTILIZATION,
            RequiredVerificationFact.DATABASE_CONNECTION_ACQUIRE_LATENCY,
        )
        active_connections = RequiredVerificationFact.ACTIVE_DATABASE_CONNECTIONS
        confirmed_direct_signal = any(
            status(fact) is VerificationFactStatus.CONFIRMED for fact in direct_pool_signals
        )
        direct_signals_unknown = all(
            status(fact) is VerificationFactStatus.UNKNOWN for fact in direct_pool_signals
        )
        direct_signals_contradicted = all(
            status(fact) is VerificationFactStatus.CONTRADICTED for fact in direct_pool_signals
        )

        supported = confirmed_direct_signal or (
            direct_signals_unknown
            and status(active_connections) is VerificationFactStatus.CONFIRMED
        )
        contradictions = direct_pool_signals if direct_signals_contradicted else ()
        return (
            supported and not contradictions,
            "Connection-pool compatibility requires a confirmed direct pool signal, "
            "or explicitly unknown direct signals plus confirmed active-connection context; "
            "active connections alone cannot override contradicted pool signals.",
            contradictions,
        )

    return (
        False,
        "This incident family has no deterministic support policy in the current calibration prototype.",
        (),
    )


def _unique_sorted(facts: Iterable[RequiredVerificationFact]) -> tuple[RequiredVerificationFact, ...]:
    return tuple(sorted(set(facts), key=lambda fact: fact.value))
