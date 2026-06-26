"""Tests for calibration-only dense retrieval comparison evidence."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from incident_precedent_harness.domain.enums import ProviderOperation
from incident_precedent_harness.inference.fake_client import FakeSemanticInferenceClient
from incident_precedent_harness.inference.models import InferenceProfile
from incident_precedent_harness.retrieval import JsonDatasetRepository
from incident_precedent_harness.retrieval.dense import DenseRetriever, build_local_dense_index
from incident_precedent_harness.retrieval.dense_reporting import (
    run_dense_retrieval_calibration,
    write_dense_retrieval_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _profile() -> InferenceProfile:
    return InferenceProfile(
        profile_id="fake-dense-calibration-v1",
        provider_name="fake",
        operation=ProviderOperation.ENCODE,
        model_id="deterministic-test-double",
        timeout_ms=100,
        max_retries=0,
    )


def test_dense_calibration_is_scoped_to_calibration_and_compares_keyword() -> None:
    repository = JsonDatasetRepository(ROOT)
    incidents = repository.load_incidents()
    profile = _profile()
    client = FakeSemanticInferenceClient(embedding_dimensions=8)
    index = build_local_dense_index(
        incidents=incidents,
        client=client,
        embedding_profile=profile,
        trace_id=uuid4(),
    )
    report = run_dense_retrieval_calibration(
        retriever=DenseRetriever(index=index, incidents=incidents),
        incidents=incidents,
        client=client,
        embedding_profile=profile,
        cases=repository.load_calibration_cases(),
        trace_id=uuid4(),
        top_k=5,
    )

    assert report.report_kind == "local_sie_dense_retrieval_calibration"
    assert report.corpus_incident_count == 12
    assert report.calibration_case_count == 12
    assert len(report.outcomes) == 12
    assert report.metrics.scored_case_count == 12
    assert report.keyword_baseline_metrics.scored_case_count == 12
    assert report.index_manifest.embedding_profile.profile_id == "fake-dense-calibration-v1"
    assert all(outcome.eval_id.startswith("EVAL-0") for outcome in report.outcomes)
    assert any("held-out cases are not loaded" in limit for limit in report.known_limits)


def test_dense_calibration_writes_machine_and_reviewer_evidence(tmp_path: Path) -> None:
    repository = JsonDatasetRepository(ROOT)
    incidents = repository.load_incidents()
    profile = _profile()
    client = FakeSemanticInferenceClient(embedding_dimensions=8)
    index = build_local_dense_index(
        incidents=incidents,
        client=client,
        embedding_profile=profile,
        trace_id=uuid4(),
    )
    report = run_dense_retrieval_calibration(
        retriever=DenseRetriever(index=index, incidents=incidents),
        incidents=incidents,
        client=client,
        embedding_profile=profile,
        cases=repository.load_calibration_cases(),
        trace_id=uuid4(),
    )
    json_path = tmp_path / "dense.json"
    markdown_path = tmp_path / "dense.md"

    write_dense_retrieval_report(report, json_path=json_path, markdown_path=markdown_path)

    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    rendered = markdown_path.read_text(encoding="utf-8")
    assert parsed["report_kind"] == "local_sie_dense_retrieval_calibration"
    assert "# Local SIE Dense Retrieval Calibration Report" in rendered
    assert "## Calibration comparison" in rendered
    assert "## Calibration interpretation" in rendered
    assert "does not promote either retriever" in rendered
    assert "held-out cases" in rendered
