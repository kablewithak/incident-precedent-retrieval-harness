"""Tests for deterministic, transparent lexical ranking."""

from __future__ import annotations

from pathlib import Path

import pytest

from incident_precedent_harness.retrieval import JsonDatasetRepository, KeywordRetriever

ROOT = Path(__file__).resolve().parents[2]


def test_keyword_retriever_is_deterministic_and_returns_sorted_match_terms() -> None:
    incidents = JsonDatasetRepository(ROOT).load_incidents()
    retriever = KeywordRetriever(incidents)
    query = "Webhook queue backlog after consumer deployment with readiness failures"

    first = retriever.rank(query, top_k=5)
    second = retriever.rank(query, top_k=5)

    assert first == second
    assert [candidate.rank for candidate in first] == [1, 2, 3, 4, 5]
    assert all(candidate.matched_terms == tuple(sorted(candidate.matched_terms)) for candidate in first)
    assert first[0].incident_id == "INC-003"


def test_keyword_retriever_rejects_invalid_top_k() -> None:
    retriever = KeywordRetriever(JsonDatasetRepository(ROOT).load_incidents())

    with pytest.raises(ValueError, match="top_k"):
        retriever.rank("queue backlog", top_k=0)


def test_keyword_retriever_returns_no_candidates_for_no_meaningful_tokens() -> None:
    retriever = KeywordRetriever(JsonDatasetRepository(ROOT).load_incidents())

    assert retriever.rank("and the or with", top_k=5) == ()
