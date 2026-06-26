"""Approved local SIE profiles for the structured-first submission path."""

from __future__ import annotations

from incident_precedent_harness.domain.enums import ProviderOperation
from incident_precedent_harness.inference.models import InferenceProfile

LOCAL_SIE_PROVIDER_NAME = "superlinked_sie"
LOCAL_SIE_EMBEDDING_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
LOCAL_SIE_RERANK_MODEL_ID = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def build_local_sie_embedding_profile(*, timeout_ms: int) -> InferenceProfile:
    """Return the approved local profile for dense incident representations."""
    return InferenceProfile(
        profile_id="local-sie-encode-v1",
        provider_name=LOCAL_SIE_PROVIDER_NAME,
        operation=ProviderOperation.ENCODE,
        model_id=LOCAL_SIE_EMBEDDING_MODEL_ID,
        timeout_ms=timeout_ms,
        max_retries=0,
    )


def build_local_sie_rerank_profile(*, timeout_ms: int) -> InferenceProfile:
    """Return the approved local profile for reranking a bounded candidate set."""
    return InferenceProfile(
        profile_id="local-sie-score-v1",
        provider_name=LOCAL_SIE_PROVIDER_NAME,
        operation=ProviderOperation.SCORE,
        model_id=LOCAL_SIE_RERANK_MODEL_ID,
        timeout_ms=timeout_ms,
        max_retries=0,
    )
