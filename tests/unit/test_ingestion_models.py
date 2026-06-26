from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from incident_precedent_harness.domain.incident_enums import ChangeContext
from incident_precedent_harness.ingestion.models import (
    ImportDataClassification,
    ImportLineOutcome,
    IncidentImportRecord,
)


def build_record(**overrides: object) -> IncidentImportRecord:
    values: dict[str, object] = {
        "import_record_id": "IMP-DEMO-001",
        "source_system": "relayops-demo-export",
        "source_record_id": "DEMO-QUEUE-001",
        "data_classification": ImportDataClassification.SYNTHETIC_DEMO,
        "title": "Worker backlog after deployment",
        "summary": "Synthetic summary prepared for controlled human review.",
        "occurred_on": date(2026, 1, 18),
        "service": "workflow-service",
        "component": "webhook-worker",
        "change_context": ChangeContext.DEPLOYMENT,
        "symptom_labels": ("queue_backlog", "consumer_error_rate"),
        "source_reference": "relayops-demo://incident/DEMO-QUEUE-001",
    }
    values.update(overrides)
    return IncidentImportRecord(**values)


def test_import_record_accepts_a_sanitized_demo_candidate() -> None:
    record = build_record()

    assert record.data_classification is ImportDataClassification.SYNTHETIC_DEMO
    assert record.import_record_id == "IMP-DEMO-001"


def test_import_record_rejects_duplicate_symptom_labels_case_insensitively() -> None:
    with pytest.raises(ValidationError, match="symptom_labels must not repeat"):
        build_record(symptom_labels=("queue_backlog", "QUEUE_BACKLOG"))


def test_synthetic_demo_requires_relayops_source_namespace() -> None:
    with pytest.raises(ValidationError, match="synthetic_demo records require a relayops"):
        build_record(source_system="internal-export")


def test_import_record_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        IncidentImportRecord.model_validate(
            {
                **build_record().model_dump(mode="json"),
                "safe_procedure_ids": ["RB-001"],
            }
        )


def test_rejected_line_outcome_requires_a_failure_or_sensitive_finding() -> None:
    with pytest.raises(ValidationError, match="rejected import outcomes require"):
        ImportLineOutcome(
            line_number=1,
            accepted_for_review=False,
        )
