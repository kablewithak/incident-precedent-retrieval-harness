"""Tests for the local submission demo request boundary."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from incident_precedent_harness.decisions.models import PolicyDecisionResult
from incident_precedent_harness.demo.application import (
    LocalDemoApplication,
    LocalDemoRequestError,
)
from incident_precedent_harness.demo.local_demo_server import require_loopback_host
from incident_precedent_harness.domain.incident_enums import EvidenceDecisionState
from incident_precedent_harness.inference.models import ProviderFailure
from incident_precedent_harness.triage.models import (
    SemanticAdvisory,
    SemanticAdvisoryCandidate,
    SemanticAdvisoryStatus,
    TriageEvidencePacket,
    TriageRequest,
)
from incident_precedent_harness.triage.service import TriageInputRejectedError


@dataclass
class _StubService:
    request: TriageRequest | None = None
    reject_sensitive: bool = False

    def triage(self, request: TriageRequest) -> TriageEvidencePacket:
        self.request = request
        if self.reject_sensitive:
            raise TriageInputRejectedError(("api_key_assignment",))
        return TriageEvidencePacket(
            request_id=request.request_id,
            trace_id=request.trace_id,
            policy_decision=PolicyDecisionResult(
                decision_state=EvidenceDecisionState.EVIDENCE_FOUND,
                retained_precedent_ids=("INC-009",),
                candidate_procedure_ids=("RB-003",),
                assessments=(),
                safety_notes=("Synthetic local demo packet.",),
            ),
            semantic_advisory=SemanticAdvisory(
                status=SemanticAdvisoryStatus.AVAILABLE,
                profile_id="fake-encode-v1",
                candidate_evidence=(
                    SemanticAdvisoryCandidate(
                        incident_id="INC-009",
                        rank=1,
                        cosine_similarity=0.8,
                    ),
                ),
                query_embedding_latency_ms=1,
            ),
            non_claims=("Synthetic test packet.",),
        )


def test_local_demo_maps_safe_browser_payload_to_typed_request() -> None:
    service = _StubService()
    application = LocalDemoApplication(service=service)

    response = application.triage_payload(
        {
            "input_summary": "Database pool acquisition latency increased.",
            "observed_facts": [
                {
                    "fact": "database_connection_pool_utilization",
                    "status": "confirmed",
                }
            ],
            "provider_available": True,
            "representative_selection_intake": {
                "service": "payments-api",
                "component": "postgres-client-pool",
                "change_context": "none",
                "operational_signal_families": ["connection_pool_pressure"],
                "contradicted_signal_families": [],
            },
        }
    )

    assert response["status"] == "ok"
    assert response["runtime_boundary"] == "typed_triage_evidence_packet_v1"
    assert service.request is not None
    assert service.request.request_id
    assert service.request.trace_id
    assert service.request.representative_selection_intake is not None
    assert response["packet"]["procedure_execution_authorized"] is False  # type: ignore[index]


def test_local_demo_rejects_unknown_browser_fields() -> None:
    application = LocalDemoApplication(service=_StubService())

    with pytest.raises(LocalDemoRequestError) as error:
        application.triage_payload(
            {
                "input_summary": "Database pool acquisition latency increased.",
                "unexpected_runtime_outcome": "INC-009",
            }
        )

    assert error.value.failure_code == "invalid_request"
    assert "invalid" in error.value.safe_message.lower()


def test_local_demo_redacts_sensitive_input_refusal() -> None:
    application = LocalDemoApplication(service=_StubService(reject_sensitive=True))

    with pytest.raises(LocalDemoRequestError) as error:
        application.triage_payload(
            {"input_summary": "api_key=do-not-return-this-value"}
        )

    assert error.value.failure_code == "sensitive_input_rejected"
    assert "do-not-return-this-value" not in error.value.safe_message


def test_health_payload_never_claims_provider_availability() -> None:
    payload = LocalDemoApplication(service=_StubService()).health_payload()

    assert payload["provider_mode"] == "local_sie_configured"
    assert payload["procedure_execution_authorized"] is False
    assert payload["persistence"] == "none"
    assert "provider_available" not in payload


def test_loopback_host_guard_rejects_network_binds() -> None:
    assert require_loopback_host("127.0.0.1") == "127.0.0.1"
    assert require_loopback_host("localhost") == "localhost"

    with pytest.raises(ValueError, match="loopback"):
        require_loopback_host("0.0.0.0")
