"""Safe local-SIE failure normalization.

Only the concrete provider adapter should call this module. It accepts exception
metadata already available at that boundary and returns the project's typed,
trace-safe ProviderFailure contract. Raw provider payloads are deliberately not
stored or returned.
"""

from __future__ import annotations

from uuid import UUID

from incident_precedent_harness.domain.enums import ProviderFailureCode, ProviderOperation
from incident_precedent_harness.inference.models import ProviderFailure


_MODEL_NOT_READY_MARKERS = (
    "provision timeout",
    "model load timeout",
    "model not ready",
    "model_not_ready",
    "503 service unavailable",
    "background model load",
)
_PROVIDER_TIMEOUT_MARKERS = (
    "request timeout",
    "read timeout",
    "connect timeout",
    "timed out",
)
_PROVIDER_UNAVAILABLE_MARKERS = (
    "connection refused",
    "connection reset",
    "could not connect",
    "server disconnected",
    "service unavailable",
)
_INVALID_RESPONSE_MARKERS = (
    "invalid response",
    "malformed response",
    "decode error",
    "validation error",
)


def normalize_local_sie_failure(
    *,
    trace_id: UUID,
    profile_id: str,
    operation: ProviderOperation,
    exception_type: str,
    message: str,
    retries_exhausted: bool = False,
) -> ProviderFailure:
    """Convert known local-SIE failures into a safe typed failure envelope.

    ``retries_exhausted`` is supplied by the adapter's bounded retry controller.
    It distinguishes a transient model-provisioning response from the terminal
    outcome after the allowed provisioning budget has been consumed.
    """
    normalized = f"{exception_type} {message}".casefold()

    if _contains_any(normalized, _MODEL_NOT_READY_MARKERS):
        if retries_exhausted:
            return _failure(
                trace_id=trace_id,
                profile_id=profile_id,
                operation=operation,
                code=ProviderFailureCode.RETRY_EXHAUSTED,
                safe_message=(
                    "Local SIE model did not become ready within the configured "
                    "provisioning budget."
                ),
                retryable=False,
            )
        return _failure(
            trace_id=trace_id,
            profile_id=profile_id,
            operation=operation,
            code=ProviderFailureCode.MODEL_NOT_READY,
            safe_message="Local SIE model is still provisioning.",
            retryable=True,
        )

    if _contains_any(normalized, _INVALID_RESPONSE_MARKERS):
        return _failure(
            trace_id=trace_id,
            profile_id=profile_id,
            operation=operation,
            code=ProviderFailureCode.INVALID_PROVIDER_RESPONSE,
            safe_message="Local SIE returned a response that could not be validated.",
            retryable=False,
        )

    if _contains_any(normalized, _PROVIDER_TIMEOUT_MARKERS):
        return _failure(
            trace_id=trace_id,
            profile_id=profile_id,
            operation=operation,
            code=ProviderFailureCode.PROVIDER_TIMEOUT,
            safe_message="Local SIE request exceeded its configured timeout.",
            retryable=True,
        )

    if _contains_any(normalized, _PROVIDER_UNAVAILABLE_MARKERS):
        return _failure(
            trace_id=trace_id,
            profile_id=profile_id,
            operation=operation,
            code=ProviderFailureCode.PROVIDER_UNAVAILABLE,
            safe_message="Local SIE was unavailable before a validated response was received.",
            retryable=True,
        )

    return _failure(
        trace_id=trace_id,
        profile_id=profile_id,
        operation=operation,
        code=ProviderFailureCode.PROVIDER_UNAVAILABLE,
        safe_message="Local SIE request failed before a validated response was received.",
        retryable=False,
    )


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    return any(marker in value for marker in markers)


def _failure(
    *,
    trace_id: UUID,
    profile_id: str,
    operation: ProviderOperation,
    code: ProviderFailureCode,
    safe_message: str,
    retryable: bool,
) -> ProviderFailure:
    return ProviderFailure(
        trace_id=trace_id,
        profile_id=profile_id,
        operation=operation,
        code=code,
        safe_message=safe_message,
        retryable=retryable,
    )
