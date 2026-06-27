"""Regression tests for the ADR-0033 conditional selection integration."""

from __future__ import annotations

from pathlib import Path

import pytest

from incident_precedent_harness.decisions.conditional_representative_selection import (
    ConditionalRepresentativeSelectionPolicy,
    RepresentativeSelectionRefinementStatus,
)
from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.decisions.strict_dominance_selection import (
    SelectionInputError,
    StrictDominanceRepresentativeSelector,
)
from incident_precedent_harness.domain.incident_data import (
    EvalCase,
    ObservedVerificationFact,
    RepresentativeSelectionIntake,
)
from incident_precedent_harness.domain.incident_enums import (
    ChangeContext,
    EvidenceDecisionState,
    OperationalSignalFamily,
    RelayComponent,
    RelayService,
    RequiredVerificationFact,
    VerificationFactStatus,
)
from incident_precedent_harness.retrieval.models import KeywordCandidate
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository

ROOT = Path(__file__).resolve().parents[2]


def _repository() -> JsonDatasetRepository:
    return JsonDatasetRepository(ROOT)


def _case() -> EvalCase:
    return EvalCase(
        eval_id="EVAL-999",
        split="calibration",
        input_summary=(
            "Database connection pool utilization and acquisition latency are confirmed "
            "elevated while active connections are high. Migration lock waits are contradicted."
        ),
        expected_decision_state=EvidenceDecisionState.EVIDENCE_FOUND,
        acceptable_precedent_ids=("INC-009",),
        expected_candidate_procedure_ids=("RB-003",),
        observed_facts=(
            ObservedVerificationFact(
                fact=RequiredVerificationFact.DATABASE_CONNECTION_POOL_UTILIZATION,
                status=VerificationFactStatus.CONFIRMED,
            ),
            ObservedVerificationFact(
                fact=RequiredVerificationFact.DATABASE_CONNECTION_ACQUIRE_LATENCY,
                status=VerificationFactStatus.CONFIRMED,
            ),
            ObservedVerificationFact(
                fact=RequiredVerificationFact.ACTIVE_DATABASE_CONNECTIONS,
                status=VerificationFactStatus.CONFIRMED,
            ),
            ObservedVerificationFact(
                fact=RequiredVerificationFact.MIGRATION_LOCK_WAITS,
                status=VerificationFactStatus.CONTRADICTED,
            ),
            ObservedVerificationFact(
                fact=RequiredVerificationFact.ERROR_RATE_BY_COMPONENT,
                status=VerificationFactStatus.CONFIRMED,
            ),
        ),
        failure_label_intent=("conditional_selection_integration",),
        acceptance_reason="Controlled conditional representative-selection integration test.",
    )


def _ranked(*incident_ids: str) -> tuple[KeywordCandidate, ...]:
    return tuple(
        KeywordCandidate(
            incident_id=incident_id,
            rank=index,
            score=float(len(incident_ids) - index + 1),
            matched_terms=(),
        )
        for index, incident_id in enumerate(incident_ids, start=1)
    )


def _single_winner_intake() -> RepresentativeSelectionIntake:
    return RepresentativeSelectionIntake(
        service=RelayService.PAYMENTS_API,
        component=RelayComponent.POSTGRES_CLIENT_POOL,
        change_context=ChangeContext.NONE,
        operational_signal_families=(
            OperationalSignalFamily.CONNECTION_POOL_PRESSURE,
            OperationalSignalFamily.ACTIVE_CONNECTION_PRESSURE,
        ),
    )


def _integration() -> tuple[
    ConditionalRepresentativeSelectionPolicy,
    tuple,
    tuple,
]:
    repository = _repository()
    return (
        ConditionalRepresentativeSelectionPolicy(AntiAnchoringDecisionPolicy()),
        repository.load_incidents(),
        repository.load_procedures(),
    )


def test_single_winner_narrows_display_without_mutating_policy_contract() -> None:
    integration, incidents, procedures = _integration()
    baseline = AntiAnchoringDecisionPolicy().evaluate(
        intake=_case(),
        ranked_candidates=_ranked("INC-010", "INC-009"),
        incidents=incidents,
        procedures=procedures,
    )

    result = integration.evaluate(
        intake=_case(),
        ranked_candidates=_ranked("INC-010", "INC-009"),
        incidents=incidents,
        procedures=procedures,
        selection_intake=_single_winner_intake(),
    )

    assert result.policy_decision == baseline
    assert result.policy_decision.retained_precedent_ids == ("INC-010",)
    assert result.policy_decision.candidate_procedure_ids == ("RB-003",)
    assert result.policy_decision.missing_critical_facts == ()
    assert result.refinement.status is (
        RepresentativeSelectionRefinementStatus.SINGLE_REPRESENTATIVE_APPLIED
    )
    assert result.refinement.displayed_representative_ids == ("INC-009",)
    assert result.refinement.policy_admitted_candidate_ids == ("INC-009", "INC-010")


def test_explicit_tie_preserves_the_full_non_dominated_set() -> None:
    integration, incidents, procedures = _integration()

    result = integration.evaluate(
        intake=_case(),
        ranked_candidates=_ranked("INC-010", "INC-009"),
        incidents=incidents,
        procedures=procedures,
        selection_intake=RepresentativeSelectionIntake(
            operational_signal_families=(
                OperationalSignalFamily.CONNECTION_POOL_PRESSURE,
            ),
        ),
    )

    assert result.refinement.status is (
        RepresentativeSelectionRefinementStatus.EXPLICIT_TIE_APPLIED
    )
    assert result.refinement.displayed_representative_ids == ("INC-009", "INC-010")
    assert result.policy_decision.decision_state is EvidenceDecisionState.EVIDENCE_FOUND
    assert result.policy_decision.candidate_procedure_ids == ("RB-003",)


def test_absent_selection_intake_keeps_legacy_display_contract() -> None:
    integration, incidents, procedures = _integration()

    result = integration.evaluate(
        intake=_case(),
        ranked_candidates=_ranked("INC-010", "INC-009"),
        incidents=incidents,
        procedures=procedures,
        selection_intake=None,
    )

    assert result.refinement.status is RepresentativeSelectionRefinementStatus.NOT_REQUESTED
    assert result.refinement.displayed_representative_ids == ("INC-010",)
    assert result.refinement.selector_invoked is False


def test_unsupported_family_bypasses_selector_and_preserves_admitted_pool() -> None:
    integration, incidents, procedures = _integration()
    queue_case = EvalCase(
        eval_id="EVAL-998",
        split="calibration",
        input_summary="Queue depth and consumer error rate are confirmed elevated.",
        expected_decision_state=EvidenceDecisionState.EVIDENCE_FOUND,
        acceptable_precedent_ids=("INC-001",),
        expected_candidate_procedure_ids=("RB-002",),
        observed_facts=(
            ObservedVerificationFact(
                fact=RequiredVerificationFact.QUEUE_DEPTH,
                status=VerificationFactStatus.CONFIRMED,
            ),
            ObservedVerificationFact(
                fact=RequiredVerificationFact.CONSUMER_ERROR_RATE,
                status=VerificationFactStatus.CONFIRMED,
            ),
            ObservedVerificationFact(
                fact=RequiredVerificationFact.WORKER_DEPLOYMENT_VERSION,
                status=VerificationFactStatus.CONFIRMED,
            ),
        ),
        failure_label_intent=("unsupported_family_bypass",),
        acceptance_reason="Unsupported family must bypass typed representative selection.",
    )

    result = integration.evaluate(
        intake=queue_case,
        ranked_candidates=_ranked("INC-001", "INC-002"),
        incidents=incidents,
        procedures=procedures,
        selection_intake=_single_winner_intake(),
    )

    assert result.refinement.status is (
        RepresentativeSelectionRefinementStatus.SELECTION_NOT_APPLIED
    )
    assert result.refinement.displayed_representative_ids == ("INC-001", "INC-002")
    assert result.refinement.selector_invoked is False


def test_selector_error_preserves_the_complete_policy_admitted_pool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    integration, incidents, procedures = _integration()

    def _raise_selection_error(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise SelectionInputError("test-only selector failure")

    monkeypatch.setattr(StrictDominanceRepresentativeSelector, "select", _raise_selection_error)

    result = integration.evaluate(
        intake=_case(),
        ranked_candidates=_ranked("INC-010", "INC-009"),
        incidents=incidents,
        procedures=procedures,
        selection_intake=_single_winner_intake(),
    )

    assert result.refinement.status is (
        RepresentativeSelectionRefinementStatus.SELECTION_NOT_APPLIED
    )
    assert result.refinement.displayed_representative_ids == ("INC-009", "INC-010")
    assert result.refinement.selector_invoked is False


def test_existing_calibration_policy_states_remain_policy_owned_without_selection_request() -> None:
    repository = _repository()
    integration = ConditionalRepresentativeSelectionPolicy(AntiAnchoringDecisionPolicy())
    policy = AntiAnchoringDecisionPolicy()
    incidents = repository.load_incidents()
    procedures = repository.load_procedures()

    for case in repository.load_calibration_cases():
        from incident_precedent_harness.retrieval.keyword import KeywordRetriever

        ranked = KeywordRetriever(incidents).rank(case.input_summary, top_k=5)
        baseline = policy.evaluate(
            intake=case,
            ranked_candidates=ranked,
            incidents=incidents,
            procedures=procedures,
        )
        integrated = integration.evaluate(
            intake=case,
            ranked_candidates=ranked,
            incidents=incidents,
            procedures=procedures,
            selection_intake=None,
        )
        assert integrated.policy_decision == baseline
        assert integrated.refinement.status is (
            RepresentativeSelectionRefinementStatus.NOT_REQUESTED
        )


@pytest.mark.parametrize("decision_state", tuple(EvidenceDecisionState))
def test_every_top_level_policy_state_remains_owned_by_the_policy(
    decision_state: EvidenceDecisionState,
) -> None:
    from incident_precedent_harness.decisions.models import PolicyDecisionResult

    class _StatePolicy:
        def evaluate(self, **kwargs):  # type: ignore[no-untyped-def]
            return PolicyDecisionResult(
                decision_state=decision_state,
                assessments=(),
                safety_notes=("Synthetic policy-owned state for boundary testing.",),
            )

    integration = ConditionalRepresentativeSelectionPolicy(_StatePolicy())  # type: ignore[arg-type]
    result = integration.evaluate(
        intake=_case(),
        ranked_candidates=(),
        incidents=(),
        procedures=(),
        selection_intake=None,
    )

    assert result.policy_decision.decision_state is decision_state
    assert result.refinement.status is RepresentativeSelectionRefinementStatus.NOT_REQUESTED
