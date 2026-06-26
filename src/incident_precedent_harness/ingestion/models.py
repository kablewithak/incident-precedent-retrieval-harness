"""Typed contracts for controlled historical-incident import inspection.

These models describe unapproved import candidates. They intentionally are not
HistoricalIncidentCard models: source exports cannot set final retrieval labels,
procedure safety, or review status by themselves.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from incident_precedent_harness.domain.incident_enums import ChangeContext

ImportRecordIdentifier = Annotated[
    str,
    Field(pattern=r"^IMP-[A-Z0-9][A-Z0-9_-]{2,63}$"),
]
SourceSystemIdentifier = Annotated[
    str,
    Field(pattern=r"^[a-z][a-z0-9_-]{2,63}$"),
]
SourceRecordIdentifier = Annotated[
    str,
    Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,127}$"),
]
ShortSafeText = Annotated[str, Field(min_length=1, max_length=240)]
SummarySafeText = Annotated[str, Field(min_length=1, max_length=4_000)]


class ImportDataClassification(str, Enum):
    """Allowed dataset posture for a staged import candidate."""

    SYNTHETIC_DEMO = "synthetic_demo"
    SANITIZED_INTERNAL = "sanitized_internal"


class ImportFailureCode(str, Enum):
    """Trace-safe line and batch failures emitted by inspection."""

    BLANK_LINE = "blank_line"
    INVALID_JSON = "invalid_json"
    SCHEMA_INVALID = "schema_invalid"
    DUPLICATE_IMPORT_RECORD = "duplicate_import_record"
    DUPLICATE_SOURCE_RECORD = "duplicate_source_record"
    SENSITIVE_CONTENT_DETECTED = "sensitive_content_detected"
    INPUT_UNREADABLE = "input_unreadable"


class SensitiveContentCode(str, Enum):
    """Named detection classes; matched values must never enter reports."""

    API_KEY_ASSIGNMENT = "api_key_assignment"
    BEARER_TOKEN = "bearer_token"
    CREDENTIAL_URL = "credential_url"
    EMAIL_ADDRESS = "email_address"
    IPV4_ADDRESS = "ipv4_address"
    PASSWORD_ASSIGNMENT = "password_assignment"


class SensitiveContentFinding(BaseModel):
    """A safe pointer to a suspicious field without the matched text."""

    model_config = ConfigDict(extra="forbid")

    field_name: str = Field(pattern=r"^(title|summary|source_reference)$")
    code: SensitiveContentCode


class IncidentImportRecord(BaseModel):
    """One unapproved, sanitized historical-incident export record."""

    model_config = ConfigDict(extra="forbid")

    import_record_id: ImportRecordIdentifier
    source_system: SourceSystemIdentifier
    source_record_id: SourceRecordIdentifier
    data_classification: ImportDataClassification
    title: ShortSafeText
    summary: SummarySafeText
    occurred_on: date
    service: ShortSafeText
    component: ShortSafeText
    change_context: ChangeContext
    symptom_labels: tuple[ShortSafeText, ...] = Field(min_length=1, max_length=12)
    source_reference: ShortSafeText

    @field_validator("symptom_labels")
    @classmethod
    def reject_duplicate_symptom_labels(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        normalized = tuple(label.casefold() for label in value)
        if len(set(normalized)) != len(normalized):
            raise ValueError("symptom_labels must not repeat")
        return value

    @model_validator(mode="after")
    def require_demo_source_namespace(self) -> "IncidentImportRecord":
        if (
            self.data_classification is ImportDataClassification.SYNTHETIC_DEMO
            and not self.source_system.startswith("relayops-")
        ):
            raise ValueError("synthetic_demo records require a relayops-* source_system")
        return self


class ImportLineOutcome(BaseModel):
    """One trace-safe inspection outcome; raw export text is intentionally absent."""

    model_config = ConfigDict(extra="forbid")

    line_number: int = Field(ge=1)
    import_record_id: str | None = Field(default=None, max_length=64)
    source_identity_sha256: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$"
    )
    accepted_for_review: bool
    failure_codes: tuple[ImportFailureCode, ...] = ()
    sensitive_findings: tuple[SensitiveContentFinding, ...] = ()

    @model_validator(mode="after")
    def validate_outcome_shape(self) -> "ImportLineOutcome":
        if self.accepted_for_review and (self.failure_codes or self.sensitive_findings):
            raise ValueError("accepted import outcomes cannot contain failures or findings")
        if not self.accepted_for_review and not (
            self.failure_codes or self.sensitive_findings
        ):
            raise ValueError("rejected import outcomes require a failure or sensitive finding")
        return self


class ImportBatchInspectionReport(BaseModel):
    """Safe, deterministic result of inspecting one JSONL import batch."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{2,63}$")
    input_file_name: str = Field(min_length=1, max_length=255)
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    total_line_count: int = Field(ge=0)
    accepted_record_count: int = Field(ge=0)
    rejected_record_count: int = Field(ge=0)
    ready_for_human_review: bool
    outputs: tuple[ImportLineOutcome, ...]

    @model_validator(mode="after")
    def validate_counts_and_review_gate(self) -> "ImportBatchInspectionReport":
        if len(self.outputs) != self.total_line_count:
            raise ValueError("total_line_count must equal the number of line outcomes")
        accepted_count = sum(outcome.accepted_for_review for outcome in self.outputs)
        if accepted_count != self.accepted_record_count:
            raise ValueError("accepted_record_count does not match line outcomes")
        if self.total_line_count - accepted_count != self.rejected_record_count:
            raise ValueError("rejected_record_count does not match line outcomes")
        if self.ready_for_human_review != (
            self.total_line_count > 0 and self.rejected_record_count == 0
        ):
            raise ValueError("review readiness must fail closed on empty or rejected batches")
        return self
