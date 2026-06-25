from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from incident_precedent_harness.domain.incident_data import (
    HistoricalIncidentCard,
    RepresentativeSelectionIntake,
)
from incident_precedent_harness.domain.incident_enums import (
    IncidentFamily,
    OperationalSignalFamily,
    RelayService,
)
from incident_precedent_harness.retrieval import JsonDatasetRepository


@pytest.fixture()
def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture()
def incident_payloads(repository_root: Path) -> dict[str, dict[str, object]]:
    return {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((repository_root / "data" / "incidents").glob("INC-*.json"))
    }


def test_connection_pool_cards_have_complete_schema_derived_signatures(
    repository_root: Path,
) -> None:
    incidents = JsonDatasetRepository(repository_root).load_incidents()
    connection_pool_cards = tuple(
        incident
        for incident in incidents
        if incident.incident_family is IncidentFamily.CONNECTION_POOL_EXHAUSTION
    )

    assert tuple(card.incident_id for card in connection_pool_cards) == (
        "INC-009",
        "INC-010",
        "INC-011",
        "INC-012",
    )
    assert all(card.selection_signature is not None for card in connection_pool_cards)
    assert all(
        card.selection_signature.service.value == card.service
        and card.selection_signature.component.value == card.component
        and card.selection_signature.change_context is card.change_context
        for card in connection_pool_cards
        if card.selection_signature is not None
    )


def test_non_connection_pool_cards_cannot_carry_selection_signature(
    incident_payloads: dict[str, dict[str, object]],
) -> None:
    payload = deepcopy(incident_payloads["INC-001"])
    payload["selection_signature"] = {
        "contract_version": "representative-selection-v1",
        "service": "feature-flag-service",
        "component": "cache-update-worker",
        "change_context": "none",
        "operational_signals": [
            {
                "signal_family": "component_error_pressure",
                "source_references": [
                    {
                        "source_field": "symptoms",
                        "source_values": ["cache invalidation retries increased"],
                    }
                ],
            }
        ],
    }

    with pytest.raises(ValidationError, match="only permitted for connection_pool_exhaustion"):
        HistoricalIncidentCard.model_validate(payload)


def test_connection_pool_card_requires_selection_signature(
    incident_payloads: dict[str, dict[str, object]],
) -> None:
    payload = deepcopy(incident_payloads["INC-009"])
    payload.pop("selection_signature")

    with pytest.raises(ValidationError, match="require a schema-derived selection_signature"):
        HistoricalIncidentCard.model_validate(payload)


def test_signature_rejects_source_values_not_present_on_parent_card(
    incident_payloads: dict[str, dict[str, object]],
) -> None:
    payload = deepcopy(incident_payloads["INC-009"])
    signature = payload["selection_signature"]
    assert isinstance(signature, dict)
    signals = signature["operational_signals"]
    assert isinstance(signals, list)
    references = signals[0]["source_references"]
    assert isinstance(references, list)
    references[0]["source_values"] = ["invented sidecar cue"]

    with pytest.raises(ValidationError, match="must appear in the parent observability_signals"):
        HistoricalIncidentCard.model_validate(payload)


def test_signature_rejects_duplicate_signal_family(
    incident_payloads: dict[str, dict[str, object]],
) -> None:
    payload = deepcopy(incident_payloads["INC-009"])
    signature = payload["selection_signature"]
    assert isinstance(signature, dict)
    signals = signature["operational_signals"]
    assert isinstance(signals, list)
    signals.append(deepcopy(signals[0]))

    with pytest.raises(ValidationError, match="must not repeat an operational signal family"):
        HistoricalIncidentCard.model_validate(payload)


def test_representative_selection_intake_rejects_label_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RepresentativeSelectionIntake.model_validate(
            {
                "service": RelayService.PAYMENTS_API.value,
                "operational_signal_families": [
                    OperationalSignalFamily.CONNECTION_POOL_PRESSURE.value
                ],
                "acceptable_precedent_ids": ["INC-009"],
            }
        )


def test_representative_selection_intake_rejects_conflicting_signal_statuses() -> None:
    with pytest.raises(ValidationError, match="cannot confirm and contradict"):
        RepresentativeSelectionIntake.model_validate(
            {
                "operational_signal_families": [
                    OperationalSignalFamily.CONNECTION_POOL_PRESSURE.value
                ],
                "contradicted_signal_families": [
                    OperationalSignalFamily.CONNECTION_POOL_PRESSURE.value
                ],
            }
        )
