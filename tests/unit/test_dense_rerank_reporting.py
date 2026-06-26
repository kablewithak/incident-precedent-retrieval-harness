"""Tests for calibration-only dense-plus-rerank evidence."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from incident_precedent_harness.domain.enums import ProviderOperation
from incident_precedent_harness.inference.fake_client import FakeSemanticInferenceClient
from incident_precedent_harness.inference.models import InferenceProfile
from incident_precedent_harness.retrieval import JsonDatasetRepository
from incident_precedent_harness.retrieval.dense import DenseRetriever, build_local_dense_index
from incident_precedent_harness.retrieval.rerank_reporting import (
    run_dense_rerank_calibration,
    write_dense_rerank_report,
)

ROOT = Path(__file__).resolve().parents[2]


def _embedding_profile() -> InferenceProfile:
    return InferenceProfile(
        profile_id="fake-encode-v1",
        provider_name="fake",
        operation=ProviderOperation.ENCODE,
        model_id="deterministic-test-double",
        timeout_ms=100,
        max_retries=0,
    )


def _score_profile() -> InferenceProfile:
    return InferenceProfile(
        profile_id="fake-score-v1",
        provider_name="fake",
        operation=ProviderOperation.SCORE,
        model_id="deterministic-test-double",
        timeout_ms=100,
        max_retries=0,
    )


def _report():
    repository = JsonDatasetRepository(ROOT)
    incidents = repository.load_incidents()
    client = FakeSemanticInferenceClient(embedding_dimensions=8)
    index = build_local_dense_index(
        incidents=incidents,
        client=client,
        embedding_profile=_embedding_profile(),
        trace_id=uuid4(),
    )
    return run_dense_rerank_calibration(
        retriever=DenseRetriever(index=index, incidents=incidents),
        incidents=incidents,
        client=client,
        embedding_profile=_embedding_profile(),
        score_profile=_score_profile(),
        cases=repository.load_calibration_cases(),
        trace_id=uuid4(),
        top_k=5,
    )


def test_dense_rerank_calibration_is_scoped_and_preserves_the_dense_candidate_set() -> None:
    report = _report()

    assert report.report_kind == "local_sie_dense_rerank_calibration"
    assert report.calibration_case_count == 12
    assert report.dense_top_k == 5
    assert report.dense_metrics.scored_case_count == 12
    assert report.rerank_metrics.scored_case_count == 12
    assert report.keyword_baseline_metrics.scored_case_count == 12
    assert all(
        set(outcome.reranked_candidate_ids) == set(outcome.dense_candidate_ids)
        for outcome in report.outcomes
    )
    assert any("held-out cases are not loaded" in limit for limit in report.known_limits)
    assert any("cannot introduce a new incident card" in limit for limit in report.known_limits)


def test_dense_rerank_calibration_writes_three_way_portable_evidence(tmp_path: Path) -> None:
    report = _report()
    json_path = tmp_path / "rerank.json"
    markdown_path = tmp_path / "rerank.md"

    write_dense_rerank_report(report, json_path=json_path, markdown_path=markdown_path)

    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    rendered = markdown_path.read_text(encoding="utf-8")
    assert parsed["report_kind"] == "local_sie_dense_rerank_calibration"
    assert "# Local SIE Dense + Score Rerank Calibration Report" in rendered
    assert "Dense + SIE score" in rendered
    assert "cannot add an incident card absent from dense top-k" in rendered
    assert "does not promote any retrieval path" in rendered
    assert "held-out cases" in rendered
    assert "N/A" in rendered
    assert "—" not in rendered
    assert rendered.isascii()
