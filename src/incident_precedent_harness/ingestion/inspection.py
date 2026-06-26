"""Review-only JSONL inspection for historical incident export batches."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import ValidationError

from incident_precedent_harness.ingestion.models import (
    ImportBatchInspectionReport,
    ImportFailureCode,
    ImportLineOutcome,
    IncidentImportRecord,
)
from incident_precedent_harness.ingestion.sensitive_content import find_sensitive_content


class ImportBatchReadError(ValueError):
    """Raised only when the input bytes cannot be read at all."""


def inspect_import_batch(*, input_path: Path, batch_id: str) -> ImportBatchInspectionReport:
    """Inspect one JSONL batch without mutating corpus, evaluation, or evidence assets."""

    try:
        raw_bytes = input_path.read_bytes()
    except OSError as error:
        raise ImportBatchReadError(f"cannot read import batch: {input_path.name}") from error

    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ImportBatchReadError(f"import batch is not valid UTF-8: {input_path.name}") from error

    outcomes: list[ImportLineOutcome] = []
    import_ids: set[str] = set()
    source_identities: set[str] = set()

    for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
        outcome = _inspect_line(
            line_number=line_number,
            raw_line=raw_line,
            import_ids=import_ids,
            source_identities=source_identities,
        )
        outcomes.append(outcome)

    accepted_record_count = sum(outcome.accepted_for_review for outcome in outcomes)
    rejected_record_count = len(outcomes) - accepted_record_count
    return ImportBatchInspectionReport(
        batch_id=batch_id,
        input_file_name=input_path.name,
        input_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        total_line_count=len(outcomes),
        accepted_record_count=accepted_record_count,
        rejected_record_count=rejected_record_count,
        ready_for_human_review=bool(outcomes) and rejected_record_count == 0,
        outputs=tuple(outcomes),
    )


def _inspect_line(
    *,
    line_number: int,
    raw_line: str,
    import_ids: set[str],
    source_identities: set[str],
) -> ImportLineOutcome:
    if not raw_line.strip():
        return ImportLineOutcome(
            line_number=line_number,
            accepted_for_review=False,
            failure_codes=(ImportFailureCode.BLANK_LINE,),
        )

    try:
        raw_value = json.loads(raw_line)
    except json.JSONDecodeError:
        return ImportLineOutcome(
            line_number=line_number,
            accepted_for_review=False,
            failure_codes=(ImportFailureCode.INVALID_JSON,),
        )

    try:
        record = IncidentImportRecord.model_validate(raw_value)
    except ValidationError:
        return ImportLineOutcome(
            line_number=line_number,
            accepted_for_review=False,
            failure_codes=(ImportFailureCode.SCHEMA_INVALID,),
        )

    source_identity = f"{record.source_system}:{record.source_record_id}"
    failure_codes: list[ImportFailureCode] = []
    if record.import_record_id in import_ids:
        failure_codes.append(ImportFailureCode.DUPLICATE_IMPORT_RECORD)
    if source_identity in source_identities:
        failure_codes.append(ImportFailureCode.DUPLICATE_SOURCE_RECORD)

    sensitive_findings = find_sensitive_content(
        title=record.title,
        summary=record.summary,
        source_reference=record.source_reference,
    )
    if sensitive_findings:
        failure_codes.append(ImportFailureCode.SENSITIVE_CONTENT_DETECTED)

    if failure_codes:
        return ImportLineOutcome(
            line_number=line_number,
            import_record_id=record.import_record_id,
            source_identity_sha256=_stable_identity_hash(source_identity),
            accepted_for_review=False,
            failure_codes=tuple(failure_codes),
            sensitive_findings=sensitive_findings,
        )

    import_ids.add(record.import_record_id)
    source_identities.add(source_identity)
    return ImportLineOutcome(
        line_number=line_number,
        import_record_id=record.import_record_id,
        source_identity_sha256=_stable_identity_hash(source_identity),
        accepted_for_review=True,
    )


def _stable_identity_hash(source_identity: str) -> str:
    """Return a trace-safe source identity correlation key without exposing its value."""

    return hashlib.sha256(source_identity.encode("utf-8")).hexdigest()
