"""Stable enums shared by provider-neutral inference contracts."""

from enum import Enum


class ProviderOperation(str, Enum):
    """Supported semantic inference capabilities."""

    EXTRACT = "extract"
    ENCODE = "encode"
    SCORE = "score"


class ProviderFailureCode(str, Enum):
    """Normalized failures that may cross the provider boundary."""

    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_TIMEOUT = "provider_timeout"
    MODEL_NOT_READY = "model_not_ready"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    INVALID_PROVIDER_RESPONSE = "invalid_provider_response"
    INPUT_LIMIT_EXCEEDED = "input_limit_exceeded"
    RATE_LIMITED = "rate_limited"
    RETRY_EXHAUSTED = "retry_exhausted"
