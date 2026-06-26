from __future__ import annotations

import json
from pathlib import Path

from incident_precedent_harness.ingestion.inspection import inspect_import_batch
from incident_precedent_harness.ingestion.models import ImportFailureCode, SensitiveContentCode


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")


def record(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "import_record_id": "IMP-DEMO-001",
        "source_system": "relayops-demo-export",
        "source_record_id": "DEMO-QUEUE-001",
        "data_classification": "synthetic_demo",
        "title": "Worker backlog after deployment",
        "summary": "Synthetic summary prepared for controlled human review.",
        "occurred_on": "2026-01-18",
        "service": "workflow-service",
        "component": "webhook-worker",
        "change_context": "deployment",
        "symptom_labels": ["queue_backlog", "consumer_error_rate"],
        "source_reference": "relayops-demo://incident/DEMO-QUEUE-001",
    }
    values.update(overrides)
    return values


def test_clean_batch_is_ready_for_human_review_and_hashes_input(tmp_path: Path) -> None:
    batch = tmp_path / "clean.jsonl"
    write_jsonl(
        batch,
        [
            record(),
            record(
                import_record_id="IMP-DEMO-002",
                source_record_id="DEMO-POOL-001",
                title="Connection acquisition waits",
                summary="Synthetic second summary for controlled human review.",
                change_context="none",
                symptom_labels=["connection_acquire_latency"],
            ),
        ],
    )

    report = inspect_import_batch(input_path=batch, batch_id="relayops-demo-v1")

    assert report.ready_for_human_review is True
    assert report.accepted_record_count == 2
    assert report.rejected_record_count == 0
    assert len(report.input_sha256) == 64
    assert all(outcome.accepted_for_review for outcome in report.outputs)


def test_sensitive_summary_fails_closed_without_leaking_the_matched_value(tmp_path: Path) -> None:
    batch = tmp_path / "sensitive.jsonl"
    secret = "api_key=super-secret-value"
    write_jsonl(batch, [record(summary=f"Synthetic detail includes {secret}." )])

    report = inspect_import_batch(input_path=batch, batch_id="relayops-demo-v1")
    serialized = json.dumps(report.model_dump(mode="json"))

    assert report.ready_for_human_review is False
    assert report.outputs[0].failure_codes == (ImportFailureCode.SENSITIVE_CONTENT_DETECTED,)
    assert report.outputs[0].sensitive_findings[0].code is SensitiveContentCode.API_KEY_ASSIGNMENT
    assert secret not in serialized


def test_duplicate_identity_fails_closed(tmp_path: Path) -> None:
    batch = tmp_path / "duplicates.jsonl"
    write_jsonl(batch, [record(), record()])

    report = inspect_import_batch(input_path=batch, batch_id="relayops-demo-v1")

    assert report.ready_for_human_review is False
    assert report.outputs[0].accepted_for_review is True
    assert report.outputs[1].accepted_for_review is False
    assert set(report.outputs[1].failure_codes) == {
        ImportFailureCode.DUPLICATE_IMPORT_RECORD,
        ImportFailureCode.DUPLICATE_SOURCE_RECORD,
    }


def test_invalid_json_is_reported_without_echoing_raw_content(tmp_path: Path) -> None:
    batch = tmp_path / "invalid.jsonl"
    raw_line = '{"summary": "secret-should-not-echo",'
    batch.write_text(raw_line, encoding="utf-8")

    report = inspect_import_batch(input_path=batch, batch_id="relayops-demo-v1")
    serialized = json.dumps(report.model_dump(mode="json"))

    assert report.ready_for_human_review is False
    assert report.outputs[0].failure_codes == (ImportFailureCode.INVALID_JSON,)
    assert "secret-should-not-echo" not in serialized
