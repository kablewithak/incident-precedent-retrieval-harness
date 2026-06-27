"""Conditional post-admission representative-selection refinement.

This boundary composes ``AntiAnchoringDecisionPolicy`` with the already-governed
strict-dominance selector. It never mutates ``PolicyDecisionResult``. Instead it
produces a separately typed display refinement that a presentation layer may use
only after inspecting the policy-owned result.

The implementation intentionally relies on the policy's existing
``evaluate_with_shadow`` admission inventory. That inventory contains only
compatibility-admitted candidates and is not derived from retrieval rank,
procedure metadata, evaluator outcomes, or held-out assets.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from incident_precedent_harness.decisions.models import (
    FamilySelectionIntakeBinding,
    PolicyDecisionResult,
    PolicyShadowRequest,
)
from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.decisions.strict_dominance_selection import (
    CandidateSelectionEvidence,
)
from incident_precedent_harness.domain.incident_data import (
    CandidateInvestigationProcedure,
    HistoricalIncidentCard,
    RepresentativeSelectionIntake,
)
from incident_precedent_harness.domain.incident_enums import (
    EvidenceDecisionState,
    IncidentFamily,
)
from incident_precedent_harness.retrieval.models import KeywordCandidate


class RepresentativeSelectionRefinementStatus(str, Enum):
    """Trace-safe state for the optional post-admission display refinement."""

    NOT_REQUESTED = "not_requested"
    SELECTION_NOT_APPLIED = "selection_not_applied"
    SINGLE_REPRESENTATIVE_APPLIED = "single_representative_applied"
    EXPLICIT_TIE_APPLIED = "explicit_tie_applied"


class RepresentativeSelectionRefinement(BaseModel):
    """A display-only selection result layered over a policy-owned decision.

    ``policy_admitted_candidate_ids`` is the complete same-boundary pool that
    was available after deterministic compatibility admission. It is never
    inferred from retrieval order. ``displayed_representative_ids`` may narrow
    only when the standalone selector has produced a valid typed result.
    """

    model_config = ConfigDict(extra="forbid")

    status: RepresentativeSelectionRefinementStatus
    incident_family: IncidentFamily | None = None
    policy_admitted_candidate_ids: tuple[str, ...] = Field(max_length=12)
    displayed_representative_ids: tuple[str, ...] = Field(max_length=12)
    selection_intake_present: bool
    selector_invoked: bool
    trace_reason: str = Field(min_length=1, max_length=500)
    candidate_evidence: tuple[CandidateSelectionEvidence, ...] = ()

    @model_validator(mode="after")
    def validate_refinement_contract(self) -> "RepresentativeSelectionRefinement":
        if len(set(self.policy_admitted_candidate_ids)) != len(
            self.policy_admitted_candidate_ids
        ):
            raise ValueError("policy_admitted_candidate_ids must not repeat")
        if len(set(self.displayed_representative_ids)) != len(
            self.displayed_representative_ids
        ):
            raise ValueError("displayed_representative_ids must not repeat")
        if not set(self.displayed_representative_ids).issubset(
            self.policy_admitted_candidate_ids
        ):
            raise ValueError(
                "displayed representative IDs must remain within the policy-admitted pool"
            )

        if self.status is RepresentativeSelectionRefinementStatus.NOT_REQUESTED:
            if self.selector_invoked or self.candidate_evidence:
                raise ValueError("not_requested refinement cannot expose selector output")

        if self.status is RepresentativeSelectionRefinementStatus.SELECTION_NOT_APPLIED:
            if self.selector_invoked or self.candidate_evidence:
                raise ValueError(
                    "selection_not_applied refinement cannot expose selector output"
                )
            if (
                self.policy_admitted_candidate_ids
                and self.displayed_representative_ids
                != self.policy_admitted_candidate_ids
            ):
                raise ValueError(
                    "selection_not_applied must preserve the complete policy-admitted pool"
                )

        if self.status is RepresentativeSelectionRefinementStatus.SINGLE_REPRESENTATIVE_APPLIED:
            if not self.selector_invoked or len(self.displayed_representative_ids) != 1:
                raise ValueError(
                    "single_representative_applied requires exactly one selector winner"
                )
            if not self.candidate_evidence:
                raise ValueError(
                    "single_representative_applied requires selector trace evidence"
                )

        if self.status is RepresentativeSelectionRefinementStatus.EXPLICIT_TIE_APPLIED:
            if not self.selector_invoked or len(self.displayed_representative_ids) < 2:
                raise ValueError(
                    "explicit_tie_applied requires the non-dominated tie set"
                )
            if not self.candidate_evidence:
                raise ValueError("explicit_tie_applied requires selector trace evidence")
        return self


class ConditionalRepresentativeSelectionResult(BaseModel):
    """Policy result plus an optional, non-authoritative display refinement."""

    model_config = ConfigDict(extra="forbid")

    policy_decision: PolicyDecisionResult
    refinement: RepresentativeSelectionRefinement

    @model_validator(mode="after")
    def preserve_policy_authority(self) -> "ConditionalRepresentativeSelectionResult":
        if (
            self.policy_decision.decision_state
            in {
                EvidenceDecisionState.PROVIDER_DEGRADED,
                EvidenceDecisionState.INSUFFICIENT_PRECEDENT,
            }
            and self.refinement.status
            in {
                RepresentativeSelectionRefinementStatus.SINGLE_REPRESENTATIVE_APPLIED,
                RepresentativeSelectionRefinementStatus.EXPLICIT_TIE_APPLIED,
            }
        ):
            raise ValueError(
                "selection cannot be applied to provider-degraded or insufficient-precedent decisions"
            )
        return self


@dataclass(frozen=True, slots=True)
class ConditionalRepresentativeSelectionPolicy:
    """Apply the ADR-0033 post-admission display-refinement contract.

    The wrapper intentionally delegates normal compatibility admission and all
    top-level safety behavior to ``AntiAnchoringDecisionPolicy``. It supplies a
    selection intake only to the existing shadow-admission path and exposes a
    display result only when the precise ADR preconditions are met.
    """

    policy: AntiAnchoringDecisionPolicy

    def evaluate(
        self,
        *,
        intake,
        ranked_candidates: tuple[KeywordCandidate, ...],
        incidents: tuple[HistoricalIncidentCard, ...],
        procedures: tuple[CandidateInvestigationProcedure, ...],
        selection_intake: RepresentativeSelectionIntake | None,
    ) -> ConditionalRepresentativeSelectionResult:
        """Evaluate policy first, then conditionally refine displayed precedents.

        The return value preserves the original ``PolicyDecisionResult`` byte for
        byte as the policy authority. The refinement is a separately typed view.
        """

        if selection_intake is None:
            policy_decision = self.policy.evaluate(
                intake=intake,
                ranked_candidates=ranked_candidates,
                incidents=incidents,
                procedures=procedures,
            )
            return ConditionalRepresentativeSelectionResult(
                policy_decision=policy_decision,
                refinement=RepresentativeSelectionRefinement(
                    status=RepresentativeSelectionRefinementStatus.NOT_REQUESTED,
                    policy_admitted_candidate_ids=policy_decision.retained_precedent_ids,
                    displayed_representative_ids=policy_decision.retained_precedent_ids,
                    selection_intake_present=False,
                    selector_invoked=False,
                    trace_reason=(
                        "No validated representative-selection intake was supplied; "
                        "the legacy policy display remains unchanged."
                    ),
                ),
            )

        shadow_result = self.policy.evaluate_with_shadow(
            intake=intake,
            ranked_candidates=ranked_candidates,
            incidents=incidents,
            procedures=procedures,
            shadow_request=PolicyShadowRequest(
                selection_intake_bindings=(
                    FamilySelectionIntakeBinding(
                        incident_family=IncidentFamily.CONNECTION_POOL_EXHAUSTION,
                        selection_intake=selection_intake,
                    ),
                )
            ),
        )
        policy_decision = shadow_result.policy_result
        admitted_ids = tuple(
            sorted(
                incident_id
                for admission in shadow_result.family_admission_sets
                for incident_id in admission.admitted_candidate_ids
            )
        )

        if policy_decision.decision_state is EvidenceDecisionState.PROVIDER_DEGRADED:
            return self._not_applied(
                policy_decision=policy_decision,
                admitted_ids=admitted_ids,
                reason=(
                    "Representative selection is blocked because provider-degraded "
                    "handling is policy-owned."
                ),
            )
        if policy_decision.decision_state is EvidenceDecisionState.INSUFFICIENT_PRECEDENT:
            return self._not_applied(
                policy_decision=policy_decision,
                admitted_ids=admitted_ids,
                reason=(
                    "Representative selection is blocked because no policy-admitted "
                    "precedent pool exists."
                ),
            )

        if len(shadow_result.family_admission_sets) != 1:
            return self._not_applied(
                policy_decision=policy_decision,
                admitted_ids=admitted_ids,
                reason=(
                    "Representative selection is not applied because the policy-admitted "
                    "pool spans multiple incident families."
                ),
            )

        admission_set = shadow_result.family_admission_sets[0]
        if admission_set.incident_family is not IncidentFamily.CONNECTION_POOL_EXHAUSTION:
            return self._not_applied(
                policy_decision=policy_decision,
                admitted_ids=admission_set.admitted_candidate_ids,
                incident_family=admission_set.incident_family,
                reason=(
                    "Representative selection is unsupported for this policy-admitted "
                    "incident family."
                ),
            )

        if len(admission_set.admitted_candidate_ids) < 2:
            return self._not_applied(
                policy_decision=policy_decision,
                admitted_ids=admission_set.admitted_candidate_ids,
                incident_family=admission_set.incident_family,
                reason=(
                    "Representative selection is not applicable because the "
                    "policy-admitted family has fewer than two candidates."
                ),
            )

        trace = next(
            (
                item
                for item in shadow_result.selection_traces
                if item.incident_family is admission_set.incident_family
            ),
            None,
        )
        if trace is None:
            return self._not_applied(
                policy_decision=policy_decision,
                admitted_ids=admission_set.admitted_candidate_ids,
                incident_family=admission_set.incident_family,
                reason=(
                    "Representative selection was not applied because no matching "
                    "trace-safe policy selection trace was produced."
                ),
            )

        if not trace.selector_invoked:
            return self._not_applied(
                policy_decision=policy_decision,
                admitted_ids=admission_set.admitted_candidate_ids,
                incident_family=admission_set.incident_family,
                reason=trace.unavailable_reason
                or (
                    "Representative selection was not applied because the typed "
                    "selector preconditions were not satisfied."
                ),
            )

        if trace.selection_state.value == "single_representative":
            return ConditionalRepresentativeSelectionResult(
                policy_decision=policy_decision,
                refinement=RepresentativeSelectionRefinement(
                    status=RepresentativeSelectionRefinementStatus.SINGLE_REPRESENTATIVE_APPLIED,
                    incident_family=admission_set.incident_family,
                    policy_admitted_candidate_ids=admission_set.admitted_candidate_ids,
                    displayed_representative_ids=trace.representative_incident_ids,
                    selection_intake_present=True,
                    selector_invoked=True,
                    trace_reason=(
                        "Typed strict-dominance selection narrowed the display to one "
                        "policy-admitted representative without altering policy authority."
                    ),
                    candidate_evidence=trace.candidate_evidence,
                ),
            )

        if trace.selection_state.value == "explicit_tie":
            return ConditionalRepresentativeSelectionResult(
                policy_decision=policy_decision,
                refinement=RepresentativeSelectionRefinement(
                    status=RepresentativeSelectionRefinementStatus.EXPLICIT_TIE_APPLIED,
                    incident_family=admission_set.incident_family,
                    policy_admitted_candidate_ids=admission_set.admitted_candidate_ids,
                    displayed_representative_ids=trace.representative_incident_ids,
                    selection_intake_present=True,
                    selector_invoked=True,
                    trace_reason=(
                        "Typed strict-dominance selection preserved the full "
                        "non-dominated policy-admitted tie set."
                    ),
                    candidate_evidence=trace.candidate_evidence,
                ),
            )

        return self._not_applied(
            policy_decision=policy_decision,
            admitted_ids=admission_set.admitted_candidate_ids,
            incident_family=admission_set.incident_family,
            reason=(
                "Representative selection was not applied because the selector did "
                "not return a permitted terminal state."
            ),
        )

    @staticmethod
    def _not_applied(
        *,
        policy_decision: PolicyDecisionResult,
        admitted_ids: tuple[str, ...],
        reason: str,
        incident_family: IncidentFamily | None = None,
    ) -> ConditionalRepresentativeSelectionResult:
        return ConditionalRepresentativeSelectionResult(
            policy_decision=policy_decision,
            refinement=RepresentativeSelectionRefinement(
                status=RepresentativeSelectionRefinementStatus.SELECTION_NOT_APPLIED,
                incident_family=incident_family,
                policy_admitted_candidate_ids=admitted_ids,
                displayed_representative_ids=admitted_ids,
                selection_intake_present=True,
                selector_invoked=False,
                trace_reason=reason,
            ),
        )
