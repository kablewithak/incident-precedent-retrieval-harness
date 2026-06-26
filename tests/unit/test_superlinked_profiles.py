from incident_precedent_harness.domain.enums import ProviderOperation
from incident_precedent_harness.inference.profiles import (
    LOCAL_SIE_EMBEDDING_MODEL_ID,
    LOCAL_SIE_RERANK_MODEL_ID,
    build_local_sie_embedding_profile,
    build_local_sie_rerank_profile,
)


def test_local_embedding_profile_is_explicit_and_no_retry() -> None:
    profile = build_local_sie_embedding_profile(timeout_ms=30_000)

    assert profile.operation is ProviderOperation.ENCODE
    assert profile.model_id == LOCAL_SIE_EMBEDDING_MODEL_ID
    assert profile.max_retries == 0


def test_local_rerank_profile_is_explicit_and_no_retry() -> None:
    profile = build_local_sie_rerank_profile(timeout_ms=30_000)

    assert profile.operation is ProviderOperation.SCORE
    assert profile.model_id == LOCAL_SIE_RERANK_MODEL_ID
    assert profile.max_retries == 0
