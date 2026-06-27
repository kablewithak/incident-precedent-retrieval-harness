"""Policy-governed triage orchestration with advisory-only SIE dense evidence."""

from __future__ import annotations

from dataclasses import dataclass

from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.domain.incident_data import (
    CandidateInvestigationProcedure,
    HistoricalIncidentCard,
)
from incident_precedent_harness.inference.errors import SemanticInferenceError
from incident_precedent_harness.inference.models import EmbeddingRequest, InferenceProfile, TextItem
from incident_precedent_harness.inference.protocol import SemanticInferenceClient
from incident_precedent_harness.ingestion.sensitive_content import find_sensitive_content
from incident_precedent_harness.retrieval.dense import DenseRetriever
from incident_precedent_harness.retrieval.keyword import KeywordRetriever
from incident_precedent_harness.triage.models import (
    SemanticAdvisory,
    SemanticAdvisoryCandidate,
    SemanticAdvisoryStatus,
    TriageEvidencePacket,
    TriageRequest,
)


class TriageContractError(ValueError):
    """Raised when typed local orchestration contracts cannot be satisfied."""


class TriageInputRejectedError(ValueError):
    """Raised before provider invocation when runtime input fails safe handling rules."""

    def __init__(self, finding_codes: tuple[str, ...]) -> None:
        super().__init__("runtime input contains disallowed sensitive-content indicators")
        self.finding_codes = finding_codes


@dataclass(frozen=True, slots=True)
class TriageService:
    """Create non-executing packets from policy authority plus semantic advisory evidence.

    The active anti-anchoring policy receives only deterministic keyword candidates.
    Local-SIE dense retrieval is displayed as advisory evidence and is structurally
    unable to change the policy result in this slice.
    """

    incidents: tuple[HistoricalIncidentCard, ...]
    procedures: tuple[CandidateInvestigationProcedure, ...]
    dense_retriever: DenseRetriever
    semantic_client: SemanticInferenceClient
    embedding_profile: InferenceProfile
    policy: AntiAnchoringDecisionPolicy
    policy_top_k: int = 5
    semantic_top_k: int = 5

    def __post_init__(self) -> None:
        if not 1 <= self.policy_top_k <= 5:
            raise TriageContractError("policy_top_k must be between 1 and 5")
        if not 1 <= self.semantic_top_k <= 5:
            raise TriageContractError("semantic_top_k must be between 1 and 5")
        if self.embedding_profile.operation.value != "encode":
            raise TriageContractError("triage semantic advisory requires an encode profile")

    def triage(self, request: TriageRequest) -> TriageEvidencePacket:
        """Return a typed packet without procedure execution authority."""

        self._reject_sensitive_runtime_input(request)
        keyword_candidates = KeywordRetriever(self.incidents).rank(
            request.input_summary,
            top_k=self.policy_top_k,
        )

        if not request.provider_available:
            policy_result = self.policy.evaluate(
                intake=request,
                ranked_candidates=keyword_candidates,
                incidents=self.incidents,
                procedures=self.procedures,
            )
            return self._packet(
                request=request,
                policy_result=policy_result,
                semantic_advisory=SemanticAdvisory(
                    status=SemanticAdvisoryStatus.PROVIDER_DEGRADED,
                    profile_id=self.embedding_profile.profile_id,
                    candidate_evidence=(),
                    safe_reason="Input declared the required semantic provider unavailable.",
                ),
            )

        try:
            semantic_advisory = self._semantic_advisory(request)
        except SemanticInferenceError as error:
            degraded_request = request.model_copy(update={"provider_available": False})
            policy_result = self.policy.evaluate(
                intake=degraded_request,
                ranked_candidates=keyword_candidates,
                incidents=self.incidents,
                procedures=self.procedures,
            )
            return self._packet(
                request=request,
                policy_result=policy_result,
                semantic_advisory=SemanticAdvisory(
                    status=SemanticAdvisoryStatus.PROVIDER_DEGRADED,
                    profile_id=self.embedding_profile.profile_id,
                    candidate_evidence=(),
                    provider_failure=error.failure,
                ),
            )

        policy_result = self.policy.evaluate(
            intake=request,
            ranked_candidates=keyword_candidates,
            incidents=self.incidents,
            procedures=self.procedures,
        )
        return self._packet(
            request=request,
            policy_result=policy_result,
            semantic_advisory=semantic_advisory,
        )

    def _semantic_advisory(self, request: TriageRequest) -> SemanticAdvisory:
        response = self.semantic_client.encode_incident_texts(
            EmbeddingRequest(
                trace_id=request.trace_id,
                profile=self.embedding_profile,
                items=(TextItem(item_id=str(request.request_id), text=request.input_summary),),
            )
        )
        if response.profile_id != self.embedding_profile.profile_id:
            raise TriageContractError("semantic advisory response profile did not match request profile")
        vectors = {vector.item_id: vector.dense_values for vector in response.vectors}
        request_key = str(request.request_id)
        if set(vectors) != {request_key}:
            raise TriageContractError("semantic advisory response did not match the triage request identity")
        candidates = self.dense_retriever.rank(
            vectors[request_key],
            top_k=self.semantic_top_k,
        )
        return SemanticAdvisory(
            status=SemanticAdvisoryStatus.AVAILABLE,
            profile_id=self.embedding_profile.profile_id,
            candidate_evidence=tuple(
                SemanticAdvisoryCandidate(
                    incident_id=candidate.incident_id,
                    rank=candidate.rank,
                    cosine_similarity=candidate.cosine_similarity,
                )
                for candidate in candidates
            ),
            query_embedding_latency_ms=response.latency_ms,
        )

    @staticmethod
    def _reject_sensitive_runtime_input(request: TriageRequest) -> None:
        findings = find_sensitive_content(
            title="runtime-triage",
            summary=request.input_summary,
            source_reference="runtime-triage",
        )
        if findings:
            codes = tuple(sorted({finding.code.value for finding in findings}))
            raise TriageInputRejectedError(codes)

    @staticmethod
    def _packet(*, request: TriageRequest, policy_result, semantic_advisory: SemanticAdvisory) -> TriageEvidencePacket:  # type: ignore[no-untyped-def]
        return TriageEvidencePacket(
            request_id=request.request_id,
            trace_id=request.trace_id,
            policy_decision=policy_result,
            semantic_advisory=semantic_advisory,
            non_claims=(
                "Semantic candidate evidence is advisory and cannot alter the active anti-anchoring policy decision.",
                "Historical precedent is not a diagnosis, root-cause determination, or remediation instruction.",
                "Candidate procedure IDs, when present, remain human-review material; this packet never authorizes execution.",
                "This local synthetic-data path does not establish production readiness or customer-data validation.",
            ),
        )
