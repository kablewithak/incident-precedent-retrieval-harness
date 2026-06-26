from __future__ import annotations

from uuid import uuid4

import pytest

from incident_precedent_harness.domain.enums import ProviderFailureCode, ProviderOperation
from incident_precedent_harness.inference.errors import SemanticInferenceError
from incident_precedent_harness.inference.models import (
    CandidateScoringRequest,
    EmbeddingRequest,
    InferenceProfile,
    TextItem,
)
from incident_precedent_harness.inference.superlinked_client import SuperlinkedSIEClient


class StubSIEClient:
    def __init__(self, *, encode_responses: list[object] | None = None, score_response: object | None = None, error: Exception | None = None) -> None:
        self.encode_responses = list(encode_responses or [])
        self.score_response = score_response
        self.error = error
        self.encode_calls: list[tuple[str, object]] = []
        self.score_calls: list[tuple[str, object, list[object]]] = []

    def encode(self, model_id: str, item: object) -> object:
        self.encode_calls.append((model_id, item))
        if self.error:
            raise self.error
        return self.encode_responses.pop(0)

    def score(self, model_id: str, query: object, candidates: list[object]) -> object:
        self.score_calls.append((model_id, query, candidates))
        if self.error:
            raise self.error
        return self.score_response



class ArrayLikeDenseVector:
    """Minimal NumPy-style stand-in that deliberately is not a Sequence."""

    def __init__(self, values: list[float]) -> None:
        self._values = values

    def tolist(self) -> list[float]:
        return list(self._values)

def item_factory(*, text: str) -> dict[str, str]:
    """Match the SDK Item contract: text is keyword-only."""
    return {"text": text}


def profile(operation: ProviderOperation, *, max_retries: int = 0) -> InferenceProfile:
    return InferenceProfile(
        profile_id=f"local-{operation.value}-v1",
        provider_name="superlinked_sie",
        operation=operation,
        model_id=f"model-{operation.value}",
        timeout_ms=30_000,
        max_retries=max_retries,
    )


def test_encode_validates_vectors_and_preserves_item_identity() -> None:
    client = SuperlinkedSIEClient(
        client=StubSIEClient(
            encode_responses=[{"dense": [0.1, 0.2]}, {"dense": [0.3, 0.4]}]
        ),
        item_factory=item_factory,
    )

    response = client.encode_incident_texts(
        EmbeddingRequest(
            trace_id=uuid4(),
            profile=profile(ProviderOperation.ENCODE),
            items=(
                TextItem(item_id="INC-001", text="safe synthetic one"),
                TextItem(item_id="INC-002", text="safe synthetic two"),
            ),
        )
    )

    assert [vector.item_id for vector in response.vectors] == ["INC-001", "INC-002"]
    assert response.vectors[0].dense_values == (0.1, 0.2)
    assert response.profile_id == "local-encode-v1"



def test_encode_accepts_array_like_dense_vectors_without_sdk_type_leakage() -> None:
    client = SuperlinkedSIEClient(
        client=StubSIEClient(
            encode_responses=[
                {"dense": ArrayLikeDenseVector([0.1, 0.2])},
                {"dense": ArrayLikeDenseVector([0.3, 0.4])},
            ]
        ),
        item_factory=item_factory,
    )

    response = client.encode_incident_texts(
        EmbeddingRequest(
            trace_id=uuid4(),
            profile=profile(ProviderOperation.ENCODE),
            items=(
                TextItem(item_id="INC-001", text="safe synthetic one"),
                TextItem(item_id="INC-002", text="safe synthetic two"),
            ),
        )
    )

    assert [vector.dense_values for vector in response.vectors] == [
        (0.1, 0.2),
        (0.3, 0.4),
    ]

def test_encode_rejects_inconsistent_dimensions_as_safe_provider_failure() -> None:
    client = SuperlinkedSIEClient(
        client=StubSIEClient(encode_responses=[{"dense": [0.1, 0.2]}, {"dense": [0.3]}]),
        item_factory=item_factory,
    )

    with pytest.raises(SemanticInferenceError) as error:
        client.encode_incident_texts(
            EmbeddingRequest(
                trace_id=uuid4(),
                profile=profile(ProviderOperation.ENCODE),
                items=(
                    TextItem(item_id="INC-001", text="safe synthetic one"),
                    TextItem(item_id="INC-002", text="safe synthetic two"),
                ),
            )
        )

    assert error.value.failure.code is ProviderFailureCode.INVALID_PROVIDER_RESPONSE
    assert "inconsistent" not in error.value.failure.safe_message.casefold()


def test_score_binds_entries_to_input_candidates_and_sorts_by_rank() -> None:
    client = SuperlinkedSIEClient(
        client=StubSIEClient(
            score_response={
                "scores": [
                    {"rank": 1, "score": -3.25},
                    {"rank": 0, "score": 4.75},
                ]
            }
        ),
        item_factory=item_factory,
    )

    response = client.score_incident_candidates(
        CandidateScoringRequest(
            trace_id=uuid4(),
            profile=profile(ProviderOperation.SCORE),
            query=TextItem(item_id="query", text="safe query"),
            candidates=(
                TextItem(item_id="INC-001", text="first candidate"),
                TextItem(item_id="INC-002", text="second candidate"),
            ),
        )
    )

    assert [(score.candidate_id, score.rank) for score in response.scores] == [
        ("INC-002", 1),
        ("INC-001", 2),
    ]
    assert [score.score for score in response.scores] == [4.75, -3.25]


def test_score_accepts_finite_raw_relevance_values_outside_probability_range() -> None:
    client = SuperlinkedSIEClient(
        client=StubSIEClient(
            score_response={
                "scores": [
                    {"rank": 0, "score": 2.5},
                    {"rank": 1, "score": -0.75},
                ]
            }
        ),
        item_factory=item_factory,
    )

    response = client.score_incident_candidates(
        CandidateScoringRequest(
            trace_id=uuid4(),
            profile=profile(ProviderOperation.SCORE),
            query=TextItem(item_id="query", text="safe query"),
            candidates=(
                TextItem(item_id="INC-001", text="first candidate"),
                TextItem(item_id="INC-002", text="second candidate"),
            ),
        )
    )

    assert [score.score for score in response.scores] == [2.5, -0.75]


def test_score_rejects_nonfinite_raw_relevance_values_as_safe_provider_failure() -> None:
    client = SuperlinkedSIEClient(
        client=StubSIEClient(
            score_response={
                "scores": [
                    {"rank": 0, "score": float("inf")},
                    {"rank": 1, "score": 0.0},
                ]
            }
        ),
        item_factory=item_factory,
    )

    with pytest.raises(SemanticInferenceError) as error:
        client.score_incident_candidates(
            CandidateScoringRequest(
                trace_id=uuid4(),
                profile=profile(ProviderOperation.SCORE),
                query=TextItem(item_id="query", text="safe query"),
                candidates=(
                    TextItem(item_id="INC-001", text="first candidate"),
                    TextItem(item_id="INC-002", text="second candidate"),
                ),
            )
        )

    assert error.value.failure.code is ProviderFailureCode.INVALID_PROVIDER_RESPONSE


def test_score_rejects_duplicate_ranks_as_safe_provider_failure() -> None:
    client = SuperlinkedSIEClient(
        client=StubSIEClient(score_response={"scores": [{"rank": 0, "score": 0.8}, {"rank": 0, "score": 0.2}]}),
        item_factory=item_factory,
    )

    with pytest.raises(SemanticInferenceError) as error:
        client.score_incident_candidates(
            CandidateScoringRequest(
                trace_id=uuid4(),
                profile=profile(ProviderOperation.SCORE),
                query=TextItem(item_id="query", text="safe query"),
                candidates=(
                    TextItem(item_id="INC-001", text="first candidate"),
                    TextItem(item_id="INC-002", text="second candidate"),
                ),
            )
        )

    assert error.value.failure.code is ProviderFailureCode.INVALID_PROVIDER_RESPONSE


def test_provider_exception_is_normalized_without_raw_message() -> None:
    client = SuperlinkedSIEClient(
        client=StubSIEClient(error=RuntimeError("Connection refused for internal-hostname.example")),
        item_factory=item_factory,
    )

    with pytest.raises(SemanticInferenceError) as error:
        client.encode_incident_texts(
            EmbeddingRequest(
                trace_id=uuid4(),
                profile=profile(ProviderOperation.ENCODE),
                items=(TextItem(item_id="INC-001", text="safe synthetic one"),),
            )
        )

    assert error.value.failure.code is ProviderFailureCode.PROVIDER_UNAVAILABLE
    assert "internal-hostname" not in error.value.failure.safe_message


def test_extract_is_explicitly_unsupported_for_submission_path() -> None:
    from incident_precedent_harness.inference.models import IncidentExtractionRequest

    client = SuperlinkedSIEClient(client=StubSIEClient(), item_factory=item_factory)

    with pytest.raises(SemanticInferenceError) as error:
        client.extract_incident_signals(
            IncidentExtractionRequest(
                trace_id=uuid4(),
                profile=profile(ProviderOperation.EXTRACT),
                item=TextItem(item_id="query", text="safe query"),
                labels=("service",),
            )
        )

    assert error.value.failure.code is ProviderFailureCode.UNSUPPORTED_CAPABILITY
