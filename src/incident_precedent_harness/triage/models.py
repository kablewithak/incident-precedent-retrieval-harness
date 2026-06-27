"""Typed contracts for advisory semantic evidence and policy-governed triage."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from incident_precedent_harness.decisions.models import PolicyDecisionResult
from incident_precedent_harness.domain.incident_data import (
    ObservedVerificationFact,
    RecordIdentifier,
)
from incident_precedent_harness.inference.models import ProviderFailure

SafeSummary = Annotated[str, Field(min_length=1, max_length=4_000)]


class SemanticAdvisoryStatus(str, Enum):
    """Whether semantic advisory retrieval was available for one request."""

    AVAILABLE = "available"
    PROVIDER_DEGRADED = "provider_degraded"


class SemanticAdvisoryCandidate(BaseModel):
    """A non-authoritative dense-retrieval candidate suitable for human review."""

    model_config = ConfigDict(extra="forbid")

    incident_id: RecordIdentifier
    rank: int = Field(ge=1, le=5)
    cosine_similarity: float = Field(ge=-1.000001, le=1.000001, allow_inf_nan=False)


class SemanticAdvisory(BaseModel):
    """Bounded semantic evidence kept separate from policy decision authority."""

    model_config = ConfigDict(extra="forbid")

    status: SemanticAdvisoryStatus
    profile_id: str | None = Field(default=None, min_length=1, max_length=128)
    candidate_evidence: tuple[SemanticAdvisoryCandidate, ...] = Field(max_length=5)
    query_embedding_latency_ms: int | None = Field(default=None, ge=0)
    provider_failure: ProviderFailure | None = None
    safe_reason: str | None = Field(default=None, min_length=1, max_length=300)

    @model_validator(mode="after")
    def validate_status_shape(self) -> "SemanticAdvisory":
        candidate_ids = [candidate.incident_id for candidate in self.candidate_evidence]
        ranks = [candidate.rank for candidate in self.candidate_evidence]
        if len(set(candidate_ids)) != len(candidate_ids):
            raise ValueError("semantic advisory candidate IDs must not repeat")
        if ranks and tuple(ranks) != tuple(range(1, len(ranks) + 1)):
            raise ValueError("semantic advisory ranks must be contiguous")

        if self.status is SemanticAdvisoryStatus.AVAILABLE:
            if not self.profile_id or not self.candidate_evidence:
                raise ValueError("available semantic advisory requires profile and candidates")
            if self.query_embedding_latency_ms is None:
                raise ValueError("available semantic advisory requires observed embedding latency")
            if self.provider_failure is not None or self.safe_reason is not None:
                raise ValueError("available semantic advisory cannot carry degradation details")
        else:
            if self.candidate_evidence or self.query_embedding_latency_ms is not None:
                raise ValueError("degraded semantic advisory cannot present candidate evidence")
            if self.profile_id is None:
                raise ValueError("degraded semantic advisory requires the requested profile ID")
            if (self.provider_failure is None) == (self.safe_reason is None):
                raise ValueError(
                    "degraded semantic advisory requires exactly one safe degradation explanation"
                )
        return self


class TriageRequest(BaseModel):
    """Sanitized structured intake accepted by the non-executing triage boundary."""

    model_config = ConfigDict(extra="forbid")

    request_id: UUID
    trace_id: UUID
    input_summary: SafeSummary
    observed_facts: tuple[ObservedVerificationFact, ...] = ()
    provider_available: bool = True

    @field_validator("observed_facts")
    @classmethod
    def reject_duplicate_observed_facts(
        cls,
        value: tuple[ObservedVerificationFact, ...],
    ) -> tuple[ObservedVerificationFact, ...]:
        facts = [observation.fact for observation in value]
        if len(set(facts)) != len(facts):
            raise ValueError("observed_facts must not repeat verification facts")
        return value


class TriageEvidencePacket(BaseModel):
    """User-facing packet with a policy result and advisory-only semantic evidence.

    The semantic advisory is deliberately separate from ``policy_decision``. The
    decision policy receives deterministic lexical candidates only in this slice,
    so semantic rank, score, and candidate order cannot alter decision state,
    retained precedent IDs, missing facts, or procedure eligibility.
    """

    model_config = ConfigDict(extra="forbid")

    packet_kind: Literal["typed_triage_evidence_packet_v1"] = "typed_triage_evidence_packet_v1"
    request_id: UUID
    trace_id: UUID
    policy_decision: PolicyDecisionResult
    semantic_advisory: SemanticAdvisory
    procedure_execution_authorized: Literal[False] = False
    non_claims: tuple[str, ...] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def enforce_non_execution_and_degraded_alignment(self) -> "TriageEvidencePacket":
        if self.procedure_execution_authorized is not False:
            raise ValueError("triage evidence packets never authorize procedure execution")
        if self.semantic_advisory.status is SemanticAdvisoryStatus.PROVIDER_DEGRADED:
            if self.policy_decision.decision_state.value != "provider_degraded":
                raise ValueError("semantic degradation must produce a provider_degraded policy decision")
            if self.policy_decision.retained_precedent_ids or self.policy_decision.candidate_procedure_ids:
                raise ValueError("provider-degraded packets cannot expose precedent or procedure candidates")
        return self
