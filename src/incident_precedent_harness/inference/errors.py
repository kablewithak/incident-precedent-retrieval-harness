"""Typed errors used at the provider boundary."""

from incident_precedent_harness.inference.models import ProviderFailure


class SemanticInferenceError(RuntimeError):
    """Exception carrying a validated, trace-safe provider failure envelope."""

    def __init__(self, failure: ProviderFailure) -> None:
        super().__init__(failure.safe_message)
        self.failure = failure
