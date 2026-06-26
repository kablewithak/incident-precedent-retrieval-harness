"""Stable, non-leaking text representations for local dense retrieval."""

from __future__ import annotations

import hashlib
import json

from incident_precedent_harness.domain.incident_data import HistoricalIncidentCard

REPRESENTATION_VERSION = "incident-retrieval-representation-v1"


def incident_retrieval_representation(card: HistoricalIncidentCard) -> str:
    """Build the approved dense-retrieval text for one historical card.

    The representation excludes incident IDs, procedure IDs, source identifiers,
    explicit incident-family labels, failure-mechanism labels, and all evaluation
    labels. It carries only the controlled operational context a responder could
    reasonably compare during early triage.
    """

    started_after_change = (
        "true"
        if card.started_after_change is True
        else "false"
        if card.started_after_change is False
        else "unknown"
    )
    fields = (
        ("title", card.title),
        ("service", card.service),
        ("component", card.component),
        ("region", card.region or "unknown"),
        ("change_context", card.change_context.value),
        ("started_after_change", started_after_change),
        ("symptoms", " | ".join(card.symptoms)),
        ("observability_signals", " | ".join(card.observability_signals)),
        ("recovery_state", card.recovery_state.value),
        ("historical_summary", card.narrative_safe),
    )
    return "\n".join(f"{name}={value}" for name, value in fields)


def representation_sha256(text: str) -> str:
    """Return the stable digest used to bind an index entry to its source text."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def corpus_fingerprint_sha256(cards: tuple[HistoricalIncidentCard, ...]) -> str:
    """Hash only approved IDs and representation digests, never raw card content."""

    rows = [
        {
            "incident_id": card.incident_id,
            "representation_sha256": representation_sha256(
                incident_retrieval_representation(card)
            ),
        }
        for card in sorted(cards, key=lambda item: item.incident_id)
    ]
    canonical = json.dumps(
        {
            "representation_version": REPRESENTATION_VERSION,
            "entries": rows,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
