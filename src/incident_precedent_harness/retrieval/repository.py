"""Validated local JSON corpus loading for deterministic baseline work."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from pydantic import ValidationError

from incident_precedent_harness.domain.incident_data import (
    CandidateInvestigationProcedure,
    EvalCase,
    HistoricalIncidentCard,
)


class DatasetLoadError(ValueError):
    """Raised when a local fixture asset cannot satisfy the dataset contract."""


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise DatasetLoadError(f"cannot read dataset asset: {path}") from error
    except json.JSONDecodeError as error:
        raise DatasetLoadError(f"invalid JSON dataset asset: {path}") from error


def _validate_unique_identifiers(items: Iterable[object], attribute: str, source: Path) -> None:
    identifiers = [str(getattr(item, attribute)) for item in items]
    duplicates = sorted({identifier for identifier in identifiers if identifiers.count(identifier) > 1})
    if duplicates:
        joined = ", ".join(duplicates)
        raise DatasetLoadError(f"duplicate {attribute} values in {source}: {joined}")


class JsonDatasetRepository:
    """Loads only validated corpus cards and evaluation cases from repository paths."""

    def __init__(self, repository_root: Path) -> None:
        self._repository_root = repository_root

    @property
    def incidents_directory(self) -> Path:
        return self._repository_root / "data" / "incidents"

    @property
    def calibration_directory(self) -> Path:
        return self._repository_root / "data" / "evals" / "calibration"

    @property
    def procedures_directory(self) -> Path:
        return self._repository_root / "data" / "procedures"

    def load_incidents(self) -> tuple[HistoricalIncidentCard, ...]:
        paths = sorted(self.incidents_directory.glob("INC-*.json"))
        if not paths:
            raise DatasetLoadError(f"no incident cards found in {self.incidents_directory}")

        cards: list[HistoricalIncidentCard] = []
        for path in paths:
            try:
                cards.append(HistoricalIncidentCard.model_validate(_load_json(path)))
            except ValidationError as error:
                raise DatasetLoadError(f"invalid incident card: {path}") from error

        _validate_unique_identifiers(cards, "incident_id", self.incidents_directory)
        return tuple(sorted(cards, key=lambda card: card.incident_id))

    def load_procedures(self) -> tuple[CandidateInvestigationProcedure, ...]:
        paths = sorted(self.procedures_directory.glob("RB-*.json"))
        if not paths:
            raise DatasetLoadError(f"no procedures found in {self.procedures_directory}")

        procedures: list[CandidateInvestigationProcedure] = []
        for path in paths:
            try:
                procedures.append(CandidateInvestigationProcedure.model_validate(_load_json(path)))
            except ValidationError as error:
                raise DatasetLoadError(f"invalid candidate procedure: {path}") from error

        _validate_unique_identifiers(procedures, "procedure_id", self.procedures_directory)
        return tuple(sorted(procedures, key=lambda procedure: procedure.procedure_id))

    def load_calibration_cases(self) -> tuple[EvalCase, ...]:
        paths = sorted(self.calibration_directory.glob("EVAL-*.json"))
        if not paths:
            raise DatasetLoadError(f"no calibration cases found in {self.calibration_directory}")

        cases: list[EvalCase] = []
        for path in paths:
            try:
                case = EvalCase.model_validate(_load_json(path))
            except ValidationError as error:
                raise DatasetLoadError(f"invalid calibration case: {path}") from error
            if case.split != "calibration":
                raise DatasetLoadError(f"calibration directory contains non-calibration case: {path}")
            cases.append(case)

        _validate_unique_identifiers(cases, "eval_id", self.calibration_directory)
        return tuple(sorted(cases, key=lambda case: case.eval_id))
