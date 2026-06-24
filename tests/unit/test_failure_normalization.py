from __future__ import annotations

from uuid import uuid4

from incident_precedent_harness.domain.enums import ProviderFailureCode, ProviderOperation
from incident_precedent_harness.inference.failure_normalization import (
    normalize_local_sie_failure,
)


def normalize(
    *,
    exception_type: str,
    message: str,
    retries_exhausted: bool = False,
):
    return normalize_local_sie_failure(
        trace_id=uuid4(),
        profile_id="local-extract-v1",
        operation=ProviderOperation.EXTRACT,
        exception_type=exception_type,
        message=message,
        retries_exhausted=retries_exhausted,
    )


def test_normalizes_transient_model_provisioning_as_model_not_ready() -> None:
    failure = normalize(
        exception_type="HTTPStatusError",
        message="503 Service Unavailable while model is loading",
    )

    assert failure.code is ProviderFailureCode.MODEL_NOT_READY
    assert failure.retryable is True
    assert failure.safe_message == "Local SIE model is still provisioning."


def test_normalizes_terminal_provisioning_timeout_as_retry_exhausted() -> None:
    failure = normalize(
        exception_type="ProvisioningError",
        message="Provision timeout (900.0s) exceeded before request could be sent",
        retries_exhausted=True,
    )

    assert failure.code is ProviderFailureCode.RETRY_EXHAUSTED
    assert failure.retryable is False
    assert failure.safe_message == (
        "Local SIE model did not become ready within the configured provisioning budget."
    )


def test_normalizes_generic_timeout_without_exposing_provider_message() -> None:
    failure = normalize(
        exception_type="TimeoutError",
        message="Read timeout after 30 seconds for internal provider request",
    )

    assert failure.code is ProviderFailureCode.PROVIDER_TIMEOUT
    assert failure.retryable is True
    assert "internal provider request" not in failure.safe_message


def test_normalizes_invalid_response_without_exposing_provider_message() -> None:
    failure = normalize(
        exception_type="ValueError",
        message="Malformed response payload with unexpected internal field",
    )

    assert failure.code is ProviderFailureCode.INVALID_PROVIDER_RESPONSE
    assert failure.retryable is False
    assert "unexpected internal field" not in failure.safe_message
