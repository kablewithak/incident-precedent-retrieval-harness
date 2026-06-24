from __future__ import annotations

from pathlib import Path

import pytest

from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.domain.incident_enums import EvidenceDecisionState, RequiredVerificationFact
from incident_precedent_harness.retrieval import JsonDatasetRepository, KeywordRetriever


@pytest.fixture()
def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture()
def policy_inputs(repository_root: Path):
    repository = JsonDatasetRepository(repository_root)
    incidents = repository.load_incidents()
    procedures = repository.load_procedures()
    cases = {case.eval_id: case for case in repository.load_calibration_cases()}
    return incidents, procedures, cases


def _evaluate(policy_inputs, eval_id: str):
    incidents, procedures, cases = policy_inputs
    retriever = KeywordRetriever(incidents)
    case = cases[eval_id]
    return AntiAnchoringDecisionPolicy().evaluate(
        intake=case,
        ranked_candidates=retriever.rank(case.input_summary, top_k=5),
        incidents=incidents,
        procedures=procedures,
    )


def test_provider_unavailable_blocks_normal_evidence(policy_inputs) -> None:
    result = _evaluate(policy_inputs, "EVAL-004")

    assert result.decision_state is EvidenceDecisionState.PROVIDER_DEGRADED
    assert result.retained_precedent_ids == ()
    assert result.candidate_procedure_ids == ()


@pytest.mark.parametrize("eval_id", ["EVAL-003", "EVAL-008", "EVAL-012"])
def test_insufficient_precedent_abstains_and_blocks_procedures(policy_inputs, eval_id: str) -> None:
    result = _evaluate(policy_inputs, eval_id)

    assert result.decision_state is EvidenceDecisionState.INSUFFICIENT_PRECEDENT
    assert result.retained_precedent_ids == ()
    assert result.candidate_procedure_ids == ()


def test_confirmed_queue_capacity_pattern_surfaces_candidate_procedure(policy_inputs) -> None:
    result = _evaluate(policy_inputs, "EVAL-001")

    assert result.decision_state is EvidenceDecisionState.EVIDENCE_FOUND
    assert result.retained_precedent_ids[0] == "INC-003"
    assert result.candidate_procedure_ids == ("RB-001",)


def test_migration_pattern_blocks_queue_procedure(policy_inputs) -> None:
    result = _evaluate(policy_inputs, "EVAL-005")

    assert result.decision_state is EvidenceDecisionState.EVIDENCE_FOUND
    assert "INC-005" in result.retained_precedent_ids
    assert result.candidate_procedure_ids == ("RB-002",)


@pytest.mark.parametrize(
    ("eval_id", "expected_missing"),
    [
        (
            "EVAL-002",
            {
                RequiredVerificationFact.WORKER_DEPLOYMENT_VERSION,
                RequiredVerificationFact.CONSUMER_ERROR_RATE,
                RequiredVerificationFact.ERROR_RATE_BY_COMPONENT,
            },
        ),
        (
            "EVAL-006",
            {
                RequiredVerificationFact.MIGRATION_LOCK_WAITS,
                RequiredVerificationFact.ACTIVE_DATABASE_CONNECTIONS,
                RequiredVerificationFact.ERROR_RATE_BY_COMPONENT,
            },
        ),
        (
            "EVAL-010",
            {
                RequiredVerificationFact.DATABASE_CONNECTION_POOL_UTILIZATION,
                RequiredVerificationFact.DATABASE_CONNECTION_ACQUIRE_LATENCY,
                RequiredVerificationFact.MIGRATION_LOCK_WAITS,
            },
        ),
    ],
)
def test_missing_critical_facts_withhold_procedures(policy_inputs, eval_id, expected_missing) -> None:
    result = _evaluate(policy_inputs, eval_id)

    assert result.decision_state is EvidenceDecisionState.MISSING_CRITICAL_FACTS
    assert set(result.missing_critical_facts) == expected_missing
    assert result.candidate_procedure_ids == ()


def test_conflict_has_no_preferred_procedure(policy_inputs) -> None:
    result = _evaluate(policy_inputs, "EVAL-011")

    assert result.decision_state is EvidenceDecisionState.EVIDENCE_FOUND_WITH_CONFLICT
    assert {"INC-003", "INC-011"}.issubset(result.retained_precedent_ids)
    assert result.candidate_procedure_ids == ()
    assert set(result.missing_critical_facts) == {
        RequiredVerificationFact.CONSUMER_ERROR_RATE,
        RequiredVerificationFact.DATABASE_CONNECTION_POOL_UTILIZATION,
    }


def test_connection_pool_rejects_context_only_support_when_direct_signals_are_contradicted(
    policy_inputs,
) -> None:
    """Active connections cannot override two contradictory direct pool signals."""
    incidents, procedures, _ = policy_inputs
    from incident_precedent_harness.domain.incident_data import EvalCase

    case = EvalCase.model_validate(
        {
            "eval_id": "EVAL-099",
            "split": "calibration",
            "input_summary": "Workflow writes slowed after a migration window.",
            "expected_decision_state": "evidence_found",
            "acceptable_precedent_ids": ["INC-005"],
            "unsafe_precedent_ids": ["INC-009"],
            "expected_candidate_procedure_ids": ["RB-002"],
            "expected_missing_facts": [],
            "failure_label_intent": ["connection_pool_context_only_rejected"],
            "acceptance_reason": "Direct pool contradictions must block a false conflict.",
            "observed_facts": [
                {"fact": "migration_lock_waits", "status": "confirmed"},
                {"fact": "active_database_connections", "status": "confirmed"},
                {"fact": "database_connection_pool_utilization", "status": "contradicted"},
                {"fact": "database_connection_acquire_latency", "status": "contradicted"},
                {"fact": "queue_depth", "status": "confirmed"},
                {"fact": "consumer_error_rate", "status": "contradicted"},
                {"fact": "worker_deployment_version", "status": "contradicted"},
                {"fact": "error_rate_by_component", "status": "confirmed"},
            ],
        }
    )

    from incident_precedent_harness.retrieval.models import KeywordCandidate

    result = AntiAnchoringDecisionPolicy().evaluate(
        intake=case,
        ranked_candidates=(
            KeywordCandidate(incident_id="INC-005", rank=1, score=10.0),
            KeywordCandidate(incident_id="INC-011", rank=2, score=9.0),
            KeywordCandidate(incident_id="INC-009", rank=3, score=8.0),
        ),
        incidents=incidents,
        procedures=procedures,
    )

    assert result.decision_state is EvidenceDecisionState.EVIDENCE_FOUND
    assert result.retained_precedent_ids == ("INC-005",)
    assert result.candidate_procedure_ids == ("RB-002",)
    connection_pool_assessments = [
        assessment
        for assessment in result.assessments
        if assessment.incident_family.value == "connection_pool_exhaustion"
    ]
    assert connection_pool_assessments
    assert all(not assessment.retained for assessment in connection_pool_assessments)
    assert all(
        set(assessment.contradicted_facts)
        == {
            RequiredVerificationFact.DATABASE_CONNECTION_POOL_UTILIZATION,
            RequiredVerificationFact.DATABASE_CONNECTION_ACQUIRE_LATENCY,
        }
        for assessment in connection_pool_assessments
    )


def test_connection_pool_unknown_direct_signals_remain_missing_fact_evidence(policy_inputs) -> None:
    """Unknown direct signals preserve the existing incomplete-evidence behavior."""
    result = _evaluate(policy_inputs, "EVAL-010")

    assert result.decision_state is EvidenceDecisionState.MISSING_CRITICAL_FACTS
    assert result.retained_precedent_ids == ("INC-010",)
    assert result.candidate_procedure_ids == ()
