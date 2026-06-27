"""Tests for the typed triage packet boundary."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from incident_precedent_harness.decisions import AntiAnchoringDecisionPolicy
from incident_precedent_harness.domain.enums import ProviderOperation
from incident_precedent_harness.inference.fake_client import FakeSemanticInferenceClient
from incident_precedent_harness.inference.models import InferenceProfile
from incident_precedent_harness.retrieval.dense import DenseRetriever, build_local_dense_index
from incident_precedent_harness.retrieval.keyword import KeywordRetriever
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository
from incident_precedent_harness.triage.models import SemanticAdvisoryStatus, TriageRequest
from incident_precedent_harness.triage.service import TriageInputRejectedError, TriageService

ROOT = Path(__file__).resolve().parents[2]


def _profile() -> InferenceProfile:
    return InferenceProfile(
        profile_id="fake-encode-v1",
        provider_name="fake",
        operation=ProviderOperation.ENCODE,
        model_id="deterministic-test-double",
        timeout_ms=100,
        max_retries=0,
    )


def _service(*, client: FakeSemanticInferenceClient) -> TriageService:
    repository = JsonDatasetRepository(ROOT)
    incidents = repository.load_incidents()
    index = build_local_dense_index(
        incidents=incidents,
        client=client,
        embedding_profile=_profile(),
        trace_id=uuid4(),
        index_id="test-triage-index",
    )
    return TriageService(
        incidents=incidents,
        procedures=repository.load_procedures(),
        dense_retriever=DenseRetriever(index=index, incidents=incidents),
        semantic_client=client,
        embedding_profile=_profile(),
        policy=AntiAnchoringDecisionPolicy(),
    )


def _request_from_case(case, *, provider_available: bool | None = None) -> TriageRequest:  # type: ignore[no-untyped-def]
    return TriageRequest(
        request_id=uuid4(),
        trace_id=uuid4(),
        input_summary=case.input_summary,
        observed_facts=case.observed_facts,
        provider_available=case.provider_available if provider_available is None else provider_available,
    )


def test_triage_packet_keeps_policy_authority_separate_from_semantic_advisory() -> None:
    repository = JsonDatasetRepository(ROOT)
    case = next(item for item in repository.load_calibration_cases() if item.eval_id == "EVAL-001")
    client = FakeSemanticInferenceClient()
    service = _service(client=client)

    packet = service.triage(_request_from_case(case))
    expected_policy = AntiAnchoringDecisionPolicy().evaluate(
        intake=case,
        ranked_candidates=KeywordRetriever(repository.load_incidents()).rank(case.input_summary, top_k=5),
        incidents=repository.load_incidents(),
        procedures=repository.load_procedures(),
    )

    assert packet.policy_decision == expected_policy
    assert packet.semantic_advisory.status is SemanticAdvisoryStatus.AVAILABLE
    assert packet.semantic_advisory.candidate_evidence
    assert packet.procedure_execution_authorized is False
    assert packet.policy_decision.candidate_procedure_ids == ("RB-001",)


def test_triage_uses_provider_degraded_packet_when_encode_fails() -> None:
    repository = JsonDatasetRepository(ROOT)
    case = next(item for item in repository.load_calibration_cases() if item.eval_id == "EVAL-001")
    index_client = FakeSemanticInferenceClient()
    # Build the index separately so only the runtime encode call fails.
    incidents = repository.load_incidents()
    index = build_local_dense_index(
        incidents=incidents,
        client=index_client,
        embedding_profile=_profile(),
        trace_id=uuid4(),
        index_id="test-triage-index-failure",
    )
    service = TriageService(
        incidents=incidents,
        procedures=repository.load_procedures(),
        dense_retriever=DenseRetriever(index=index, incidents=incidents),
        semantic_client=FakeSemanticInferenceClient(fail_operations=(ProviderOperation.ENCODE,)),
        embedding_profile=_profile(),
        policy=AntiAnchoringDecisionPolicy(),
    )

    packet = service.triage(_request_from_case(case))

    assert packet.policy_decision.decision_state.value == "provider_degraded"
    assert packet.semantic_advisory.status is SemanticAdvisoryStatus.PROVIDER_DEGRADED
    assert packet.semantic_advisory.provider_failure is not None
    assert packet.semantic_advisory.candidate_evidence == ()
    assert packet.policy_decision.retained_precedent_ids == ()
    assert packet.policy_decision.candidate_procedure_ids == ()


def test_triage_does_not_invoke_provider_when_request_declares_unavailable() -> None:
    repository = JsonDatasetRepository(ROOT)
    case = next(item for item in repository.load_calibration_cases() if item.eval_id == "EVAL-004")
    service = _service(client=FakeSemanticInferenceClient())

    packet = service.triage(_request_from_case(case, provider_available=False))

    assert packet.policy_decision.decision_state.value == "provider_degraded"
    assert packet.semantic_advisory.status is SemanticAdvisoryStatus.PROVIDER_DEGRADED
    assert packet.semantic_advisory.provider_failure is None
    assert packet.semantic_advisory.safe_reason is not None
    assert packet.semantic_advisory.candidate_evidence == ()


def test_triage_rejects_sensitive_runtime_input_before_provider_call() -> None:
    service = _service(client=FakeSemanticInferenceClient())
    request = TriageRequest(
        request_id=uuid4(),
        trace_id=uuid4(),
        input_summary="queue backlog observed; api_key=super-secret-token",
    )

    with pytest.raises(TriageInputRejectedError) as error:
        service.triage(request)

    assert error.value.finding_codes == ("api_key_assignment",)
