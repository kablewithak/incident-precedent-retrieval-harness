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
