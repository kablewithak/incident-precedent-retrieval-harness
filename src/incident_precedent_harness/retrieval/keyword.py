"""Deterministic BM25-style keyword baseline.

This module intentionally does not infer decision states, surface procedures, or
pretend lexical similarity proves operational compatibility. It provides a
transparent ranker that the later semantic pipeline must beat without violating
anti-anchoring constraints.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from incident_precedent_harness.domain.incident_data import HistoricalIncidentCard
from incident_precedent_harness.retrieval.models import KeywordCandidate

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
        "while",
    }
)


@dataclass(frozen=True, slots=True)
class _IndexedIncident:
    card: HistoricalIncidentCard
    tokens: tuple[str, ...]
    term_frequencies: Counter[str]


def tokenize(text: str) -> tuple[str, ...]:
    """Normalize controlled text without stemming or model-dependent transforms."""

    return tuple(
        token
        for token in _TOKEN_PATTERN.findall(text.lower().replace("_", " ").replace("-", " "))
        if token not in _STOP_WORDS
    )


def _incident_text(card: HistoricalIncidentCard) -> str:
    """Build the explicit corpus representation used by the baseline."""

    fields = [
        card.title,
        card.incident_family.value.replace("_", " "),
        card.service,
        card.component,
        card.change_context.value,
        card.failure_mechanism,
        card.mitigation_summary,
        card.timeline_summary,
        card.narrative_safe,
        *card.symptoms,
        *card.observability_signals,
        *(fact.value.replace("_", " ") for fact in card.required_verification_facts),
    ]
    return " ".join(fields)


class KeywordRetriever:
    """A deterministic in-memory BM25 baseline for a small local corpus."""

    algorithm_name = "BM25-style lexical ranking (k1=1.2, b=0.75)"
    tokenization_name = "lowercase alphanumeric tokens; underscore/hyphen split; fixed stopword list"

    def __init__(self, incidents: tuple[HistoricalIncidentCard, ...]) -> None:
        if not incidents:
            raise ValueError("KeywordRetriever requires at least one incident")
        self._documents = tuple(
            _IndexedIncident(
                card=card,
                tokens=tokenize(_incident_text(card)),
                term_frequencies=Counter(tokenize(_incident_text(card))),
            )
            for card in incidents
        )
        self._average_document_length = sum(len(item.tokens) for item in self._documents) / len(
            self._documents
        )
        self._document_frequencies = Counter(
            token for item in self._documents for token in set(item.tokens)
        )

    @property
    def incident_families_by_id(self) -> dict[str, str]:
        """Return the fixed family assigned to each in-memory incident card."""

        return {
            item.card.incident_id: item.card.incident_family.value
            for item in self._documents
        }

    def rank(self, query: str, *, top_k: int = 5) -> tuple[KeywordCandidate, ...]:
        """Rank candidates by explicit lexical overlap only."""

        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        query_tokens = tokenize(query)
        if not query_tokens:
            return ()
        query_terms = set(query_tokens)

        scored: list[tuple[HistoricalIncidentCard, float, tuple[str, ...]]] = []
        for item in self._documents:
            score = self._score(query_terms, item)
            matched_terms = tuple(sorted(query_terms.intersection(item.term_frequencies)))
            scored.append((item.card, score, matched_terms))

        ranked = sorted(scored, key=lambda item: (-item[1], item[0].incident_id))[:top_k]
        return tuple(
            KeywordCandidate(
                incident_id=card.incident_id,
                rank=index,
                score=round(score, 8),
                matched_terms=matched_terms,
            )
            for index, (card, score, matched_terms) in enumerate(ranked, start=1)
        )

    def _score(self, query_terms: set[str], item: _IndexedIncident) -> float:
        score = 0.0
        document_count = len(self._documents)
        k1 = 1.2
        b = 0.75
        document_length = len(item.tokens)
        denominator_normalizer = k1 * (
            1 - b + b * document_length / self._average_document_length
        )
        for term in query_terms:
            term_frequency = item.term_frequencies.get(term, 0)
            if not term_frequency:
                continue
            document_frequency = self._document_frequencies[term]
            inverse_document_frequency = math.log(
                1 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            score += inverse_document_frequency * (
                term_frequency * (k1 + 1) / (term_frequency + denominator_normalizer)
            )
        return score
