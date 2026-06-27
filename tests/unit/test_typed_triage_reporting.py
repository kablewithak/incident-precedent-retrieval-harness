"""Tests for calibration-only typed triage reporting."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from incident_precedent_harness.decisions import AntiAnchoringDecisionPolicy
from incident_precedent_harness.domain.enums import ProviderOperation
from incident_precedent_harness.inference.fake_client import FakeSemanticInferenceClient
from incident_precedent_harness.inference.models import InferenceProfile
from incident_precedent_harness.retrieval.dense import DenseRetriever, build_local_dense_index
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository
from incident_precedent_harness.triage.reporting import (
    run_typed_triage_calibration,
    write_typed_triage_report,
)
from incident_precedent_harness.triage.service import TriageService

ROOT = Path(__file__).resolve().parents[2]


def _service() -> TriageService:
    repository = JsonDatasetRepository(ROOT)
    incidents = repository.load_incidents()
    client = FakeSemanticInferenceClient()
    profile = InferenceProfile(
        profile_id="fake-encode-v1",
        provider_name="fake",
        operation=ProviderOperation.ENCODE,
        model_id="deterministic-test-double",
        timeout_ms=100,
        max_retries=0,
    )
    index = build_local_dense_index(
        incidents=incidents,
        client=client,
        embedding_profile=profile,
        trace_id=uuid4(),
        index_id="test-triage-report-index",
    )
    return TriageService(
        incidents=incidents,
        procedures=repository.load_procedures(),
        dense_retriever=DenseRetriever(index=index, incidents=incidents),
        semantic_client=client,
        embedding_profile=profile,
        policy=AntiAnchoringDecisionPolicy(),
    )


def test_typed_triage_calibration_preserves_policy_state_and_never_authorizes_execution(tmp_path: Path) -> None:
    repository = JsonDatasetRepository(ROOT)
    report = run_typed_triage_calibration(
        service=_service(),
        cases=repository.load_calibration_cases(),
    )

    assert report.status == "passed"
    assert report.metrics.decision_state_match_rate == 1.0
    assert report.metrics.procedure_execution_authorized_count == 0
    assert report.metrics.provider_degraded_packet_count == 1

    json_path = tmp_path / "triage.json"
    markdown_path = tmp_path / "triage.md"
    write_typed_triage_report(report, json_path=json_path, markdown_path=markdown_path)

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Procedure execution authorized | 0" in markdown
    assert "held-out cases" in markdown
    assert all(ord(character) < 128 for character in markdown)
