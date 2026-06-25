"""Typed, calibration-only fixtures for representative-selection contracts.

This module defines labelled calibration assets for a future selector. It does
not implement selection, alter the active anti-anchoring policy, or load any
held-out data.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from incident_precedent_harness.domain.incident_data import (
    NonEmptyText,
    RecordIdentifier,
    RepresentativeSelectionIntake,
)


SelectionCalibrationIdentifier = Annotated[
    str,
    Field(pattern=r"^SEL-CAL-[0-9]{3}$"),
]
OrderInvarianceGroup = Annotated[
    str,
    Field(pattern=r"^ORDER-INVARIANCE-[0-9]{3}$"),
]


class RepresentativeSelectionExpectationState(str, Enum):
    """Expected calibration outcome for a future representative selector."""

    SINGLE_REPRESENTATIVE = "single_representative"
    EXPLICIT_TIE = "explicit_tie"


class RepresentativeSelectionExpectedOutcome(BaseModel):
    """Labelled calibration outcome, intentionally separate from selection input."""

    model_config = ConfigDict(extra="forbid")

    state: RepresentativeSelectionExpectationState
    representative_incident_ids: tuple[RecordIdentifier, ...] = Field(
        min_length=1,
        max_length=4,
    )

    @field_validator("representative_incident_ids")
    @classmethod
    def reject_duplicate_representative_ids(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("representative_incident_ids must not repeat")
        return value

    @model_validator(mode="after")
    def validate_outcome_cardinality(self) -> "RepresentativeSelectionExpectedOutcome":
        if (
            self.state is RepresentativeSelectionExpectationState.SINGLE_REPRESENTATIVE
            and len(self.representative_incident_ids) != 1
        ):
            raise ValueError("single_representative outcomes require exactly one card")
        if (
            self.state is RepresentativeSelectionExpectationState.EXPLICIT_TIE
            and len(self.representative_incident_ids) < 2
        ):
            raise ValueError("explicit_tie outcomes require at least two cards")
        return self


class RepresentativeSelectionCalibrationCase(BaseModel):
    """One fixed calibration fixture for the future schema-derived selector."""

    model_config = ConfigDict(extra="forbid")

    selection_case_id: SelectionCalibrationIdentifier
    split: Literal["selection_calibration"]
    contract_version: Literal["representative-selection-v1"]
    selection_intake: RepresentativeSelectionIntake
    candidate_incident_ids: tuple[RecordIdentifier, ...] = Field(min_length=2, max_length=4)
    expected_outcome: RepresentativeSelectionExpectedOutcome
    order_invariance_group: OrderInvarianceGroup | None = None
    order_variant: Literal["canonical", "reversed"] | None = None
    failure_label_intent: tuple[NonEmptyText, ...] = Field(min_length=1, max_length=8)
    acceptance_reason: NonEmptyText

    @field_validator("candidate_incident_ids")
    @classmethod
    def reject_duplicate_candidate_ids(
        cls,
        value: tuple[str, ...],
    ) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("candidate_incident_ids must not repeat")
        return value

    @model_validator(mode="after")
    def validate_expected_candidates_and_order_pairing(
        self,
    ) -> "RepresentativeSelectionCalibrationCase":
        if not set(self.expected_outcome.representative_incident_ids).issubset(
            self.candidate_incident_ids
        ):
            raise ValueError("expected representatives must be candidates in the fixture")
        if (self.order_invariance_group is None) != (self.order_variant is None):
            raise ValueError(
                "order_invariance_group and order_variant must be supplied together"
            )
        return self
