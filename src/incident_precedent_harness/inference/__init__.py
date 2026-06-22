"""Provider-neutral semantic inference contracts and test doubles."""

from incident_precedent_harness.inference.fake_client import FakeSemanticInferenceClient
from incident_precedent_harness.inference.protocol import SemanticInferenceClient

__all__ = ["FakeSemanticInferenceClient", "SemanticInferenceClient"]
