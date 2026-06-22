from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from incident_precedent_harness.domain.enums import ProviderFailureCode, ProviderOperation
from incident_precedent_harness.inference.errors import SemanticInferenceError
from incident_precedent_harness.inference.fake_client import FakeSemanticInferenceClient
from incident_precedent_harness.inference.models import (
    CandidateScoringRequest,
    EmbeddingRequest,
    IncidentExtractionRequest,
    InferenceProfile,
    TextItem,
)


def build_profile(operation: ProviderOperation) -> InferenceProfile:
    return InferenceProfile(
        profile_id=f"fake-{operation.value}-v1",
        provider_name="fake",
        operation=operation,
        model_id="deterministic-test-double",
        timeout_ms=100,
        max_retries=0,
    )


def test_fake_client_extracts_only_allowed_deterministic_signals() -> None:
    client = FakeSemanticInferenceClient()
    response = client.extract_incident_signals(
        IncidentExtractionRequest(
            trace_id=uuid4(),
            profile=build_profile(ProviderOperation.EXTRACT),
            item=TextItem(
                item_id="intake-1",
                text="Queue backlog began after a worker deploy.",
            ),
            labels=("change_context", "symptom", "component"),
        )
    )

    assert [(signal.label, signal.value) for signal in response.signals] == [
        ("change_context", "deployment"),
        ("symptom", "queue_backlog"),
        ("component", "background_worker"),
    ]
    assert response.latency_ms == 0


def test_fake_client_embeddings_are_deterministic_and_normalized() -> None:
    client = FakeSemanticInferenceClient(embedding_dimensions=8)
    request = EmbeddingRequest(
        trace_id=uuid4(),
        profile=build_profile(ProviderOperation.ENCODE),
        items=(TextItem(item_id="incident-1", text="queue backlog after deployment"),),
    )

    first = client.encode_incident_texts(request)
    second = client.encode_incident_texts(request)

    assert first.vectors == second.vectors
    assert len(first.vectors[0].dense_values) == 8
    magnitude = sum(value * value for value in first.vectors[0].dense_values)
    assert magnitude == pytest.approx(1.0)


def test_fake_client_scores_lexical_overlap_with_stable_ranking() -> None:
    client = FakeSemanticInferenceClient()
    response = client.score_incident_candidates(
        CandidateScoringRequest(
            trace_id=uuid4(),
            profile=build_profile(ProviderOperation.SCORE),
            query=TextItem(item_id="query", text="queue backlog after deployment"),
            candidates=(
                TextItem(item_id="INC-001", text="cache stampede caused latency"),
                TextItem(item_id="INC-002", text="deployment triggered worker queue backlog"),
            ),
        )
    )

    assert [score.candidate_id for score in response.scores] == ["INC-002", "INC-001"]
    assert [score.rank for score in response.scores] == [1, 2]
    assert response.scores[0].score > response.scores[1].score


def test_fake_client_failure_is_a_typed_safe_envelope() -> None:
    client = FakeSemanticInferenceClient(fail_operations=(ProviderOperation.ENCODE,))
    request = EmbeddingRequest(
        trace_id=uuid4(),
        profile=build_profile(ProviderOperation.ENCODE),
        items=(TextItem(item_id="incident-1", text="safe synthetic text"),),
    )

    with pytest.raises(SemanticInferenceError) as error:
        client.encode_incident_texts(request)

    assert error.value.failure.code is ProviderFailureCode.PROVIDER_UNAVAILABLE
    assert error.value.failure.operation is ProviderOperation.ENCODE
    assert error.value.failure.safe_message == "Configured fake provider failure."


def test_request_rejects_profile_for_the_wrong_operation() -> None:
    with pytest.raises(ValidationError, match="embedding requires an encode profile"):
        EmbeddingRequest(
            trace_id=uuid4(),
            profile=build_profile(ProviderOperation.SCORE),
            items=(TextItem(item_id="incident-1", text="safe synthetic text"),),
        )
