"""Safe local request boundary for the read-only submission demo.

This module accepts sanitized structured incident intake, creates request and
trace identifiers server-side, then delegates all decision behavior to the
existing ``TriageService``. It does not implement retrieval, policy, selection,
or procedure logic itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from incident_precedent_harness.domain.incident_data import (
    ObservedVerificationFact,
    RepresentativeSelectionIntake,
)
from incident_precedent_harness.triage.models import TriageEvidencePacket, TriageRequest
from incident_precedent_harness.triage.service import TriageInputRejectedError


class LocalDemoRequestError(ValueError):
    """A safe, browser-displayable local demo request refusal."""

    def __init__(self, failure_code: str, safe_message: str) -> None:
        super().__init__(safe_message)
        self.failure_code = failure_code
        self.safe_message = safe_message


class _TriageCallable(Protocol):
    """The narrow service contract required by the local demo transport."""

    def triage(self, request: TriageRequest) -> TriageEvidencePacket:
        """Return one typed, non-executing evidence packet."""


class LocalDemoPayload(BaseModel):
    """Browser payload deliberately limited to the typed triage boundary."""

    model_config = ConfigDict(extra="forbid")

    input_summary: str = Field(min_length=1, max_length=4_000)
    observed_facts: tuple[ObservedVerificationFact, ...] = ()
    provider_available: bool = True
    representative_selection_intake: RepresentativeSelectionIntake | None = None

    @field_validator("observed_facts")
    @classmethod
    def reject_duplicate_observed_facts(
        cls,
        value: tuple[ObservedVerificationFact, ...],
    ) -> tuple[ObservedVerificationFact, ...]:
        facts = [observation.fact for observation in value]
        if len(facts) != len(set(facts)):
            raise ValueError("observed_facts must not repeat a verification fact")
        return value


@dataclass(frozen=True, slots=True)
class LocalDemoApplication:
    """Map an allowed browser request into the existing typed triage service.

    The local surface intentionally has no persistence, authentication, upload,
    tenant, connector, or administration responsibilities. It emits only the
    typed packet serialisation already produced by the governed harness.
    """

    service: _TriageCallable

    def health_payload(self) -> dict[str, object]:
        """Return safe local-surface metadata without probing or exposing provider state."""

        return {
            "status": "ok",
            "surface_kind": "local_submission_demo",
            "corpus_mode": "synthetic_relayops",
            "provider_mode": "local_sie_configured",
            "procedure_execution_authorized": False,
            "persistence": "none",
        }

    def triage_payload(self, payload: Mapping[str, Any]) -> dict[str, object]:
        """Validate browser input and return a JSON-safe typed evidence packet."""

        if not isinstance(payload, Mapping):
            raise LocalDemoRequestError(
                "invalid_request",
                "The demo accepts one structured JSON incident intake.",
            )

        try:
            parsed = LocalDemoPayload.model_validate(dict(payload))
        except (ValidationError, TypeError):
            raise LocalDemoRequestError(
                "invalid_request",
                "The structured incident intake was invalid. Check the selected facts and fields.",
            ) from None

        request = TriageRequest(
            request_id=uuid4(),
            trace_id=uuid4(),
            input_summary=parsed.input_summary,
            observed_facts=parsed.observed_facts,
            provider_available=parsed.provider_available,
            representative_selection_intake=parsed.representative_selection_intake,
        )
        try:
            packet = self.service.triage(request)
        except TriageInputRejectedError:
            raise LocalDemoRequestError(
                "sensitive_input_rejected",
                "The summary contains content this local demo will not send to the provider.",
            ) from None
        except (ValueError, RuntimeError):
            raise LocalDemoRequestError(
                "triage_unavailable",
                "The local triage boundary could not produce a safe evidence packet.",
            ) from None

        return {
            "status": "ok",
            "packet": packet.model_dump(mode="json"),
            "runtime_boundary": "typed_triage_evidence_packet_v1",
        }
