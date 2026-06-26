from __future__ import annotations

from pathlib import Path

import pytest

from incident_precedent_harness.decisions.models import (
    FamilySelectionIntakeBinding,
    PolicyShadowRequest,
    ShadowSelectionState,
)
from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.domain.incident_data import RepresentativeSelectionIntake
from incident_precedent_harness.domain.incident_enums import IncidentFamily
from incident_precedent_harness.evals.shadow_integration import (
    load_shadow_integration_calibration_cases,
)
from incident_precedent_harness.retrieval.keyword import KeywordRetriever
from incident_precedent_harness.retrieval.models import KeywordCandidate
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository


@pytest.fixture()
def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture()
def policy_inputs(repository_root: Path):
    repository = JsonDatasetRepository(repository_root)
    incidents = repository.load_incidents()
    procedures = repository.load_procedures()
    cases = {case.eval_id: case for case in repository.load_calibration_cases()}
    return incidents, procedures, cases, KeywordRetriever(incidents)


@pytest.fixture()
def shadow_cases(repository_root: Path):
    return {
        case.shadow_case_id: case
        for case in load_shadow_integration_calibration_cases(repository_root)
    }


def _ranked(policy_inputs, policy_case_id: str) -> tuple[KeywordCandidate, ...]:
    _, _, cases, retriever = policy_inputs
    return retriever.rank(cases[policy_case_id].input_summary, top_k=5)


def _trace_projection(trace) -> dict[str, object]:
    return {
        "incident_family": trace.incident_family,
        "admitted_candidate_ids": trace.admitted_candidate_ids,
        "selection_intake_present": trace.selection_intake_present,
        "selector_invoked": trace.selector_invoked,
        "selection_state": trace.selection_state,
        "representative_incident_ids": trace.representative_incident_ids,
        "unavailable_reason": trace.unavailable_reason,
    }


@pytest.mark.parametrize(
    "policy_case_id",
    tuple(f"EVAL-{index:03d}" for index in range(1, 13)),
)
def test_shadow_preserves_exact_public_result_for_identical_policy_inputs(
    policy_inputs,
    policy_case_id: str,
) -> None:
    incidents, procedures, cases, _ = policy_inputs
    policy = AntiAnchoringDecisionPolicy()
    ranked_candidates = _ranked(policy_inputs, policy_case_id)

    active_result = policy.evaluate(
        intake=cases[policy_case_id],
        ranked_candidates=ranked_candidates,
        incidents=incidents,
        procedures=procedures,
    )
    shadow_result = policy.evaluate_with_shadow(
        intake=cases[policy_case_id],
        ranked_candidates=ranked_candidates,
        incidents=incidents,
        procedures=procedures,
        shadow_request=PolicyShadowRequest(),
    )

    assert shadow_result.policy_result == active_result


@pytest.mark.parametrize(
    "shadow_case_id",
    tuple(f"SHADOW-CAL-{index:03d}" for index in range(1, 9)),
)
def test_shadow_traces_match_fixed_bridge_fixture_contract(
    policy_inputs,
    shadow_cases,
    shadow_case_id: str,
) -> None:
    incidents, procedures, cases, _ = policy_inputs
    fixture = shadow_cases[shadow_case_id]
    policy_case = cases[fixture.policy_case_id]
    policy = AntiAnchoringDecisionPolicy()
    active_result = policy.evaluate(
        intake=policy_case,
        ranked_candidates=_ranked(policy_inputs, fixture.policy_case_id),
        incidents=incidents,
        procedures=procedures,
    )
    shadow_result = policy.evaluate_with_shadow(
        intake=policy_case,
        ranked_candidates=_ranked(policy_inputs, fixture.policy_case_id),
        incidents=incidents,
        procedures=procedures,
        shadow_request=PolicyShadowRequest(
            selection_intake_bindings=fixture.selection_intake_bindings
        ),
    )

    assert shadow_result.policy_result == active_result
    assert [_trace_projection(trace) for trace in shadow_result.selection_traces] == [
        {
            "incident_family": expected.incident_family,
            "admitted_candidate_ids": expected.admitted_candidate_ids,
            "selection_intake_present": expected.selection_intake_present,
            "selector_invoked": expected.selector_invoked,
            "selection_state": expected.selection_state,
            "representative_incident_ids": expected.representative_incident_ids,
            "unavailable_reason": expected.unavailable_reason,
        }
        for expected in fixture.expected_traces
    ]


def test_connection_pool_shadow_trace_is_order_invariant_while_legacy_policy_difference_is_observed(
    policy_inputs,
    shadow_cases,
) -> None:
    incidents, procedures, cases, _ = policy_inputs
    fixture = shadow_cases["SHADOW-CAL-005"]
    policy_case = cases[fixture.policy_case_id]
    canonical_candidates = _ranked(policy_inputs, fixture.policy_case_id)
    reversed_candidates = tuple(
        KeywordCandidate(
            incident_id=candidate.incident_id,
            rank=index,
            score=candidate.score,
            matched_terms=candidate.matched_terms,
        )
        for index, candidate in enumerate(reversed(canonical_candidates), start=1)
    )
    request = PolicyShadowRequest(selection_intake_bindings=fixture.selection_intake_bindings)
    policy = AntiAnchoringDecisionPolicy()

    canonical_active = policy.evaluate(
        intake=policy_case,
        ranked_candidates=canonical_candidates,
        incidents=incidents,
        procedures=procedures,
    )
    canonical_shadow = policy.evaluate_with_shadow(
        intake=policy_case,
        ranked_candidates=canonical_candidates,
        incidents=incidents,
        procedures=procedures,
        shadow_request=request,
    )
    reversed_active = policy.evaluate(
        intake=policy_case,
        ranked_candidates=reversed_candidates,
        incidents=incidents,
        procedures=procedures,
    )
    reversed_shadow = policy.evaluate_with_shadow(
        intake=policy_case,
        ranked_candidates=reversed_candidates,
        incidents=incidents,
        procedures=procedures,
        shadow_request=request,
    )

    assert canonical_shadow.policy_result == canonical_active
    assert reversed_shadow.policy_result == reversed_active
    assert canonical_shadow.selection_traces == reversed_shadow.selection_traces
    assert canonical_active != reversed_active
    assert canonical_active.decision_state.value == "evidence_found"
    assert reversed_active.decision_state.value == "missing_critical_facts"
    assert canonical_active.candidate_procedure_ids == ("RB-003",)
    assert reversed_active.candidate_procedure_ids == ()


def test_schema_unavailable_trace_never_falls_back_to_rank_or_id(
    policy_inputs,
    shadow_cases,
) -> None:
    incidents, procedures, cases, _ = policy_inputs
    fixture = shadow_cases["SHADOW-CAL-005"]
    invalid_incidents = tuple(
        incident.model_copy(update={"selection_signature": None})
        if incident.incident_id == "INC-012"
        else incident
        for incident in incidents
    )

    result = AntiAnchoringDecisionPolicy().evaluate_with_shadow(
        intake=cases[fixture.policy_case_id],
        ranked_candidates=_ranked(policy_inputs, fixture.policy_case_id),
        incidents=invalid_incidents,
        procedures=procedures,
        shadow_request=PolicyShadowRequest(
            selection_intake_bindings=fixture.selection_intake_bindings
        ),
    )

    trace = result.selection_traces[0]
    assert trace.selection_state is ShadowSelectionState.UNAVAILABLE
    assert trace.selector_invoked is False
    assert trace.representative_incident_ids == ()
    assert trace.unavailable_reason == (
        "Schema-derived representative selection was unavailable for one or more policy-admitted cards."
    )


def test_shadow_request_rejects_duplicate_family_bindings() -> None:
    binding = FamilySelectionIntakeBinding(
        incident_family=IncidentFamily.CONNECTION_POOL_EXHAUSTION,
        selection_intake=RepresentativeSelectionIntake(),
    )
    with pytest.raises(ValueError, match="must not repeat an incident family"):
        PolicyShadowRequest(selection_intake_bindings=(binding, binding))
