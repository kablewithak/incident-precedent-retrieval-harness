"""Calibration-only preview for connection-pool representative selection.

This module intentionally does not alter ``AntiAnchoringDecisionPolicy``. It
uses that policy only to identify cards that already pass current family
compatibility rules, then compares compatible connection-pool cards using
explicit, data-declared selection signals. Retrieval rank and score are never
read by the selection key.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.domain.incident_data import (
    CandidateInvestigationProcedure,
    EvalCase,
    HistoricalIncidentCard,
    RecordIdentifier,
)
from incident_precedent_harness.domain.incident_enums import (
    ChangeContext,
    EvidenceDecisionState,
    IncidentFamily,
)
from incident_precedent_harness.retrieval.models import KeywordCandidate


class PreviewSelectionStatus(str, Enum):
    """Trace state for a calibration-only representative-selection preview."""

    SELECTED = "selected"
    TIED = "tied"
    NOT_SELECTED = "not_selected"
    NOT_ELIGIBLE = "not_eligible"


class ConnectionPoolSelectionProfile(BaseModel):
    """Explicit, reviewable signals for one connection-pool incident card.

    The fields are card-specific metadata, not inferred labels. They are used
    only after the existing deterministic policy independently finds the card
    compatible with the intake.
    """

    incident_id: RecordIdentifier
    declared_change_context: ChangeContext
    distinguishing_intake_cues: tuple[str, ...] = Field(min_length=1, max_length=12)

    @field_validator("distinguishing_intake_cues")
    @classmethod
    def require_unique_lowercase_cues(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(cue.strip().lower() for cue in value)
        if any(not cue for cue in normalized):
            raise ValueError("distinguishing intake cues must be non-empty")
        if len(set(normalized)) != len(normalized):
            raise ValueError("distinguishing intake cues must be unique")
        return normalized


class ConnectionPoolProfileSet(BaseModel):
    """One calibration-only profile set for the current connection-pool corpus."""

    profile_set_id: str = Field(min_length=1, max_length=100)
    incident_family: IncidentFamily
    profiles: tuple[ConnectionPoolSelectionProfile, ...] = Field(min_length=1, max_length=12)

    @field_validator("profiles")
    @classmethod
    def require_unique_incident_ids(
        cls,
        value: tuple[ConnectionPoolSelectionProfile, ...],
    ) -> tuple[ConnectionPoolSelectionProfile, ...]:
        if len({profile.incident_id for profile in value}) != len(value):
            raise ValueError("connection-pool selection profiles must have unique incident IDs")
        return value


class ConnectionPoolCandidatePreview(BaseModel):
    """Trace-safe evidence for one candidate in the preview selection pool."""

    incident_id: RecordIdentifier
    context_alignment: bool
    matched_cues: tuple[str, ...] = ()
    selection_status: PreviewSelectionStatus
    reasons: tuple[str, ...] = Field(min_length=1, max_length=4)


class ConnectionPoolSelectionPreview(BaseModel):
    """One family-level preview result without changing the live policy result."""

    incident_family: IncidentFamily = IncidentFamily.CONNECTION_POOL_EXHAUSTION
    retained_incident_ids: tuple[RecordIdentifier, ...]
    candidate_previews: tuple[ConnectionPoolCandidatePreview, ...] = Field(min_length=1)
    selection_reason: str = Field(min_length=1, max_length=500)


class ConnectionPoolRepresentativePreview:
    """Preview a connection-pool representative without activating new policy."""

    def __init__(
        self,
        *,
        policy: AntiAnchoringDecisionPolicy,
        profile_set: ConnectionPoolProfileSet,
    ) -> None:
        if profile_set.incident_family is not IncidentFamily.CONNECTION_POOL_EXHAUSTION:
            raise ValueError("only connection_pool_exhaustion profiles are supported in this preview")
        self._policy = policy
        self._profiles_by_id = {profile.incident_id: profile for profile in profile_set.profiles}

    def preview(
        self,
        *,
        intake: EvalCase,
        ranked_candidates: tuple[KeywordCandidate, ...],
        incidents: tuple[HistoricalIncidentCard, ...],
        procedures: tuple[CandidateInvestigationProcedure, ...],
    ) -> ConnectionPoolSelectionPreview | None:
        """Return a preview only when at least two pool cards are already compatible.

        Compatibility remains owned by the current policy. Each candidate is
        assessed in isolation to avoid the existing first-compatible-per-family
        retention behavior affecting the calibration-only candidate pool.
        """
        if not intake.provider_available:
            return None

        incident_by_id = {incident.incident_id: incident for incident in incidents}
        compatible_ids: list[RecordIdentifier] = []
        for candidate in ranked_candidates:
            incident = incident_by_id.get(candidate.incident_id)
            if incident is None or incident.incident_family is not IncidentFamily.CONNECTION_POOL_EXHAUSTION:
                continue
            if incident.incident_id not in self._profiles_by_id:
                continue
            singleton_result = self._policy.evaluate(
                intake=intake,
                ranked_candidates=(candidate,),
                incidents=incidents,
                procedures=procedures,
            )
            if singleton_result.decision_state in {
                EvidenceDecisionState.EVIDENCE_FOUND,
                EvidenceDecisionState.MISSING_CRITICAL_FACTS,
            } and singleton_result.retained_precedent_ids == (incident.incident_id,):
                compatible_ids.append(incident.incident_id)

        if len(compatible_ids) < 2:
            return None

        intake_text = _normalize(intake.input_summary)
        observed_contexts = _declared_contexts(intake_text)
        evidence: list[tuple[RecordIdentifier, bool, tuple[str, ...]]] = []
        for incident_id in compatible_ids:
            profile = self._profiles_by_id[incident_id]
            context_alignment = profile.declared_change_context in observed_contexts
            matched_cues = tuple(
                cue for cue in profile.distinguishing_intake_cues if _cue_matches(cue, intake_text)
            )
            evidence.append((incident_id, context_alignment, matched_cues))

        # The ordered key contains only declared profile signals. It deliberately
        # excludes lexical rank, lexical score, incident ID, procedure ID, and
        # any evaluation label. IDs are sorted only after a genuine tie for stable
        # output serialization.
        strongest_key = max((int(context), len(cues)) for _, context, cues in evidence)
        winner_ids = tuple(
            sorted(
                incident_id
                for incident_id, context, cues in evidence
                if (int(context), len(cues)) == strongest_key
            )
        )
        status_for_winner = (
            PreviewSelectionStatus.SELECTED
            if len(winner_ids) == 1
            else PreviewSelectionStatus.TIED
        )

        previews: list[ConnectionPoolCandidatePreview] = []
        for incident_id, context, cues in sorted(evidence, key=lambda item: item[0]):
            if incident_id in winner_ids:
                previews.append(
                    ConnectionPoolCandidatePreview(
                        incident_id=incident_id,
                        context_alignment=context,
                        matched_cues=cues,
                        selection_status=status_for_winner,
                        reasons=_winner_reasons(context_alignment=context, matched_cues=cues, tied=len(winner_ids) > 1),
                    )
                )
            else:
                previews.append(
                    ConnectionPoolCandidatePreview(
                        incident_id=incident_id,
                        context_alignment=context,
                        matched_cues=cues,
                        selection_status=PreviewSelectionStatus.NOT_SELECTED,
                        reasons=(
                            "A compatible connection-pool card had stronger declared context or cue evidence.",
                        ),
                    )
                )

        if len(winner_ids) == 1:
            reason = "One compatible connection-pool card had the strongest declared selection profile."
        else:
            reason = (
                "Multiple compatible connection-pool cards remained indistinguishable under declared selection signals; "
                "the preview preserves the tie rather than using retriever order."
            )
        return ConnectionPoolSelectionPreview(
            retained_incident_ids=winner_ids,
            candidate_previews=tuple(previews),
            selection_reason=reason,
        )


def load_connection_pool_profile_set(path: Path) -> ConnectionPoolProfileSet:
    """Load the reviewed calibration profile set from a local JSON artifact."""
    return ConnectionPoolProfileSet.model_validate_json(path.read_text(encoding="utf-8"))


def _normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _cue_matches(cue: str, normalized_intake_text: str) -> bool:
    return _normalize(cue) in normalized_intake_text


def _declared_contexts(normalized_intake_text: str) -> frozenset[ChangeContext]:
    contexts: set[ChangeContext] = set()
    if any(phrase in normalized_intake_text for phrase in ("deployment", "rollout", "version")):
        contexts.add(ChangeContext.DEPLOYMENT)
    if any(phrase in normalized_intake_text for phrase in ("migration", "schema migration")):
        contexts.add(ChangeContext.MIGRATION)
    if any(phrase in normalized_intake_text for phrase in ("configuration", "config update", "configuration change")):
        contexts.add(ChangeContext.CONFIGURATION)
    if any(
        phrase in normalized_intake_text
        for phrase in ("without a migration", "no migration", "migration lock waits are absent")
    ):
        contexts.add(ChangeContext.NONE)
    return frozenset(contexts)


def _winner_reasons(*, context_alignment: bool, matched_cues: tuple[str, ...], tied: bool) -> tuple[str, ...]:
    reasons: list[str] = []
    if context_alignment:
        reasons.append("Declared change context aligns with the intake summary.")
    if matched_cues:
        reasons.append("Matched declared incident-specific intake cues: " + ", ".join(matched_cues) + ".")
    if tied:
        reasons.append("No declared profile signal distinguished this card from the tied candidate set.")
    if not reasons:
        reasons.append("No stronger declared profile signal was available than the tied candidate set.")
    return tuple(reasons)
