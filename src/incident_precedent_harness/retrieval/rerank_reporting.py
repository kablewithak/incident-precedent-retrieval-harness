"""Calibration-only evidence for dense top-k retrieval plus SIE score reranking."""

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
    DenseRerankCalibrationReport,
    DenseRerankCaseOutcome,
    DenseRerankMetrics,
    DenseRetrievalMetrics,
    KeywordBaselineMetrics,
    ThreeWayRetrievalComparison,
)
from incident_precedent_harness.retrieval.reporting import run_keyword_baseline
from incident_precedent_harness.retrieval.rerank import DenseTopKReranker


def run_dense_rerank_calibration(
    *,
    retriever: DenseRetriever,
    incidents: tuple[HistoricalIncidentCard, ...],
    client: SemanticInferenceClient,
    embedding_profile: InferenceProfile,
    score_profile: InferenceProfile,
    cases: tuple[EvalCase, ...],
    trace_id: UUID,
    top_k: int = 5,
) -> DenseRerankCalibrationReport:
    """Compare keyword, dense, and dense-plus-rerank on calibration only."""

    if top_k < 1 or top_k > 10:
        raise ValueError("top_k must be between 1 and 10 for bounded score reranking")

    query_items = tuple(TextItem(item_id=case.eval_id, text=case.input_summary) for case in cases)
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
    reranker = DenseTopKReranker(incidents=incidents)
    dense_outcomes: list[DenseCaseOutcome] = []
    rerank_outcomes: list[DenseRerankCaseOutcome] = []

    for case in cases:
        dense_candidates, similarity_latency_ms = retriever.rank_with_latency(
            vectors_by_eval_id[case.eval_id],
            top_k=top_k,
        )
        dense_candidate_ids = tuple(candidate.incident_id for candidate in dense_candidates)
        dense_candidate_families = tuple(
            incident_families[incident_id] for incident_id in dense_candidate_ids
        )
        expected_families = _expected_families(case=case, incident_families=incident_families)
        dense_first_acceptable_rank = _first_acceptable_rank(
            candidate_ids=dense_candidate_ids,
            acceptable_precedent_ids=case.acceptable_precedent_ids,
        )
        dense_top_1_is_unsafe = bool(
            dense_candidate_ids and dense_candidate_ids[0] in case.unsafe_precedent_ids
        )
        dense_outcomes.append(
            DenseCaseOutcome(
                eval_id=case.eval_id,
                expected_decision_state=case.expected_decision_state.value,
                candidate_ids=dense_candidate_ids,
                candidate_incident_families=dense_candidate_families,
                expected_incident_families=expected_families,
                acceptable_precedent_ids=case.acceptable_precedent_ids,
                unsafe_precedent_ids=case.unsafe_precedent_ids,
                first_acceptable_rank=dense_first_acceptable_rank,
                top_1_is_unsafe=dense_top_1_is_unsafe,
                similarity_latency_ms=similarity_latency_ms,
                failure_labels=_dense_labels(
                    case=case,
                    first_acceptable_rank=dense_first_acceptable_rank,
                    top_1_is_unsafe=dense_top_1_is_unsafe,
                    candidates_returned=bool(dense_candidate_ids),
                ),
            )
        )

        reranked_candidates, score_latency_ms = reranker.rerank(
            query_text=case.input_summary,
            dense_candidates=dense_candidates,
            client=client,
            score_profile=score_profile,
            trace_id=trace_id,
        )
        reranked_candidate_ids = tuple(candidate.incident_id for candidate in reranked_candidates)
        rerank_first_acceptable_rank = _first_acceptable_rank(
            candidate_ids=reranked_candidate_ids,
            acceptable_precedent_ids=case.acceptable_precedent_ids,
        )
        rerank_top_1_is_unsafe = bool(
            reranked_candidate_ids and reranked_candidate_ids[0] in case.unsafe_precedent_ids
        )
        rerank_outcomes.append(
            DenseRerankCaseOutcome(
                eval_id=case.eval_id,
                expected_decision_state=case.expected_decision_state.value,
                dense_candidate_ids=dense_candidate_ids,
                reranked_candidate_ids=reranked_candidate_ids,
                reranked_candidate_incident_families=tuple(
                    incident_families[incident_id] for incident_id in reranked_candidate_ids
                ),
                expected_incident_families=expected_families,
                acceptable_precedent_ids=case.acceptable_precedent_ids,
                unsafe_precedent_ids=case.unsafe_precedent_ids,
                first_acceptable_rank=rerank_first_acceptable_rank,
                top_1_is_unsafe=rerank_top_1_is_unsafe,
                score_latency_ms=score_latency_ms,
                failure_labels=_rerank_labels(
                    case=case,
                    first_acceptable_rank=rerank_first_acceptable_rank,
                    top_1_is_unsafe=rerank_top_1_is_unsafe,
                    candidates_returned=bool(reranked_candidate_ids),
                ),
            )
        )

    dense_metrics = _dense_metrics(tuple(dense_outcomes))
    rerank_metrics = _rerank_metrics(tuple(rerank_outcomes))
    keyword_metrics = run_keyword_baseline(
        retriever=KeywordRetriever(incidents),
        cases=cases,
        top_k=top_k,
    ).metrics

    return DenseRerankCalibrationReport(
        generated_at=datetime.now(UTC),
        corpus_incident_count=len(incidents),
        calibration_case_count=len(cases),
        dense_top_k=top_k,
        index_manifest=retriever.index_manifest,
        query_embedding_profile=embedding_profile,
        score_profile=score_profile,
        query_embedding_batch_latency_ms=embedding_response.latency_ms,
        dense_metrics=dense_metrics,
        rerank_metrics=rerank_metrics,
        keyword_baseline_metrics=keyword_metrics,
        comparison=_three_way_comparison(
            keyword=keyword_metrics,
            dense=dense_metrics,
            reranked=rerank_metrics,
        ),
        outcomes=tuple(rerank_outcomes),
        known_limits=(
            "Calibration-only report; held-out cases are not loaded or scored.",
            "SIE score can reorder only the dense top-k candidate set; it cannot introduce a new incident card.",
            "Dense-plus-rerank does not assign decision states, select an authoritative precedent, or authorize a procedure.",
            "Raw relevance values are provider-native ranking evidence, not calibrated probabilities or confidence values.",
            "A candidate returned for an insufficient-precedent case remains a retrieval limitation until a separate abstention policy is applied.",
            "Observed provider score latency is synthetic calibration evidence, not a warm-operation or production latency claim.",
            "This report is not a promotion decision; anti-anchoring policy and held-out evaluation remain separate gates.",
        ),
    )


def write_dense_rerank_report(
    report: DenseRerankCalibrationReport,
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write machine-readable and reviewer-readable rerank calibration evidence."""

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _expected_families(*, case: EvalCase, incident_families: dict[str, str]) -> tuple[str, ...]:
    return tuple(
        sorted({incident_families[incident_id] for incident_id in case.acceptable_precedent_ids})
    )


def _first_acceptable_rank(
    *,
    candidate_ids: tuple[str, ...],
    acceptable_precedent_ids: tuple[str, ...],
) -> int | None:
    return next(
        (
            rank
            for rank, incident_id in enumerate(candidate_ids, start=1)
            if incident_id in acceptable_precedent_ids
        ),
        None,
    )


def _dense_labels(
    *,
    case: EvalCase,
    first_acceptable_rank: int | None,
    top_1_is_unsafe: bool,
    candidates_returned: bool,
) -> tuple[str, ...]:
    labels: list[str] = []
    if case.acceptable_precedent_ids and first_acceptable_rank is None:
        labels.append("retrieval_miss")
    if top_1_is_unsafe:
        labels.append("false_operational_match")
    if case.expected_decision_state.value == "insufficient_precedent" and candidates_returned:
        labels.append("dense_candidate_returned_without_abstention_policy")
    return tuple(labels)


def _rerank_labels(
    *,
    case: EvalCase,
    first_acceptable_rank: int | None,
    top_1_is_unsafe: bool,
    candidates_returned: bool,
) -> tuple[str, ...]:
    labels = list(
        _dense_labels(
            case=case,
            first_acceptable_rank=first_acceptable_rank,
            top_1_is_unsafe=top_1_is_unsafe,
            candidates_returned=candidates_returned,
        )
    )
    if case.expected_decision_state.value == "insufficient_precedent" and candidates_returned:
        labels[-1] = "rerank_candidate_returned_without_abstention_policy"
    return tuple(labels)


def _dense_metrics(outcomes: tuple[DenseCaseOutcome, ...]) -> DenseRetrievalMetrics:
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
    false_count = sum(outcome.top_1_is_unsafe for outcome in safety_evaluable)
    latencies = tuple(outcome.similarity_latency_ms for outcome in outcomes)
    return DenseRetrievalMetrics(
        scored_case_count=len(outcomes),
        cases_with_acceptable_precedent=len(positive),
        correct_precedent_mrr=_mean_reciprocal_rank(reciprocal_ranks, len(positive)),
        incident_family_recall_at_5=_mean_booleans(recall_at_five, len(positive)),
        safety_evaluable_case_count=len(safety_evaluable),
        safe_precedent_top_1_rate=_safe_top_one_rate(safety_evaluable),
        false_operational_match_count=false_count,
        false_operational_match_rate=_rate(false_count, len(safety_evaluable)),
        p50_similarity_latency_ms=round(_percentile(latencies, 0.5), 4),
        p95_similarity_latency_ms=round(_percentile(latencies, 0.95), 4),
    )


def _rerank_metrics(outcomes: tuple[DenseRerankCaseOutcome, ...]) -> DenseRerankMetrics:
    positive = tuple(outcome for outcome in outcomes if outcome.acceptable_precedent_ids)
    reciprocal_ranks = tuple(
        1 / outcome.first_acceptable_rank
        for outcome in positive
        if outcome.first_acceptable_rank is not None
    )
    recall_at_five = tuple(
        bool(
            set(outcome.reranked_candidate_incident_families).intersection(
                outcome.expected_incident_families
            )
        )
        for outcome in positive
    )
    safety_evaluable = tuple(outcome for outcome in outcomes if outcome.unsafe_precedent_ids)
    false_count = sum(outcome.top_1_is_unsafe for outcome in safety_evaluable)
    latencies = tuple(outcome.score_latency_ms for outcome in outcomes)
    return DenseRerankMetrics(
        scored_case_count=len(outcomes),
        cases_with_acceptable_precedent=len(positive),
        correct_precedent_mrr=_mean_reciprocal_rank(reciprocal_ranks, len(positive)),
        incident_family_recall_at_5=_mean_booleans(recall_at_five, len(positive)),
        safety_evaluable_case_count=len(safety_evaluable),
        safe_precedent_top_1_rate=_safe_top_one_rate(safety_evaluable),
        false_operational_match_count=false_count,
        false_operational_match_rate=_rate(false_count, len(safety_evaluable)),
        p50_score_latency_ms=round(_percentile(latencies, 0.5), 4),
        p95_score_latency_ms=round(_percentile(latencies, 0.95), 4),
    )


def _mean_reciprocal_rank(values: tuple[float, ...], denominator: int) -> float | None:
    return round(sum(values) / denominator, 4) if denominator else None


def _mean_booleans(values: tuple[bool, ...], denominator: int) -> float | None:
    return round(sum(values) / denominator, 4) if denominator else None


def _safe_top_one_rate(outcomes: tuple[object, ...]) -> float | None:
    if not outcomes:
        return None
    safe_count = sum(not bool(getattr(outcome, "top_1_is_unsafe")) for outcome in outcomes)
    return round(safe_count / len(outcomes), 4)


def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


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


def _three_way_comparison(
    *,
    keyword: KeywordBaselineMetrics,
    dense: DenseRetrievalMetrics,
    reranked: DenseRerankMetrics,
) -> ThreeWayRetrievalComparison:
    return ThreeWayRetrievalComparison(
        keyword_correct_precedent_mrr=keyword.correct_precedent_mrr,
        dense_correct_precedent_mrr=dense.correct_precedent_mrr,
        reranked_correct_precedent_mrr=reranked.correct_precedent_mrr,
        reranked_correct_precedent_mrr_delta_vs_dense=_delta(
            reranked.correct_precedent_mrr, dense.correct_precedent_mrr
        ),
        reranked_correct_precedent_mrr_delta_vs_keyword=_delta(
            reranked.correct_precedent_mrr, keyword.correct_precedent_mrr
        ),
        keyword_incident_family_recall_at_5=keyword.incident_family_recall_at_5,
        dense_incident_family_recall_at_5=dense.incident_family_recall_at_5,
        reranked_incident_family_recall_at_5=reranked.incident_family_recall_at_5,
        reranked_incident_family_recall_at_5_delta_vs_dense=_delta(
            reranked.incident_family_recall_at_5, dense.incident_family_recall_at_5
        ),
        reranked_incident_family_recall_at_5_delta_vs_keyword=_delta(
            reranked.incident_family_recall_at_5, keyword.incident_family_recall_at_5
        ),
        keyword_false_operational_match_rate=keyword.false_operational_match_rate,
        dense_false_operational_match_rate=dense.false_operational_match_rate,
        reranked_false_operational_match_rate=reranked.false_operational_match_rate,
        reranked_false_operational_match_rate_delta_vs_dense=_delta(
            reranked.false_operational_match_rate, dense.false_operational_match_rate
        ),
        reranked_false_operational_match_rate_delta_vs_keyword=_delta(
            reranked.false_operational_match_rate, keyword.false_operational_match_rate
        ),
    )


def _delta(left: float | None, right: float | None) -> float | None:
    return round(left - right, 4) if left is not None and right is not None else None


def _render_markdown(report: DenseRerankCalibrationReport) -> str:
    dense = report.dense_metrics
    reranked = report.rerank_metrics
    keyword = report.keyword_baseline_metrics
    comparison = report.comparison
    manifest = report.index_manifest
    lines = [
        "# Local SIE Dense + Score Rerank Calibration Report",
        "",
        "## Scope",
        "",
        "This report compares deterministic keyword retrieval, local-SIE dense retrieval, and SIE score reranking of the fixed dense top-k on calibration fixtures only.",
        "It does not score held-out cases, assign product decision states, select an authoritative precedent, authorize procedures, or constitute a promotion decision.",
        "",
        "## Rerank boundary",
        "",
        f"- Dense top-k: `{report.dense_top_k}`",
        "- SIE score can reorder only those already-retrieved dense candidates.",
        "- The reranker cannot add an incident card absent from dense top-k.",
        "- Provider raw relevance values are not confidence values; provider rank governs ordering.",
        "",
        "## Index and provider binding",
        "",
        f"- Index ID: `{manifest.index_id}`",
        f"- Corpus cards: `{manifest.corpus_incident_count}`",
        f"- Corpus fingerprint: `{manifest.corpus_fingerprint_sha256}`",
        f"- Encode profile: `{report.query_embedding_profile.profile_id}`",
        f"- Encode model: `{report.query_embedding_profile.model_id}`",
        f"- Score profile: `{report.score_profile.profile_id}`",
        f"- Score model: `{report.score_profile.model_id}`",
        f"- Vector dimension: `{manifest.vector_dimension}`",
        f"- Query embedding batch latency (ms): `{report.query_embedding_batch_latency_ms}`",
        "",
        "## Calibration comparison",
        "",
        "| Metric | Keyword | Dense | Dense + SIE score | Rerank minus dense | Rerank minus keyword |",
        "|---|---:|---:|---:|---:|---:|",
        f"| Correct-precedent MRR | {_value(keyword.correct_precedent_mrr)} | {_value(dense.correct_precedent_mrr)} | {_value(reranked.correct_precedent_mrr)} | {_value(comparison.reranked_correct_precedent_mrr_delta_vs_dense)} | {_value(comparison.reranked_correct_precedent_mrr_delta_vs_keyword)} |",
        f"| Incident-family Recall@5 | {_value(keyword.incident_family_recall_at_5)} | {_value(dense.incident_family_recall_at_5)} | {_value(reranked.incident_family_recall_at_5)} | {_value(comparison.reranked_incident_family_recall_at_5_delta_vs_dense)} | {_value(comparison.reranked_incident_family_recall_at_5_delta_vs_keyword)} |",
        f"| False-operational-match rate | {_value(keyword.false_operational_match_rate)} | {_value(dense.false_operational_match_rate)} | {_value(reranked.false_operational_match_rate)} | {_value(comparison.reranked_false_operational_match_rate_delta_vs_dense)} | {_value(comparison.reranked_false_operational_match_rate_delta_vs_keyword)} |",
        "",
        "## Calibration interpretation",
        "",
        f"- {_metric_interpretation('Exact-precedent ranking', comparison.reranked_correct_precedent_mrr_delta_vs_dense, 'higher', 'dense retrieval')}",
        f"- {_metric_interpretation('False-operational-match rate', comparison.reranked_false_operational_match_rate_delta_vs_dense, 'lower', 'dense retrieval')}",
        "- Decision: this calibration report does not promote any retrieval path. Anti-anchoring policy and held-out evaluation remain separate gates.",
        "",
        "## Rerank-only diagnostics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Safety-evaluable cases | {reranked.safety_evaluable_case_count} |",
        f"| Safe top-1 rate | {_value(reranked.safe_precedent_top_1_rate)} |",
        f"| False-operational matches | {reranked.false_operational_match_count}/{reranked.safety_evaluable_case_count} |",
        f"| p50 SIE score latency (ms) | {reranked.p50_score_latency_ms} |",
        f"| p95 SIE score latency (ms) | {reranked.p95_score_latency_ms} |",
        "",
        "## Case outcomes",
        "",
        "| Eval case | Dense top-k | Reranked top-k | First acceptable rank | Unsafe top-1 | Rerank failure labels |",
        "|---|---|---|---:|---:|---|",
    ]
    for outcome in report.outcomes:
        dense_ids = ", ".join(outcome.dense_candidate_ids) or "none"
        reranked_ids = ", ".join(outcome.reranked_candidate_ids) or "none"
        labels = ", ".join(outcome.failure_labels) or "none"
        first_rank = str(outcome.first_acceptable_rank) if outcome.first_acceptable_rank else "N/A"
        lines.append(
            f"| {outcome.eval_id} | {dense_ids} | {reranked_ids} | {first_rank} | {str(outcome.top_1_is_unsafe).lower()} | {labels} |"
        )
    lines.extend(["", "## Known limits", ""])
    lines.extend(f"- {limit}" for limit in report.known_limits)
    lines.append("")
    return "\n".join(lines)


def _metric_interpretation(
    metric_name: str,
    delta: float | None,
    preferred_direction: str,
    baseline_name: str,
) -> str:
    if delta is None:
        return f"{metric_name} could not be compared with {baseline_name} because one or both metrics were not applicable."
    if delta == 0:
        return f"SIE score reranking tied {baseline_name} on {metric_name} for this calibration set."
    improvement = delta > 0 if preferred_direction == "higher" else delta < 0
    verb = "improved" if improvement else "was worse"
    return f"SIE score reranking {verb} than {baseline_name} on {metric_name} by {abs(delta):.4f} on this calibration set; this is diagnostic evidence only."


def _value(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.4f}"
