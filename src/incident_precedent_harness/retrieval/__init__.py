"""Retrieval baselines, local dense indexing, and validated corpus access."""

from incident_precedent_harness.retrieval.dense import (
    DenseIndexError,
    DenseIndexStore,
    DenseRetriever,
    build_local_dense_index,
    validate_dense_index_against_corpus,
)
from incident_precedent_harness.retrieval.keyword import KeywordRetriever
from incident_precedent_harness.retrieval.models import (
    DenseCandidate,
    DenseRetrievalCalibrationReport,
    KeywordBaselineReport,
    KeywordCandidate,
    KeywordCaseOutcome,
    LocalDenseIndex,
)
from incident_precedent_harness.retrieval.repository import DatasetLoadError, JsonDatasetRepository

__all__ = [
    "DatasetLoadError",
    "DenseCandidate",
    "DenseIndexError",
    "DenseIndexStore",
    "DenseRetriever",
    "DenseRetrievalCalibrationReport",
    "JsonDatasetRepository",
    "KeywordBaselineReport",
    "KeywordCandidate",
    "KeywordCaseOutcome",
    "KeywordRetriever",
    "LocalDenseIndex",
    "build_local_dense_index",
    "validate_dense_index_against_corpus",
]
