"""Versioned local dense indexing and cosine retrieval.

This module is provider-neutral. It consumes validated application embedding
responses and never imports the SIE SDK or provider-specific response types.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import UUID

from pydantic import ValidationError

from incident_precedent_harness.domain.incident_data import HistoricalIncidentCard
from incident_precedent_harness.inference.models import EmbeddingRequest, InferenceProfile, TextItem
from incident_precedent_harness.inference.protocol import SemanticInferenceClient
from incident_precedent_harness.retrieval.models import (
    DenseCandidate,
    DenseIndexEntry,
    DenseIndexManifest,
    LocalDenseIndex,
)
from incident_precedent_harness.retrieval.representation import (
    REPRESENTATION_VERSION,
    corpus_fingerprint_sha256,
    incident_retrieval_representation,
    representation_sha256,
)


class DenseIndexError(ValueError):
    """Raised when a generated local dense index cannot be trusted."""


class DenseIndexStore:
    """Safe JSON persistence for an explicitly versioned local dense index."""

    @staticmethod
    def write(index: LocalDenseIndex, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(index.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def load(path: Path) -> LocalDenseIndex:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except OSError as error:
            raise DenseIndexError(f"cannot read dense index artifact: {path}") from error
        except json.JSONDecodeError as error:
            raise DenseIndexError(f"invalid dense index JSON: {path}") from error
        try:
            return LocalDenseIndex.model_validate(raw)
        except ValidationError as error:
            raise DenseIndexError(f"invalid dense index contract: {path}") from error


def build_local_dense_index(
    *,
    incidents: tuple[HistoricalIncidentCard, ...],
    client: SemanticInferenceClient,
    embedding_profile: InferenceProfile,
    trace_id: UUID,
    index_id: str = "local-sie-dense-index-v1",
) -> LocalDenseIndex:
    """Encode approved corpus cards and bind their vectors to a corpus fingerprint."""

    if not incidents:
        raise DenseIndexError("cannot build a dense index without incident cards")
    if tuple(sorted(card.incident_id for card in incidents)) != tuple(
        card.incident_id for card in incidents
    ):
        raise DenseIndexError("incident cards must be sorted by incident ID before indexing")

    items = tuple(
        TextItem(
            item_id=card.incident_id,
            text=incident_retrieval_representation(card),
        )
        for card in incidents
    )
    response = client.encode_incident_texts(
        EmbeddingRequest(
            trace_id=trace_id,
            profile=embedding_profile,
            items=items,
        )
    )
    vector_by_id = {vector.item_id: vector for vector in response.vectors}
    expected_ids = tuple(item.item_id for item in items)
    if set(vector_by_id) != set(expected_ids) or len(vector_by_id) != len(expected_ids):
        raise DenseIndexError("embedding response item identities did not match the approved corpus")

    entries = tuple(
        DenseIndexEntry(
            incident_id=card.incident_id,
            representation_sha256=representation_sha256(
                incident_retrieval_representation(card)
            ),
            dense_values=vector_by_id[card.incident_id].dense_values,
        )
        for card in incidents
    )
    dimensions = {len(entry.dense_values) for entry in entries}
    if len(dimensions) != 1:
        raise DenseIndexError("approved corpus embeddings have inconsistent dimensions")

    return LocalDenseIndex(
        manifest=DenseIndexManifest(
            index_format_version="local-dense-index-v1",
            index_id=index_id,
            built_at=datetime.now(UTC),
            corpus_incident_count=len(incidents),
            corpus_fingerprint_sha256=corpus_fingerprint_sha256(incidents),
            representation_version=REPRESENTATION_VERSION,
            embedding_profile=embedding_profile,
            vector_dimension=next(iter(dimensions)),
        ),
        entries=entries,
    )


def validate_dense_index_against_corpus(
    *,
    index: LocalDenseIndex,
    incidents: tuple[HistoricalIncidentCard, ...],
) -> None:
    """Fail closed when an index no longer matches the current approved corpus."""

    if index.manifest.representation_version != REPRESENTATION_VERSION:
        raise DenseIndexError("dense index uses an unsupported representation version")
    if index.manifest.corpus_incident_count != len(incidents):
        raise DenseIndexError("dense index corpus count does not match the current corpus")
    if index.manifest.corpus_fingerprint_sha256 != corpus_fingerprint_sha256(incidents):
        raise DenseIndexError("dense index fingerprint does not match the current corpus")

    expected_hashes = {
        card.incident_id: representation_sha256(incident_retrieval_representation(card))
        for card in incidents
    }
    actual_hashes = {
        entry.incident_id: entry.representation_sha256 for entry in index.entries
    }
    if actual_hashes != expected_hashes:
        raise DenseIndexError("dense index representation hashes do not match the current corpus")


class DenseRetriever:
    """In-memory cosine retrieval over a validated local dense index."""

    algorithm_name = "cosine similarity over local SIE embeddings"

    def __init__(
        self,
        *,
        index: LocalDenseIndex,
        incidents: tuple[HistoricalIncidentCard, ...],
    ) -> None:
        validate_dense_index_against_corpus(index=index, incidents=incidents)
        self._index = index
        self._vectors = {
            entry.incident_id: entry.dense_values for entry in index.entries
        }
        self._incident_families_by_id = {
            card.incident_id: card.incident_family.value for card in incidents
        }

    @property
    def incident_families_by_id(self) -> dict[str, str]:
        """Return fixed incident-family metadata for report construction only."""

        return dict(self._incident_families_by_id)

    @property
    def index_manifest(self) -> DenseIndexManifest:
        """Return the validated immutable manifest bound to this retriever."""

        return self._index.manifest

    @property
    def vector_dimension(self) -> int:
        """Return the fixed index dimension after integrity validation."""

        return self._index.manifest.vector_dimension

    def rank(
        self,
        query_dense_values: tuple[float, ...],
        *,
        top_k: int = 5,
    ) -> tuple[DenseCandidate, ...]:
        """Rank an already-validated query vector by deterministic cosine similarity."""

        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        self._validate_query_vector(query_dense_values)
        scored = [
            (incident_id, _cosine_similarity(query_dense_values, vector))
            for incident_id, vector in self._vectors.items()
        ]
        ranked = sorted(scored, key=lambda item: (-item[1], item[0]))[:top_k]
        return tuple(
            DenseCandidate(
                incident_id=incident_id,
                rank=rank,
                cosine_similarity=round(score, 8),
            )
            for rank, (incident_id, score) in enumerate(ranked, start=1)
        )

    def rank_with_latency(
        self,
        query_dense_values: tuple[float, ...],
        *,
        top_k: int = 5,
    ) -> tuple[tuple[DenseCandidate, ...], float]:
        """Return candidates with local similarity-only elapsed time."""

        started = perf_counter()
        candidates = self.rank(query_dense_values, top_k=top_k)
        return candidates, round((perf_counter() - started) * 1000, 4)

    def _validate_query_vector(self, values: tuple[float, ...]) -> None:
        if len(values) != self.vector_dimension:
            raise DenseIndexError("query vector dimension does not match the dense index")
        if not all(math.isfinite(item) for item in values):
            raise DenseIndexError("query vector must contain finite values")
        if not any(item != 0.0 for item in values):
            raise DenseIndexError("query vector must not be all zero")


def _cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        raise DenseIndexError("cosine similarity requires non-zero vectors")
    return dot_product / (left_norm * right_norm)
