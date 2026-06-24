"""Deterministic anti-anchoring policy for ranked historical incidents.

The policy consumes ranked candidates and structured intake facts. It does not infer
facts from model output, choose a root cause, or execute an investigation procedure.
"""

from __future__ import annotations

from collections.abc import Iterable

from incident_precedent_harness.decisions.models import (
    CandidatePolicyAssessment,
    PolicyDecisionResult,
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


class AntiAnchoringDecisionPolicy:
    """Apply compatibility, missing-fact, conflict, and procedure gates.

    This is intentionally a deterministic prototype for the current three-family
    calibration corpus. Future family support must be added with fixed cases rather
    than silently treating lexical similarity as compatibility.
    """

    def evaluate(
        self,
        *,
        intake: EvalCase,
        ranked_candidates: tuple[KeywordCandidate, ...],
        incidents: tuple[HistoricalIncidentCard, ...],
        procedures: tuple[CandidateInvestigationProcedure, ...],
    ) -> PolicyDecisionResult:
        if not intake.provider_available:
            return PolicyDecisionResult(
                decision_state=EvidenceDecisionState.PROVIDER_DEGRADED,
                assessments=(),
                safety_notes=(
                    "Required provider capability is unavailable; normal evidence presentation is blocked.",
                ),
            )

        incident_by_id = {incident.incident_id: incident for incident in incidents}
        status_by_fact = {observation.fact: observation.status for observation in intake.observed_facts}
        assessments: list[CandidatePolicyAssessment] = []
        retained_cards: list[HistoricalIncidentCard] = []

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

        if not retained_cards:
            return PolicyDecisionResult(
                decision_state=EvidenceDecisionState.INSUFFICIENT_PRECEDENT,
                assessments=tuple(assessments),
                safety_notes=(
                    "No ranked precedent satisfied the deterministic compatibility gate.",
                    "Candidate investigation procedures are blocked when precedent is insufficient.",
                ),
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
            return PolicyDecisionResult(
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

        if missing_facts:
            return PolicyDecisionResult(
                decision_state=EvidenceDecisionState.MISSING_CRITICAL_FACTS,
                retained_precedent_ids=tuple(card.incident_id for card in retained_cards),
                missing_critical_facts=missing_facts,
                assessments=tuple(assessments),
                safety_notes=(
                    "Plausible historical evidence exists, but critical verification facts are unknown.",
                    "Candidate procedures are withheld until required facts are known.",
                ),
            )

        return PolicyDecisionResult(
            decision_state=EvidenceDecisionState.EVIDENCE_FOUND,
            retained_precedent_ids=tuple(card.incident_id for card in retained_cards),
            candidate_procedure_ids=eligible_procedures,
            assessments=tuple(assessments),
            safety_notes=(
                "Historical incidents are candidate evidence, not a diagnosis or remediation instruction.",
            ),
        )

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
        relevant = (
            RequiredVerificationFact.DATABASE_CONNECTION_POOL_UTILIZATION,
            RequiredVerificationFact.DATABASE_CONNECTION_ACQUIRE_LATENCY,
            RequiredVerificationFact.ACTIVE_DATABASE_CONNECTIONS,
        )
        supported = any(status(fact) is VerificationFactStatus.CONFIRMED for fact in relevant)
        contradictions = relevant if all(
            status(fact) is VerificationFactStatus.CONTRADICTED for fact in relevant
        ) else ()
        return (
            supported and not contradictions,
            "Connection-pool compatibility checked from pool, acquisition, and active-connection facts.",
            contradictions,
        )

    return (
        False,
        "This incident family has no deterministic support policy in the current calibration prototype.",
        (),
    )


def _unique_sorted(facts: Iterable[RequiredVerificationFact]) -> tuple[RequiredVerificationFact, ...]:
    return tuple(sorted(set(facts), key=lambda fact: fact.value))
