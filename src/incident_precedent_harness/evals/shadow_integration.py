"""Fixed calibration fixtures for policy shadow-selection integration.

These fixtures bind an existing policy calibration case to separate typed
selection evidence. They do not extend ``EvalCase`` or derive selection inputs
from free text.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from incident_precedent_harness.decisions.models import (
    FamilySelectionIntakeBinding,
    ShadowSelectionState,
)
from incident_precedent_harness.domain.incident_data import EvalIdentifier, NonEmptyText, RecordIdentifier
from incident_precedent_harness.domain.incident_enums import IncidentFamily

ShadowCalibrationIdentifier = Annotated[str, Field(pattern=r"^SHADOW-CAL-[0-9]{3}$")]


class ShadowTraceExpectation(BaseModel):
    """Expected non-authoritative trace for one admitted incident family."""

    model_config = ConfigDict(extra="forbid")

    incident_family: IncidentFamily
    admitted_candidate_ids: tuple[RecordIdentifier, ...] = Field(min_length=1, max_length=12)
    selection_intake_present: bool
    selector_invoked: bool
    selection_state: ShadowSelectionState
    representative_incident_ids: tuple[RecordIdentifier, ...] = ()
    unavailable_reason: NonEmptyText | None = None

    @model_validator(mode="after")
    def validate_trace_expectation(self) -> "ShadowTraceExpectation":
        if len(set(self.admitted_candidate_ids)) != len(self.admitted_candidate_ids):
            raise ValueError("admitted_candidate_ids must not repeat")
        if tuple(sorted(self.admitted_candidate_ids)) != self.admitted_candidate_ids:
            raise ValueError("admitted_candidate_ids must be serialized in deterministic order")
        if not set(self.representative_incident_ids).issubset(self.admitted_candidate_ids):
            raise ValueError("representative IDs must be admitted candidates")
        if self.selection_state is ShadowSelectionState.SINGLE_REPRESENTATIVE:
            if not self.selector_invoked or len(self.representative_incident_ids) != 1:
                raise ValueError("single representative expectation requires one selector result")
        if self.selection_state is ShadowSelectionState.EXPLICIT_TIE:
            if not self.selector_invoked or len(self.representative_incident_ids) < 2:
                raise ValueError("explicit tie expectation requires a selector tie set")
        if self.selection_state in {
            ShadowSelectionState.UNAVAILABLE,
            ShadowSelectionState.NOT_APPLICABLE_SINGLE_CANDIDATE,
        }:
            if self.selector_invoked or self.representative_incident_ids:
                raise ValueError("unavailable and bypass expectations cannot carry selector output")
            if self.unavailable_reason is None:
                raise ValueError("unavailable and bypass expectations require a reason")
        return self


class ShadowIntegrationCalibrationCase(BaseModel):
    """One explicit bridge fixture for E1 shadow integration."""

    model_config = ConfigDict(extra="forbid")

    shadow_case_id: ShadowCalibrationIdentifier
    split: Literal["shadow_integration_calibration"]
    policy_case_id: EvalIdentifier
    selection_intake_bindings: tuple[FamilySelectionIntakeBinding, ...] = ()
    expected_traces: tuple[ShadowTraceExpectation, ...] = ()
    failure_label_intent: tuple[NonEmptyText, ...] = Field(min_length=1, max_length=8)
    acceptance_reason: NonEmptyText

    @field_validator("selection_intake_bindings")
    @classmethod
    def reject_duplicate_selection_families(
        cls,
        value: tuple[FamilySelectionIntakeBinding, ...],
    ) -> tuple[FamilySelectionIntakeBinding, ...]:
        families = [binding.incident_family for binding in value]
        if len(set(families)) != len(families):
            raise ValueError("selection_intake_bindings must not repeat an incident family")
        return value

    @field_validator("expected_traces")
    @classmethod
    def reject_duplicate_trace_families(
        cls,
        value: tuple[ShadowTraceExpectation, ...],
    ) -> tuple[ShadowTraceExpectation, ...]:
        families = [trace.incident_family for trace in value]
        if len(set(families)) != len(families):
            raise ValueError("expected_traces must not repeat an incident family")
        return value


class ShadowIntegrationFixtureLoadError(ValueError):
    """Raised when a shadow integration fixture is unreadable or invalid."""


def load_shadow_integration_calibration_cases(
    repository_root: Path,
) -> tuple[ShadowIntegrationCalibrationCase, ...]:
    """Load only explicit E1 bridge fixtures; held-out paths are never inspected."""
    directory = repository_root / "data" / "evals" / "shadow_integration"
    paths = sorted(directory.glob("SHADOW-CAL-*.json"))
    if not paths:
        raise ShadowIntegrationFixtureLoadError(
            f"no shadow integration fixtures found in {directory}"
        )
    cases: list[ShadowIntegrationCalibrationCase] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except OSError as error:
            raise ShadowIntegrationFixtureLoadError(
                f"cannot read shadow integration fixture: {path}"
            ) from error
        except json.JSONDecodeError as error:
            raise ShadowIntegrationFixtureLoadError(
                f"invalid JSON shadow integration fixture: {path}"
            ) from error
        try:
            cases.append(ShadowIntegrationCalibrationCase.model_validate(payload))
        except ValidationError as error:
            raise ShadowIntegrationFixtureLoadError(
                f"invalid shadow integration fixture: {path}"
            ) from error
    identifiers = [case.shadow_case_id for case in cases]
    duplicates = sorted({item for item in identifiers if identifiers.count(item) > 1})
    if duplicates:
        raise ShadowIntegrationFixtureLoadError(
            "duplicate shadow_case_id values: " + ", ".join(duplicates)
        )
    return tuple(sorted(cases, key=lambda case: case.shadow_case_id))
