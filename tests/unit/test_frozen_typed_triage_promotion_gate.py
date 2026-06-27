"""Tests for the frozen end-to-end typed-triage promotion gate."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.domain.enums import ProviderOperation
from incident_precedent_harness.evaluation.typed_triage_promotion import (
    TriagePromotionDecision,
    run_frozen_typed_triage_promotion_gate,
    write_frozen_typed_triage_promotion_report,
)
from incident_precedent_harness.inference.fake_client import FakeSemanticInferenceClient
from incident_precedent_harness.inference.models import InferenceProfile
from incident_precedent_harness.retrieval.dense import DenseRetriever, build_local_dense_index
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository
from incident_precedent_harness.triage.service import TriageService

ROOT = Path(__file__).resolve().parents[2]


def _profile() -> InferenceProfile:
    return InferenceProfile(
        profile_id="fake-frozen-gate-encode-v1",
        provider_name="fake",
        operation=ProviderOperation.ENCODE,
        model_id="deterministic-test-double",
        timeout_ms=100,
        max_retries=0,
    )


def _service(*, client: FakeSemanticInferenceClient) -> TriageService:
    repository = JsonDatasetRepository(ROOT)
    incidents = repository.load_incidents()
    index_client = FakeSemanticInferenceClient()
    index = build_local_dense_index(
        incidents=incidents,
        client=index_client,
        embedding_profile=_profile(),
        trace_id=uuid4(),
        index_id="test-frozen-typed-triage-index",
    )
    return TriageService(
        incidents=incidents,
        procedures=repository.load_procedures(),
        dense_retriever=DenseRetriever(index=index, incidents=incidents),
        semantic_client=client,
        embedding_profile=_profile(),
        policy=AntiAnchoringDecisionPolicy(),
    )


def _run(*, client: FakeSemanticInferenceClient):
    repository = JsonDatasetRepository(ROOT)
    return run_frozen_typed_triage_promotion_gate(
        repository_root=ROOT,
        service=_service(client=client),
        incidents=repository.load_incidents(),
        procedures=repository.load_procedures(),
        cases=repository.load_heldout_cases(),
    )


def test_frozen_typed_triage_gate_preserves_policy_authority_and_freeze_identity() -> None:
    report = _run(client=FakeSemanticInferenceClient())

    assert report.freeze_verification.verified is True
    assert report.freeze_verification.scope == "heldout_tranche_01"
    assert report.metrics.heldout_case_count == 12
    assert report.metrics.policy_baseline_parity_rate == 1.0
    assert report.metrics.procedure_execution_authorized_count == 0
    assert report.metrics.provider_degraded_safe_resolution_rate == 1.0
    assert all(
        outcome.policy_matches_baseline
        for outcome in report.outcomes
    )
    assert all(
        outcome.procedure_execution_authorized is False
        for outcome in report.outcomes
    )


def test_frozen_typed_triage_gate_blocks_when_underlying_policy_baseline_is_blocked() -> None:
    report = _run(client=FakeSemanticInferenceClient())

    assert report.baseline.promotion_status == "blocked"
    assert report.decision is TriagePromotionDecision.BLOCK
    assert any(
        "underlying frozen keyword-plus-policy baseline is blocked" in reason.casefold()
        for reason in report.decision_reasons
    )


def test_frozen_typed_triage_gate_blocks_when_semantic_provider_degrades_unexpectedly() -> None:
    report = _run(
        client=FakeSemanticInferenceClient(
            fail_operations=(ProviderOperation.ENCODE,),
        )
    )

    assert report.decision is TriagePromotionDecision.BLOCK
    assert report.metrics.unexpected_semantic_degraded_count > 0
    assert report.metrics.policy_baseline_parity_rate < 1.0
    assert report.metrics.procedure_execution_authorized_count == 0


def test_frozen_typed_triage_report_is_write_once(tmp_path: Path) -> None:
    report = _run(client=FakeSemanticInferenceClient())
    json_path = tmp_path / "evidence_vault" / "reports" / "gate.json"
    markdown_path = tmp_path / "docs" / "reports" / "gate.md"

    write_frozen_typed_triage_promotion_report(
        report,
        json_path=json_path,
        markdown_path=markdown_path,
    )

    assert json_path.is_file()
    assert markdown_path.is_file()
    assert "Decision:" in markdown_path.read_text(encoding="utf-8")
    assert "input_summary" not in json_path.read_text(encoding="utf-8")

    with pytest.raises(FileExistsError, match="will not be overwritten"):
        write_frozen_typed_triage_promotion_report(
            report,
            json_path=json_path,
            markdown_path=markdown_path,
        )
