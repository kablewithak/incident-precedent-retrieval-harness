"""Validate schema-derived representative-selection coverage without selection logic."""

from __future__ import annotations

import argparse
from pathlib import Path

from incident_precedent_harness.domain.incident_enums import IncidentFamily
from incident_precedent_harness.retrieval import JsonDatasetRepository


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the connection-pool schema signatures required by "
            "ADR-0012 without invoking representative-selection logic."
        )
    )
    parser.add_argument(
        "--repository-root",
        default=".",
        help="Repository root containing data/incidents.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repository_root = Path(args.repository_root).resolve()
    incidents = JsonDatasetRepository(repository_root).load_incidents()

    connection_pool_cards = tuple(
        incident
        for incident in incidents
        if incident.incident_family is IncidentFamily.CONNECTION_POOL_EXHAUSTION
    )
    if not connection_pool_cards:
        raise RuntimeError("no connection_pool_exhaustion cards found")

    missing_signatures = tuple(
        card.incident_id for card in connection_pool_cards if card.selection_signature is None
    )
    non_pool_signatures = tuple(
        card.incident_id
        for card in incidents
        if card.incident_family is not IncidentFamily.CONNECTION_POOL_EXHAUSTION
        and card.selection_signature is not None
    )
    if missing_signatures or non_pool_signatures:
        raise RuntimeError(
            "schema signature coverage failed: "
            f"missing_connection_pool_signatures={missing_signatures}; "
            f"unexpected_non_pool_signatures={non_pool_signatures}"
        )

    signal_count = sum(
        len(card.selection_signature.operational_signals)
        for card in connection_pool_cards
        if card.selection_signature is not None
    )

    print("REPRESENTATIVE SELECTION SCHEMA VALIDATION")
    print("------------------------------------------")
    print(f"connection_pool_cards={len(connection_pool_cards)}")
    print(f"schema_signatures={len(connection_pool_cards)}")
    print(f"schema_derived_signal_families={signal_count}")
    print("active_policy_changed=false")
    print("heldout_loaded=false")
    print("selector_executed=false")
    print("status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
