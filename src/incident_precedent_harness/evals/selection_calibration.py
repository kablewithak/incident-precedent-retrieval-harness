"""Validated loading and integrity checks for selection-calibration fixtures."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

from pydantic import ValidationError

from incident_precedent_harness.domain.incident_data import HistoricalIncidentCard
from incident_precedent_harness.domain.incident_enums import IncidentFamily
from incident_precedent_harness.domain.selection_calibration import (
    RepresentativeSelectionCalibrationCase,
)
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository


class SelectionCalibrationLoadError(ValueError):
    """Raised when a calibration fixture fails its typed integrity contract."""


def load_selection_calibration_cases(
    repository_root: Path,
) -> tuple[RepresentativeSelectionCalibrationCase, ...]:
    """Load only the dedicated selection-calibration fixture directory."""
    directory = repository_root / "data" / "evals" / "selection_calibration"
    paths = sorted(directory.glob("SEL-CAL-*.json"))
    if not paths:
        raise SelectionCalibrationLoadError(
            f"no selection calibration cases found in {directory}"
        )

    cases: list[RepresentativeSelectionCalibrationCase] = []
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except OSError as error:
            raise SelectionCalibrationLoadError(
                f"cannot read selection calibration case: {path}"
            ) from error
        except json.JSONDecodeError as error:
            raise SelectionCalibrationLoadError(
                f"invalid JSON selection calibration case: {path}"
            ) from error
        try:
            cases.append(RepresentativeSelectionCalibrationCase.model_validate(payload))
        except ValidationError as error:
            raise SelectionCalibrationLoadError(
                f"invalid selection calibration case: {path}"
            ) from error

    validate_selection_calibration_cases(
        cases=tuple(cases),
        incidents=JsonDatasetRepository(repository_root).load_incidents(),
    )
    return tuple(sorted(cases, key=lambda case: case.selection_case_id))


def validate_selection_calibration_cases(
    *,
    cases: tuple[RepresentativeSelectionCalibrationCase, ...],
    incidents: tuple[HistoricalIncidentCard, ...],
) -> None:
    """Validate candidate coverage, selection scope, and order-pair invariants."""
    identifiers = [case.selection_case_id for case in cases]
    duplicates = sorted({identifier for identifier in identifiers if identifiers.count(identifier) > 1})
    if duplicates:
        raise SelectionCalibrationLoadError(
            "duplicate selection_case_id values: " + ", ".join(duplicates)
        )

    incidents_by_id = {incident.incident_id: incident for incident in incidents}
    for case in cases:
        for incident_id in case.candidate_incident_ids:
            incident = incidents_by_id.get(incident_id)
            if incident is None:
                raise SelectionCalibrationLoadError(
                    f"{case.selection_case_id} references an unknown candidate: {incident_id}"
                )
            if incident.incident_family is not IncidentFamily.CONNECTION_POOL_EXHAUSTION:
                raise SelectionCalibrationLoadError(
                    f"{case.selection_case_id} candidate is not connection_pool_exhaustion: {incident_id}"
                )
            if incident.selection_signature is None:
                raise SelectionCalibrationLoadError(
                    f"{case.selection_case_id} candidate lacks selection_signature: {incident_id}"
                )

    _validate_order_invariance_groups(cases)


def _validate_order_invariance_groups(
    cases: Iterable[RepresentativeSelectionCalibrationCase],
) -> None:
    grouped: dict[str, list[RepresentativeSelectionCalibrationCase]] = defaultdict(list)
    for case in cases:
        if case.order_invariance_group is not None:
            grouped[case.order_invariance_group].append(case)

    for group, members in grouped.items():
        if len(members) != 2:
            raise SelectionCalibrationLoadError(
                f"{group} must contain exactly two order variants"
            )
        variants = {member.order_variant for member in members}
        if variants != {"canonical", "reversed"}:
            raise SelectionCalibrationLoadError(
                f"{group} must contain canonical and reversed variants"
            )

        canonical = next(member for member in members if member.order_variant == "canonical")
        reversed_case = next(member for member in members if member.order_variant == "reversed")
        if tuple(reversed(canonical.candidate_incident_ids)) != reversed_case.candidate_incident_ids:
            raise SelectionCalibrationLoadError(
                f"{group} reversed candidate order does not mirror canonical order"
            )
        if canonical.selection_intake != reversed_case.selection_intake:
            raise SelectionCalibrationLoadError(
                f"{group} variants must share the same selection intake"
            )
        if canonical.expected_outcome != reversed_case.expected_outcome:
            raise SelectionCalibrationLoadError(
                f"{group} variants must share the same expected outcome"
            )
