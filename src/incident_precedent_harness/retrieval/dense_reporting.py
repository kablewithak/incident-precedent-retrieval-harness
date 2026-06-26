"""Calibration-only reporting for local-SIE dense retrieval."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from incident_precedent_harness.domain.incident_data import EvalCase, HistoricalIncidentCard
from incident_precedent_harness.inference.models import EmbeddingRequest, InferenceProfile, TextItem
from incident_precedent_harness.inference.protocol import SemanticInferenceClient
from incident_precedent_harness.retrieval.dense import DenseRetriever
from incident_precedent_harness.retrieval.keyword import KeywordRetriever
from incident_precedent_harness.retrieval.models import (
    DenseCaseOutcome,
    DenseRetrievalCalibrationReport,
    DenseRetrievalMetrics,
    DenseVsKeywordComparison,
    KeywordBaselineMetrics,
)
from incident_precedent_harness.retrieval.reporting import run_keyword_baseline


def run_dense_retrieval_calibration(
    *,
    retriever: DenseRetriever,
    incidents: tuple[HistoricalIncidentCard, ...],
    client: SemanticInferenceClient,
    embedding_profile: InferenceProfile,
    cases: tuple[EvalCase, ...],
    trace_id: UUID,
    top_k: int = 5,
) -> DenseRetrievalCalibrationReport:
    """Evaluate dense retrieval on calibration only, alongside the lexical baseline."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    query_items = tuple(
        TextItem(item_id=case.eval_id, text=case.input_summary) for case in cases
    )
    embedding_response = client.encode_incident_texts(
        EmbeddingRequest(
            trace_id=trace_id,
            profile=embedding_profile,
            items=query_items,
        )
    )
    vectors_by_eval_id = {vector.item_id: vector.dense_values for vector in embedding_response.vectors}
    expected_ids = {case.eval_id for case in cases}
    if set(vectors_by_eval_id) != expected_ids or len(vectors_by_eval_id) != len(expected_ids):
        raise ValueError("query embedding identities did not match calibration case IDs")

    incident_families = retriever.incident_families_by_id
    outcomes: list[DenseCaseOutcome] = []
    for case in cases:
        candidates, similarity_latency_ms = retriever.rank_with_latency(
            vectors_by_eval_id[case.eval_id],
            top_k=top_k,
        )
        candidate_ids = tuple(candidate.incident_id for candidate in candidates)
        candidate_incident_families = tuple(
            incident_families[incident_id] for incident_id in candidate_ids
        )
        expected_incident_families = tuple(
            sorted(
                {
                    incident_families[incident_id]
                    for incident_id in case.acceptable_precedent_ids
                }
            )
        )
        first_acceptable_rank = next(
            (
                rank
                for rank, incident_id in enumerate(candidate_ids, start=1)
                if incident_id in case.acceptable_precedent_ids
            ),
            None,
        )
        top_1_is_unsafe = bool(candidate_ids and candidate_ids[0] in case.unsafe_precedent_ids)
        labels: list[str] = []
        if case.acceptable_precedent_ids and first_acceptable_rank is None:
            labels.append("retrieval_miss")
        if top_1_is_unsafe:
            labels.append("false_operational_match")
        if case.expected_decision_state.value == "insufficient_precedent" and candidate_ids:
            labels.append("dense_candidate_returned_without_abstention_policy")
        outcomes.append(
            DenseCaseOutcome(
                eval_id=case.eval_id,
                expected_decision_state=case.expected_decision_state.value,
                candidate_ids=candidate_ids,
                candidate_incident_families=candidate_incident_families,
                expected_incident_families=expected_incident_families,
                acceptable_precedent_ids=case.acceptable_precedent_ids,
                unsafe_precedent_ids=case.unsafe_precedent_ids,
                first_acceptable_rank=first_acceptable_rank,
                top_1_is_unsafe=top_1_is_unsafe,
                similarity_latency_ms=similarity_latency_ms,
                failure_labels=tuple(labels),
            )
        )

    dense_metrics = _metrics(tuple(outcomes))
    keyword_metrics = run_keyword_baseline(
        retriever=KeywordRetriever(incidents),
        cases=cases,
        top_k=top_k,
    ).metrics
    return DenseRetrievalCalibrationReport(
        generated_at=datetime.now(UTC),
        corpus_incident_count=len(incidents),
        calibration_case_count=len(cases),
        top_k=top_k,
        index_manifest=retriever.index_manifest,
        query_embedding_profile=embedding_profile,
        query_embedding_batch_latency_ms=embedding_response.latency_ms,
        metrics=dense_metrics,
        keyword_baseline_metrics=keyword_metrics,
        comparison_to_keyword_baseline=_comparison(keyword_metrics, dense_metrics),
        outcomes=tuple(outcomes),
        known_limits=(
            "Calibration-only report; held-out cases are not loaded or scored.",
            "Dense retrieval does not assign a final decision state or authorize a procedure.",
            "Cosine retrieval has not yet been reranked with SIE score.",
            "A candidate returned for an insufficient-precedent case is a retrieval limitation, not acceptable evidence.",
            "The provider latency is an observed batch encoding time for synthetic calibration inputs, not a warm-operation or production latency claim.",
            "This report is not a promotion decision; safety policy and provider-degraded behavior are evaluated in later slices.",
        ),
    )


def write_dense_retrieval_report(
    report: DenseRetrievalCalibrationReport,
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write machine-readable and reviewer-readable dense calibration evidence."""

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _metrics(outcomes: tuple[DenseCaseOutcome, ...]) -> DenseRetrievalMetrics:
    positive = tuple(outcome for outcome in outcomes if outcome.acceptable_precedent_ids)
    reciprocal_ranks = tuple(
        1 / outcome.first_acceptable_rank
        for outcome in positive
        if outcome.first_acceptable_rank is not None
    )
    recall_at_five = tuple(
        bool(set(outcome.candidate_incident_families).intersection(outcome.expected_incident_families))
        for outcome in positive
    )
    safety_evaluable = tuple(outcome for outcome in outcomes if outcome.unsafe_precedent_ids)
    false_operational_match_count = sum(outcome.top_1_is_unsafe for outcome in safety_evaluable)
    latencies = tuple(outcome.similarity_latency_ms for outcome in outcomes)
    return DenseRetrievalMetrics(
        scored_case_count=len(outcomes),
        cases_with_acceptable_precedent=len(positive),
        correct_precedent_mrr=round(sum(reciprocal_ranks) / len(positive), 4) if positive else None,
        incident_family_recall_at_5=round(sum(recall_at_five) / len(positive), 4) if positive else None,
        safety_evaluable_case_count=len(safety_evaluable),
        safe_precedent_top_1_rate=(
            round(
                sum(not outcome.top_1_is_unsafe for outcome in safety_evaluable)
                / len(safety_evaluable),
                4,
            )
            if safety_evaluable
            else None
        ),
        false_operational_match_count=false_operational_match_count,
        false_operational_match_rate=(
            round(false_operational_match_count / len(safety_evaluable), 4)
            if safety_evaluable
            else None
        ),
        p50_similarity_latency_ms=round(_percentile(latencies, 0.5), 4),
        p95_similarity_latency_ms=round(_percentile(latencies, 0.95), 4),
    )


def _comparison(
    keyword: KeywordBaselineMetrics,
    dense: DenseRetrievalMetrics,
) -> DenseVsKeywordComparison:
    return DenseVsKeywordComparison(
        keyword_correct_precedent_mrr=keyword.correct_precedent_mrr,
        dense_correct_precedent_mrr=dense.correct_precedent_mrr,
        correct_precedent_mrr_delta=_delta(
            dense.correct_precedent_mrr,
            keyword.correct_precedent_mrr,
        ),
        keyword_incident_family_recall_at_5=keyword.incident_family_recall_at_5,
        dense_incident_family_recall_at_5=dense.incident_family_recall_at_5,
        incident_family_recall_at_5_delta=_delta(
            dense.incident_family_recall_at_5,
            keyword.incident_family_recall_at_5,
        ),
        keyword_false_operational_match_rate=keyword.false_operational_match_rate,
        dense_false_operational_match_rate=dense.false_operational_match_rate,
        false_operational_match_rate_delta=_delta(
            dense.false_operational_match_rate,
            keyword.false_operational_match_rate,
        ),
    )


def _delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(left - right, 4)


def _percentile(values: tuple[float, ...], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _render_markdown(report: DenseRetrievalCalibrationReport) -> str:
    metrics = report.metrics
    baseline = report.keyword_baseline_metrics
    comparison = report.comparison_to_keyword_baseline
    manifest = report.index_manifest
    lines = [
        "# Local SIE Dense Retrieval Calibration Report",
        "",
        "## Scope",
        "",
        "This report compares local-SIE embedding retrieval with the deterministic keyword baseline on calibration fixtures only.",
        "It does not score held-out cases, assign product decision states, authorize procedures, or constitute a promotion decision.",
        "",
        "## Dense index binding",
        "",
        f"- Index ID: `{manifest.index_id}`",
        f"- Index format: `{manifest.index_format_version}`",
        f"- Corpus cards: `{manifest.corpus_incident_count}`",
        f"- Corpus fingerprint: `{manifest.corpus_fingerprint_sha256}`",
        f"- Representation version: `{manifest.representation_version}`",
        f"- Encode profile: `{manifest.embedding_profile.profile_id}`",
        f"- Encode model: `{manifest.embedding_profile.model_id}`",
        f"- Vector dimension: `{manifest.vector_dimension}`",
        f"- Query embedding batch latency (ms): `{report.query_embedding_batch_latency_ms}`",
        "",
        "## Calibration comparison",
        "",
        "| Metric | Keyword baseline | Dense retrieval | Dense minus keyword |",
        "|---|---:|---:|---:|",
        f"| Correct-precedent MRR | {_value(baseline.correct_precedent_mrr)} | {_value(metrics.correct_precedent_mrr)} | {_value(comparison.correct_precedent_mrr_delta)} |",
        f"| Incident-family Recall@5 | {_value(baseline.incident_family_recall_at_5)} | {_value(metrics.incident_family_recall_at_5)} | {_value(comparison.incident_family_recall_at_5_delta)} |",
        f"| False-operational-match rate | {_value(baseline.false_operational_match_rate)} | {_value(metrics.false_operational_match_rate)} | {_value(comparison.false_operational_match_rate_delta)} |",
        "",
        "## Calibration interpretation",
        "",
        f"- {_exact_precedent_interpretation(comparison.correct_precedent_mrr_delta)}",
        f"- {_incident_family_interpretation(comparison.incident_family_recall_at_5_delta)}",
        f"- {_safety_proxy_interpretation(comparison.false_operational_match_rate_delta)}",
        "- Decision: this calibration report does not promote either retriever. SIE score reranking, anti-anchoring controls, and held-out evaluation remain separate gates.",
        "",
        "## Dense-only diagnostics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Safety-evaluable cases | {metrics.safety_evaluable_case_count} |",
        f"| Safe top-1 rate | {_value(metrics.safe_precedent_top_1_rate)} |",
        f"| False-operational matches | {metrics.false_operational_match_count}/{metrics.safety_evaluable_case_count} |",
        f"| p50 local cosine latency (ms) | {metrics.p50_similarity_latency_ms} |",
        f"| p95 local cosine latency (ms) | {metrics.p95_similarity_latency_ms} |",
        "",
        "## Case outcomes",
        "",
        "| Eval case | Expected state | Top candidates | First acceptable rank | Unsafe top-1 | Dense failure labels |",
        "|---|---|---|---:|---:|---|",
    ]
    for outcome in report.outcomes:
        candidates = ", ".join(outcome.candidate_ids) or "none"
        labels = ", ".join(outcome.failure_labels) or "none"
        first_rank = str(outcome.first_acceptable_rank) if outcome.first_acceptable_rank else "—"
        lines.append(
            f"| {outcome.eval_id} | {outcome.expected_decision_state} | {candidates} | {first_rank} | {str(outcome.top_1_is_unsafe).lower()} | {labels} |"
        )
    lines.extend(["", "## Known limits", ""])
    lines.extend(f"- {limit}" for limit in report.known_limits)
    lines.append("")
    return "\n".join(lines)


def _exact_precedent_interpretation(delta: float | None) -> str:
    if delta is None:
        return "Exact-precedent ranking could not be compared because one or both metrics were not applicable."
    if delta > 0:
        return f"Dense retrieval improved exact-precedent ranking by {delta:.4f} on this calibration set; this is not a promotion claim."
    if delta < 0:
        return f"Dense retrieval was lower on exact-precedent ranking by {abs(delta):.4f} on this calibration set; no exact-ranking improvement is claimed."
    return "Dense retrieval tied the keyword baseline on exact-precedent ranking for this calibration set."


def _incident_family_interpretation(delta: float | None) -> str:
    if delta is None:
        return "Incident-family Recall@5 could not be compared because one or both metrics were not applicable."
    if delta > 0:
        return f"Dense retrieval improved incident-family Recall@5 by {delta:.4f} on this calibration set; this is diagnostic evidence only."
    if delta < 0:
        return f"Dense retrieval was lower on incident-family Recall@5 by {abs(delta):.4f} on this calibration set."
    return "Dense retrieval tied the keyword baseline on incident-family Recall@5 for this calibration set."


def _safety_proxy_interpretation(delta: float | None) -> str:
    if delta is None:
        return "False-operational-match rate could not be compared because one or both metrics were not applicable."
    if delta < 0:
        return f"Dense retrieval reduced the calibration false-operational-match rate by {abs(delta):.4f}; this safety proxy still requires later policy and held-out evaluation."
    if delta > 0:
        return f"Dense retrieval increased the calibration false-operational-match rate by {delta:.4f}; do not treat it as a safety improvement."
    return "Dense retrieval tied the keyword baseline on calibration false-operational-match rate."


def _value(value: float | None) -> str:
    return str(value) if value is not None else "not applicable"
