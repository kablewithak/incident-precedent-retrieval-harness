"""Calibration-only strict-dominance representative selector.

This module consumes only typed representative-selection intake and
schema-derived candidate signatures. It does not import retrieval, policy,
procedure, evaluation-label, or held-out modules.

The selector is intentionally disconnected from ``AntiAnchoringDecisionPolicy``.
A future activation slice may call it only after the existing policy has already
admitted candidate cards within one incident family.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from incident_precedent_harness.domain.incident_data import (
    HistoricalIncidentCard,
    RecordIdentifier,
    RepresentativeSelectionIntake,
)
from incident_precedent_harness.domain.incident_enums import (
    ChangeContext,
    IncidentFamily,
    OperationalSignalFamily,
    RelayComponent,
    RelayService,
)


class SelectionInputError(ValueError):
    """Raised when a caller violates the selector's typed input boundary."""


class SelectionAlignment(str, Enum):
    """Observed alignment for one independently compared selection dimension."""

    MATCH = "match"
    UNKNOWN = "unknown"
    MISMATCH = "mismatch"


class RepresentativeSelectionState(str, Enum):
    """Safe outcomes for one already-admitted same-family candidate pool."""

    SINGLE_REPRESENTATIVE = "single_representative"
    EXPLICIT_TIE = "explicit_tie"


class CandidateSelectionEvidence(BaseModel):
    """Trace-safe structured evidence for one candidate card.

    The model deliberately exposes comparisons rather than an aggregate score.
    The selector never sums dimensions or applies weights.
    """

    model_config = ConfigDict(extra="forbid")

    incident_id: RecordIdentifier
    service_alignment: SelectionAlignment
    component_alignment: SelectionAlignment
    change_context_alignment: SelectionAlignment
    matching_signal_families: tuple[OperationalSignalFamily, ...] = ()
    contradicted_signal_families: tuple[OperationalSignalFamily, ...] = ()
    strict_dominates_incident_ids: tuple[RecordIdentifier, ...] = ()
    dominated_by_incident_ids: tuple[RecordIdentifier, ...] = ()
    selection_state: RepresentativeSelectionState | None = None
    reasons: tuple[str, ...] = Field(min_length=1, max_length=8)


class RepresentativeSelectionResult(BaseModel):
    """One calibration-only selection result for same-family candidate cards."""

    model_config = ConfigDict(extra="forbid")

    incident_family: IncidentFamily = IncidentFamily.CONNECTION_POOL_EXHAUSTION
    selection_state: RepresentativeSelectionState
    representative_incident_ids: tuple[RecordIdentifier, ...] = Field(
        min_length=1,
        max_length=4,
    )
    candidate_evidence: tuple[CandidateSelectionEvidence, ...] = Field(
        min_length=2,
        max_length=4,
    )
    selection_reason: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_result_cardinality(self) -> "RepresentativeSelectionResult":
        if (
            self.selection_state is RepresentativeSelectionState.SINGLE_REPRESENTATIVE
            and len(self.representative_incident_ids) != 1
        ):
            raise ValueError("single_representative results require exactly one card")
        if (
            self.selection_state is RepresentativeSelectionState.EXPLICIT_TIE
            and len(self.representative_incident_ids) < 2
        ):
            raise ValueError("explicit_tie results require at least two cards")
        return self


class StrictDominanceRepresentativeSelector:
    """Select a representative only when structured evidence strictly dominates.

    Candidate order is never a selection input. Identifiers are sorted only
    after dominance has already determined a tie set, making trace output
    deterministic without turning identifiers into a tie-break rule.
    """

    def select(
        self,
        *,
        intake: RepresentativeSelectionIntake,
        candidate_incident_ids: tuple[RecordIdentifier, ...],
        incidents: tuple[HistoricalIncidentCard, ...],
    ) -> RepresentativeSelectionResult:
        candidate_cards = _resolve_selection_candidates(
            candidate_incident_ids=candidate_incident_ids,
            incidents=incidents,
        )
        evidence_by_id = {
            card.incident_id: _build_candidate_evidence(card=card, intake=intake)
            for card in candidate_cards
        }

        dominates: dict[RecordIdentifier, set[RecordIdentifier]] = {
            card.incident_id: set() for card in candidate_cards
        }
        dominated_by: dict[RecordIdentifier, set[RecordIdentifier]] = {
            card.incident_id: set() for card in candidate_cards
        }
        for left_card in candidate_cards:
            for right_card in candidate_cards:
                if left_card.incident_id == right_card.incident_id:
                    continue
                if _strictly_dominates(
                    left=evidence_by_id[left_card.incident_id],
                    right=evidence_by_id[right_card.incident_id],
                ):
                    dominates[left_card.incident_id].add(right_card.incident_id)
                    dominated_by[right_card.incident_id].add(left_card.incident_id)

        winner_ids = tuple(
            sorted(
                incident_id
                for incident_id, dominators in dominated_by.items()
                if not dominators
            )
        )
        if len(winner_ids) == 1:
            outcome = RepresentativeSelectionState.SINGLE_REPRESENTATIVE
            selection_reason = (
                "One policy-admitted candidate strictly dominated every other "
                "candidate on typed identity, change-context, and operational-signal evidence."
            )
        else:
            outcome = RepresentativeSelectionState.EXPLICIT_TIE
            selection_reason = (
                "No single policy-admitted candidate strictly dominated every other "
                "candidate; the selector preserves the non-dominated tie set."
            )

        trace: list[CandidateSelectionEvidence] = []
        for incident_id in sorted(evidence_by_id):
            evidence = evidence_by_id[incident_id]
            if incident_id in winner_ids:
                selection_state = outcome
                reasons = _winner_reasons(
                    evidence=evidence,
                    tied=outcome is RepresentativeSelectionState.EXPLICIT_TIE,
                )
            else:
                selection_state = None
                reasons = (
                    "Another candidate had structured evidence that strictly dominated this card.",
                )

            trace.append(
                evidence.model_copy(
                    update={
                        "strict_dominates_incident_ids": tuple(sorted(dominates[incident_id])),
                        "dominated_by_incident_ids": tuple(sorted(dominated_by[incident_id])),
                        "selection_state": selection_state,
                        "reasons": reasons,
                    }
                )
            )

        return RepresentativeSelectionResult(
            selection_state=outcome,
            representative_incident_ids=winner_ids,
            candidate_evidence=tuple(trace),
            selection_reason=selection_reason,
        )


def _resolve_selection_candidates(
    *,
    candidate_incident_ids: tuple[RecordIdentifier, ...],
    incidents: tuple[HistoricalIncidentCard, ...],
) -> tuple[HistoricalIncidentCard, ...]:
    if len(candidate_incident_ids) < 2:
        raise SelectionInputError("representative selection requires at least two candidate cards")
    if len(set(candidate_incident_ids)) != len(candidate_incident_ids):
        raise SelectionInputError("candidate_incident_ids must not repeat")

    incidents_by_id = {incident.incident_id: incident for incident in incidents}
    cards: list[HistoricalIncidentCard] = []
    for incident_id in candidate_incident_ids:
        card = incidents_by_id.get(incident_id)
        if card is None:
            raise SelectionInputError(f"unknown candidate incident: {incident_id}")
        if card.incident_family is not IncidentFamily.CONNECTION_POOL_EXHAUSTION:
            raise SelectionInputError(
                "representative selection currently supports only "
                f"connection_pool_exhaustion cards: {incident_id}"
            )
        if card.selection_signature is None:
            raise SelectionInputError(
                f"candidate lacks schema-derived selection_signature: {incident_id}"
            )
        cards.append(card)
    return tuple(cards)


def _build_candidate_evidence(
    *,
    card: HistoricalIncidentCard,
    intake: RepresentativeSelectionIntake,
) -> CandidateSelectionEvidence:
    signature = card.selection_signature
    if signature is None:
        raise SelectionInputError(
            f"candidate lacks schema-derived selection_signature: {card.incident_id}"
        )
    signature_signals = {signal.signal_family for signal in signature.operational_signals}
    matching_signals = tuple(
        sorted(
            signature_signals & set(intake.operational_signal_families),
            key=lambda signal: signal.value,
        )
    )
    contradicted_signals = tuple(
        sorted(
            signature_signals & set(intake.contradicted_signal_families),
            key=lambda signal: signal.value,
        )
    )
    return CandidateSelectionEvidence(
        incident_id=card.incident_id,
        service_alignment=_alignment_for_service(
            intake.service,
            signature.service,
        ),
        component_alignment=_alignment_for_component(
            intake.component,
            signature.component,
        ),
        change_context_alignment=_alignment_for_change_context(
            intake.change_context,
            signature.change_context,
        ),
        matching_signal_families=matching_signals,
        contradicted_signal_families=contradicted_signals,
        reasons=("Candidate evidence was derived from typed selection intake and card signature.",),
    )


def _alignment_for_service(
    observed: RelayService | None,
    candidate: RelayService,
) -> SelectionAlignment:
    if observed is None:
        return SelectionAlignment.UNKNOWN
    return SelectionAlignment.MATCH if observed is candidate else SelectionAlignment.MISMATCH


def _alignment_for_component(
    observed: RelayComponent | None,
    candidate: RelayComponent,
) -> SelectionAlignment:
    if observed is None:
        return SelectionAlignment.UNKNOWN
    return SelectionAlignment.MATCH if observed is candidate else SelectionAlignment.MISMATCH


def _alignment_for_change_context(
    observed: ChangeContext | None,
    candidate: ChangeContext,
) -> SelectionAlignment:
    if observed is None:
        return SelectionAlignment.UNKNOWN
    return SelectionAlignment.MATCH if observed is candidate else SelectionAlignment.MISMATCH


def _strictly_dominates(
    *,
    left: CandidateSelectionEvidence,
    right: CandidateSelectionEvidence,
) -> bool:
    """Return whether left is no worse everywhere and stronger somewhere.

    Identity is deliberately decomposed into service and component. This avoids
    a hidden priority rule: a service match cannot silently outrank an exact
    component match, and vice versa. The same is true for change context,
    matching signal families, and contradicted signal families.
    """

    alignment_pairs = (
        (left.service_alignment, right.service_alignment),
        (left.component_alignment, right.component_alignment),
        (left.change_context_alignment, right.change_context_alignment),
    )
    no_worse_alignment = all(
        _alignment_rank(left_value) >= _alignment_rank(right_value)
        for left_value, right_value in alignment_pairs
    )
    if not no_worse_alignment:
        return False

    left_matching = set(left.matching_signal_families)
    right_matching = set(right.matching_signal_families)
    left_contradicted = set(left.contradicted_signal_families)
    right_contradicted = set(right.contradicted_signal_families)

    if not left_matching.issuperset(right_matching):
        return False
    if not left_contradicted.issubset(right_contradicted):
        return False

    stronger_alignment = any(
        _alignment_rank(left_value) > _alignment_rank(right_value)
        for left_value, right_value in alignment_pairs
    )
    stronger_matching = left_matching > right_matching
    fewer_contradictions = left_contradicted < right_contradicted
    return stronger_alignment or stronger_matching or fewer_contradictions


def _alignment_rank(alignment: SelectionAlignment) -> int:
    return {
        SelectionAlignment.MISMATCH: 0,
        SelectionAlignment.UNKNOWN: 1,
        SelectionAlignment.MATCH: 2,
    }[alignment]


def _winner_reasons(
    *,
    evidence: CandidateSelectionEvidence,
    tied: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if evidence.service_alignment is SelectionAlignment.MATCH:
        reasons.append("Service identity aligns with typed intake evidence.")
    if evidence.component_alignment is SelectionAlignment.MATCH:
        reasons.append("Component identity aligns with typed intake evidence.")
    if evidence.change_context_alignment is SelectionAlignment.MATCH:
        reasons.append("Change context aligns with typed intake evidence.")
    if evidence.matching_signal_families:
        signals = ", ".join(signal.value for signal in evidence.matching_signal_families)
        reasons.append(f"Matching operational signal families: {signals}.")
    if evidence.contradicted_signal_families:
        signals = ", ".join(signal.value for signal in evidence.contradicted_signal_families)
        reasons.append(f"Card carries intake-contradicted signal families: {signals}.")
    if tied:
        reasons.append("No candidate strictly dominated this card under the contract.")
    if not reasons:
        reasons.append("No typed evidence distinguished this candidate from the non-dominated set.")
    return tuple(reasons)
