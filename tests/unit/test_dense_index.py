"""Tests for provider-neutral local dense indexing and cosine retrieval."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from incident_precedent_harness.domain.enums import ProviderOperation
from incident_precedent_harness.inference.fake_client import FakeSemanticInferenceClient
from incident_precedent_harness.inference.models import EmbeddingRequest, InferenceProfile, TextItem
from incident_precedent_harness.retrieval import JsonDatasetRepository
from incident_precedent_harness.retrieval.dense import (
    DenseIndexError,
    DenseIndexStore,
    DenseRetriever,
    build_local_dense_index,
)
from incident_precedent_harness.retrieval.representation import (
    REPRESENTATION_VERSION,
    incident_retrieval_representation,
)

ROOT = Path(__file__).resolve().parents[2]


def _profile() -> InferenceProfile:
    return InferenceProfile(
        profile_id="fake-dense-index-v1",
        provider_name="fake",
        operation=ProviderOperation.ENCODE,
        model_id="deterministic-test-double",
        timeout_ms=100,
        max_retries=0,
    )


def _index():
    incidents = JsonDatasetRepository(ROOT).load_incidents()
    return incidents, build_local_dense_index(
        incidents=incidents,
        client=FakeSemanticInferenceClient(embedding_dimensions=8),
        embedding_profile=_profile(),
        trace_id=uuid4(),
    )


def test_builds_versioned_index_bound_to_the_current_approved_corpus() -> None:
    incidents, index = _index()

    assert index.manifest.index_format_version == "local-dense-index-v1"
    assert index.manifest.representation_version == REPRESENTATION_VERSION
    assert index.manifest.corpus_incident_count == len(incidents) == 12
    assert index.manifest.vector_dimension == 8
    assert [entry.incident_id for entry in index.entries] == [
        incident.incident_id for incident in incidents
    ]
    assert all(len(entry.representation_sha256) == 64 for entry in index.entries)


def test_representation_excludes_direct_identity_procedure_and_ground_truth_fields() -> None:
    incident = JsonDatasetRepository(ROOT).load_incidents()[0]

    representation = incident_retrieval_representation(incident)

    assert incident.incident_id not in representation
    assert "RB-001" not in representation
    assert incident.incident_family.value not in representation
    assert incident.failure_mechanism not in representation
    assert incident.narrative_safe in representation


def test_dense_retriever_is_deterministic_and_checks_query_dimension() -> None:
    incidents, index = _index()
    client = FakeSemanticInferenceClient(embedding_dimensions=8)
    retriever = DenseRetriever(index=index, incidents=incidents)
    query = client.encode_incident_texts(
        EmbeddingRequest(
            trace_id=uuid4(),
            profile=_profile(),
            items=(TextItem(item_id="query", text="queue backlog after deployment"),),
        )
    ).vectors[0].dense_values

    first = retriever.rank(query, top_k=5)
    second = retriever.rank(query, top_k=5)

    assert first == second
    assert [candidate.rank for candidate in first] == [1, 2, 3, 4, 5]
    assert [candidate.incident_id for candidate in first] == sorted(
        [candidate.incident_id for candidate in first],
        key=lambda incident_id: (-next(item.cosine_similarity for item in first if item.incident_id == incident_id), incident_id),
    )

    with pytest.raises(DenseIndexError, match="dimension"):
        retriever.rank((0.1, 0.2), top_k=5)


def test_dense_retriever_rejects_index_when_corpus_fingerprint_is_stale() -> None:
    incidents, index = _index()
    stale = index.model_copy(
        update={
            "manifest": index.manifest.model_copy(
                update={"corpus_fingerprint_sha256": "0" * 64}
            )
        }
    )

    with pytest.raises(DenseIndexError, match="fingerprint"):
        DenseRetriever(index=stale, incidents=incidents)


def test_dense_index_store_round_trips_without_raw_incident_text(tmp_path: Path) -> None:
    _, index = _index()
    index_path = tmp_path / "dense-index.json"

    DenseIndexStore.write(index, index_path)
    restored = DenseIndexStore.load(index_path)
    rendered = index_path.read_text(encoding="utf-8")

    assert restored == index
    assert "narrative_safe" not in rendered
    assert "historical_summary" not in rendered
