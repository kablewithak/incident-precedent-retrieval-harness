"""Calibration-only reporting for bounded keyword-plus-dense SIE score reranking."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from incident_precedent_harness.domain.incident_data import EvalCase, HistoricalIncidentCard
from incident_precedent_harness.inference.models import EmbeddingRequest, InferenceProfile, TextItem
from incident_precedent_harness.inference.protocol import SemanticInferenceClient
from incident_precedent_harness.retrieval.dense import DenseRetriever
from incident_precedent_harness.retrieval.hybrid import (
    HybridCandidatePoolBuilder,
    HybridTopKReranker,
)
from incident_precedent_harness.retrieval.keyword import KeywordRetriever
from incident_precedent_harness.retrieval.models import (
    DenseRerankMetrics,
    DenseRetrievalMetrics,
    KeywordBaselineMetrics,
)
from incident_precedent_harness.retrieval.rerank_reporting import run_dense_rerank_calibration

PositiveInteger = Annotated[int, Field(ge=1)]
NonNegativeFloat = Annotated[float, Field(ge=0)]


class HybridRerankCaseOutcome(BaseModel):
    """One calibration-only hybrid candidate-pool and rerank outcome."""

    eval_id: str = Field(min_length=1)
    expected_decision_state: str
    keyword_candidate_ids: tuple[str, ...]
    dense_candidate_ids: tuple[str, ...]
    hybrid_seed_candidate_ids: tuple[str, ...]
    reranked_candidate_ids: tuple[str, ...]
    reranked_candidate_incident_families: tuple[str, ...]
    acceptable_precedent_ids: tuple[str, ...]
    unsafe_precedent_ids: tuple[str, ...]
    first_acceptable_rank: int | None = Field(default=None, ge=1)
    top_1_is_unsafe: bool
    score_latency_ms: NonNegativeFloat
    failure_labels: tuple[str, ...] = ()


class HybridRerankMetrics(BaseModel):
    """Metrics for a bounded hybrid candidate union after SIE score reranking."""

    scored_case_count: int = Field(ge=0)
    cases_with_acceptable_precedent: int = Field(ge=0)
    correct_precedent_mrr: float | None = Field(default=None, ge=0, le=1)
    incident_family_recall_at_5: float | None = Field(default=None, ge=0, le=1)
    safety_evaluable_case_count: int = Field(ge=0)
    safe_precedent_top_1_rate: float | None = Field(default=None, ge=0, le=1)
    false_operational_match_count: int = Field(ge=0)
    false_operational_match_rate: float | None = Field(default=None, ge=0, le=1)
    p50_score_latency_ms: NonNegativeFloat
    p95_score_latency_ms: NonNegativeFloat
    p50_seed_candidate_count: NonNegativeFloat
    p95_seed_candidate_count: NonNegativeFloat


class FourWayRetrievalComparison(BaseModel):
    """Calibration-only comparison. This is not a promotion decision."""

    keyword_correct_precedent_mrr: float | None = Field(default=None, ge=0, le=1)
    dense_correct_precedent_mrr: float | None = Field(default=None, ge=0, le=1)
    dense_reranked_correct_precedent_mrr: float | None = Field(default=None, ge=0, le=1)
    hybrid_reranked_correct_precedent_mrr: float | None = Field(default=None, ge=0, le=1)
    hybrid_mrr_delta_vs_keyword: float | None = None
    hybrid_mrr_delta_vs_dense: float | None = None
    hybrid_mrr_delta_vs_dense_rerank: float | None = None
    keyword_false_operational_match_rate: float | None = Field(default=None, ge=0, le=1)
    dense_false_operational_match_rate: float | None = Field(default=None, ge=0, le=1)
    dense_reranked_false_operational_match_rate: float | None = Field(default=None, ge=0, le=1)
    hybrid_reranked_false_operational_match_rate: float | None = Field(default=None, ge=0, le=1)
    hybrid_false_operational_match_rate_delta_vs_keyword: float | None = None
    hybrid_false_operational_match_rate_delta_vs_dense: float | None = None
    hybrid_false_operational_match_rate_delta_vs_dense_rerank: float | None = None


class HybridRerankCalibrationReport(BaseModel):
    """Saved evidence for bounded hybrid retrieval plus SIE score reranking."""

    report_kind: Literal["local_sie_hybrid_rerank_calibration"] = (
        "local_sie_hybrid_rerank_calibration"
    )
    generated_at: datetime
    corpus_incident_count: PositiveInteger
    calibration_case_count: PositiveInteger
    keyword_top_k: PositiveInteger
    dense_top_k: PositiveInteger
    hybrid_max_candidates: PositiveInteger
    evaluation_top_k: PositiveInteger
    query_embedding_profile: InferenceProfile
    score_profile: InferenceProfile
    query_embedding_batch_latency_ms: NonNegativeFloat
    keyword_baseline_metrics: KeywordBaselineMetrics
    dense_metrics: DenseRetrievalMetrics
    dense_rerank_metrics: DenseRerankMetrics
    hybrid_rerank_metrics: HybridRerankMetrics
    comparison: FourWayRetrievalComparison
    outcomes: tuple[HybridRerankCaseOutcome, ...]
    known_limits: tuple[str, ...] = Field(min_length=1)


def run_hybrid_rerank_calibration(
    *,
    retriever: DenseRetriever,
    incidents: tuple[HistoricalIncidentCard, ...],
    client: SemanticInferenceClient,
    embedding_profile: InferenceProfile,
    score_profile: InferenceProfile,
    cases: tuple[EvalCase, ...],
    trace_id: UUID,
    keyword_top_k: int = 5,
    dense_top_k: int = 5,
) -> HybridRerankCalibrationReport:
    """Evaluate a bounded keyword-plus-dense union with score reranking.

    Existing keyword, dense, and dense-rerank metrics are recomputed through the
    established dense-rerank calibration boundary. The new hybrid path uses a
    separate, deterministic lexical-first union and can only score that union.
    """

    if keyword_top_k < 1 or keyword_top_k > 5:
        raise ValueError("keyword_top_k must be between 1 and 5")
    if dense_top_k < 1 or dense_top_k > 5:
        raise ValueError("dense_top_k must be between 1 and 5")

    dense_rerank_report = run_dense_rerank_calibration(
        retriever=retriever,
        incidents=incidents,
        client=client,
        embedding_profile=embedding_profile,
        score_profile=score_profile,
        cases=cases,
        trace_id=trace_id,
        top_k=dense_top_k,
    )

    query_items = tuple(TextItem(item_id=case.eval_id, text=case.input_summary) for case in cases)
    embedding_response = client.encode_incident_texts(
        EmbeddingRequest(
            trace_id=trace_id,
            profile=embedding_profile,
            items=query_items,
        )
    )
    vectors_by_eval_id = {
        vector.item_id: vector.dense_values for vector in embedding_response.vectors
    }
    expected_ids = {case.eval_id for case in cases}
    if set(vectors_by_eval_id) != expected_ids or len(vectors_by_eval_id) != len(expected_ids):
        raise ValueError("query embedding identities did not match calibration case IDs")

    keyword_retriever = KeywordRetriever(incidents)
    incident_families = retriever.incident_families_by_id
    pool_builder = HybridCandidatePoolBuilder(
        maximum_candidates=keyword_top_k + dense_top_k
    )
    reranker = HybridTopKReranker(incidents=incidents)
    outcomes: list[HybridRerankCaseOutcome] = []

    for case in cases:
        keyword_candidates = keyword_retriever.rank(
            case.input_summary,
            top_k=keyword_top_k,
        )
        dense_candidates = retriever.rank(
            vectors_by_eval_id[case.eval_id],
            top_k=dense_top_k,
        )
        hybrid_candidates = pool_builder.build(
            keyword_candidates=keyword_candidates,
            dense_candidates=dense_candidates,
        )
        reranked_candidates, score_latency_ms = reranker.rerank(
            query_text=case.input_summary,
            hybrid_candidates=hybrid_candidates,
            client=client,
            score_profile=score_profile,
            trace_id=trace_id,
        )
        reranked_ids = tuple(candidate.incident_id for candidate in reranked_candidates)
        first_acceptable_rank = _first_acceptable_rank(
            candidate_ids=reranked_ids,
            acceptable_precedent_ids=case.acceptable_precedent_ids,
            evaluation_top_k=dense_top_k,
        )
        unsafe_top_one = bool(
            reranked_ids and reranked_ids[0] in case.unsafe_precedent_ids
        )
        outcomes.append(
            HybridRerankCaseOutcome(
                eval_id=case.eval_id,
                expected_decision_state=case.expected_decision_state.value,
                keyword_candidate_ids=tuple(
                    candidate.incident_id for candidate in keyword_candidates
                ),
                dense_candidate_ids=tuple(
                    candidate.incident_id for candidate in dense_candidates
                ),
                hybrid_seed_candidate_ids=tuple(
                    candidate.incident_id for candidate in hybrid_candidates
                ),
                reranked_candidate_ids=reranked_ids,
                reranked_candidate_incident_families=tuple(
                    incident_families[incident_id] for incident_id in reranked_ids
                ),
                acceptable_precedent_ids=case.acceptable_precedent_ids,
                unsafe_precedent_ids=case.unsafe_precedent_ids,
                first_acceptable_rank=first_acceptable_rank,
                top_1_is_unsafe=unsafe_top_one,
                score_latency_ms=score_latency_ms,
                failure_labels=_failure_labels(
                    case=case,
                    first_acceptable_rank=first_acceptable_rank,
                    top_1_is_unsafe=unsafe_top_one,
                    candidates_returned=bool(reranked_ids),
                ),
            )
        )

    hybrid_metrics = _metrics(tuple(outcomes), incident_families)
    comparison = _comparison(
        keyword=dense_rerank_report.keyword_baseline_metrics,
        dense=dense_rerank_report.dense_metrics,
        dense_reranked=dense_rerank_report.rerank_metrics,
        hybrid=hybrid_metrics,
    )
    return HybridRerankCalibrationReport(
        generated_at=datetime.now(UTC),
        corpus_incident_count=len(incidents),
        calibration_case_count=len(cases),
        keyword_top_k=keyword_top_k,
        dense_top_k=dense_top_k,
        hybrid_max_candidates=pool_builder.maximum_candidates,
        evaluation_top_k=dense_top_k,
        query_embedding_profile=embedding_profile,
        score_profile=score_profile,
        query_embedding_batch_latency_ms=embedding_response.latency_ms,
        keyword_baseline_metrics=dense_rerank_report.keyword_baseline_metrics,
        dense_metrics=dense_rerank_report.dense_metrics,
        dense_rerank_metrics=dense_rerank_report.rerank_metrics,
        hybrid_rerank_metrics=hybrid_metrics,
        comparison=comparison,
        outcomes=tuple(outcomes),
        known_limits=(
            "Calibration-only report; held-out cases are not loaded or scored.",
            "The hybrid seed union contains only keyword top-k and dense top-k candidates.",
            "SIE score can reorder only the bounded hybrid seed union; it cannot introduce a new incident card.",
            "The lexical-first seed order is deterministic provenance, not a final ranking or policy preference.",
            "Dense-plus-rerank and hybrid-plus-rerank do not assign decision states, select an authoritative precedent, or authorize a procedure.",
            "Raw relevance values are provider-native ranking evidence, not calibrated probabilities or confidence values.",
            "A candidate returned for an insufficient-precedent case remains a retrieval limitation until a separate abstention policy is applied.",
            "This report is not a promotion decision; anti-anchoring policy and held-out evaluation remain separate gates.",
        ),
    )


def write_hybrid_rerank_report(
    report: HybridRerankCalibrationReport,
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write machine-readable and portable reviewer-facing evidence."""

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _first_acceptable_rank(
    *,
    candidate_ids: tuple[str, ...],
    acceptable_precedent_ids: tuple[str, ...],
    evaluation_top_k: int,
) -> int | None:
    """Return acceptable rank only within the common top-k evaluation cut."""
    return next(
        (
            rank
            for rank, incident_id in enumerate(candidate_ids[:evaluation_top_k], start=1)
            if incident_id in acceptable_precedent_ids
        ),
        None,
    )


def _failure_labels(
    *,
    case: EvalCase,
    first_acceptable_rank: int | None,
    top_1_is_unsafe: bool,
    candidates_returned: bool,
) -> tuple[str, ...]:
    labels: list[str] = []
    if case.acceptable_precedent_ids and first_acceptable_rank is None:
        labels.append("hybrid_retrieval_miss")
    if top_1_is_unsafe:
        labels.append("false_operational_match")
    if case.expected_decision_state.value == "insufficient_precedent" and candidates_returned:
        labels.append("hybrid_candidate_returned_without_abstention_policy")
    return tuple(labels)


def _metrics(
    outcomes: tuple[HybridRerankCaseOutcome, ...],
    incident_families: dict[str, str],
) -> HybridRerankMetrics:
    positive = tuple(outcome for outcome in outcomes if outcome.acceptable_precedent_ids)
    reciprocal_ranks = tuple(
        1 / outcome.first_acceptable_rank
        for outcome in positive
        if outcome.first_acceptable_rank is not None
    )
    family_recall = tuple(
        bool(
            {
                incident_families[incident_id]
                for incident_id in outcome.reranked_candidate_ids[:5]
            }.intersection(
                {
                    incident_families[incident_id]
                    for incident_id in outcome.acceptable_precedent_ids
                }
            )
        )
        for outcome in positive
    )
    safety_evaluable = tuple(outcome for outcome in outcomes if outcome.unsafe_precedent_ids)
    false_count = sum(outcome.top_1_is_unsafe for outcome in safety_evaluable)
    latencies = tuple(outcome.score_latency_ms for outcome in outcomes)
    seed_counts = tuple(len(outcome.hybrid_seed_candidate_ids) for outcome in outcomes)
    return HybridRerankMetrics(
        scored_case_count=len(outcomes),
        cases_with_acceptable_precedent=len(positive),
        correct_precedent_mrr=(
            round(sum(reciprocal_ranks) / len(positive), 4) if positive else None
        ),
        incident_family_recall_at_5=(
            round(sum(family_recall) / len(positive), 4) if positive else None
        ),
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
        false_operational_match_count=false_count,
        false_operational_match_rate=(
            round(false_count / len(safety_evaluable), 4)
            if safety_evaluable
            else None
        ),
        p50_score_latency_ms=round(_percentile(latencies, 0.5), 4),
        p95_score_latency_ms=round(_percentile(latencies, 0.95), 4),
        p50_seed_candidate_count=round(_percentile(seed_counts, 0.5), 4),
        p95_seed_candidate_count=round(_percentile(seed_counts, 0.95), 4),
    )


def _comparison(
    *,
    keyword: KeywordBaselineMetrics,
    dense: DenseRetrievalMetrics,
    dense_reranked: DenseRerankMetrics,
    hybrid: HybridRerankMetrics,
) -> FourWayRetrievalComparison:
    return FourWayRetrievalComparison(
        keyword_correct_precedent_mrr=keyword.correct_precedent_mrr,
        dense_correct_precedent_mrr=dense.correct_precedent_mrr,
        dense_reranked_correct_precedent_mrr=dense_reranked.correct_precedent_mrr,
        hybrid_reranked_correct_precedent_mrr=hybrid.correct_precedent_mrr,
        hybrid_mrr_delta_vs_keyword=_delta(
            hybrid.correct_precedent_mrr,
            keyword.correct_precedent_mrr,
        ),
        hybrid_mrr_delta_vs_dense=_delta(
            hybrid.correct_precedent_mrr,
            dense.correct_precedent_mrr,
        ),
        hybrid_mrr_delta_vs_dense_rerank=_delta(
            hybrid.correct_precedent_mrr,
            dense_reranked.correct_precedent_mrr,
        ),
        keyword_false_operational_match_rate=keyword.false_operational_match_rate,
        dense_false_operational_match_rate=dense.false_operational_match_rate,
        dense_reranked_false_operational_match_rate=(
            dense_reranked.false_operational_match_rate
        ),
        hybrid_reranked_false_operational_match_rate=(
            hybrid.false_operational_match_rate
        ),
        hybrid_false_operational_match_rate_delta_vs_keyword=_delta(
            hybrid.false_operational_match_rate,
            keyword.false_operational_match_rate,
        ),
        hybrid_false_operational_match_rate_delta_vs_dense=_delta(
            hybrid.false_operational_match_rate,
            dense.false_operational_match_rate,
        ),
        hybrid_false_operational_match_rate_delta_vs_dense_rerank=_delta(
            hybrid.false_operational_match_rate,
            dense_reranked.false_operational_match_rate,
        ),
    )


def _delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(left - right, 4)


def _percentile(values: tuple[float, ...] | tuple[int, ...], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return float(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction)


def _render_markdown(report: HybridRerankCalibrationReport) -> str:
    comparison = report.comparison
    metrics = report.hybrid_rerank_metrics
    lines = [
        "# Local SIE Hybrid + Score Rerank Calibration Report",
        "",
        "## Scope",
        "",
        "This report compares keyword retrieval, local-SIE dense retrieval, dense-plus-SIE-score reranking, and a bounded hybrid candidate union with SIE score reranking on calibration fixtures only.",
        "It does not score held-out cases, assign product decision states, select an authoritative precedent, authorize procedures, or constitute a promotion decision.",
        "",
        "## Hybrid boundary",
        "",
        f"- Keyword candidates per case: `{report.keyword_top_k}`",
        f"- Dense candidates per case: `{report.dense_top_k}`",
        f"- Maximum score candidates per case: `{report.hybrid_max_candidates}`",
        f"- Common metric evaluation cut: top `{report.evaluation_top_k}`",
        "- Seed union order: keyword rank order, then dense-only candidates in dense rank order.",
        "- SIE score cannot add an incident card absent from the hybrid seed union.",
        "- Provider raw relevance values are not confidence values; provider rank governs reranked ordering.",
        "",
        "## Calibration comparison",
        "",
        "| Metric | Keyword | Dense | Dense + SIE score | Hybrid + SIE score | Hybrid minus keyword | Hybrid minus dense + score |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| Correct-precedent MRR | {_value(comparison.keyword_correct_precedent_mrr)} | {_value(comparison.dense_correct_precedent_mrr)} | {_value(comparison.dense_reranked_correct_precedent_mrr)} | {_value(comparison.hybrid_reranked_correct_precedent_mrr)} | {_value(comparison.hybrid_mrr_delta_vs_keyword)} | {_value(comparison.hybrid_mrr_delta_vs_dense_rerank)} |",
        f"| False-operational-match rate | {_value(comparison.keyword_false_operational_match_rate)} | {_value(comparison.dense_false_operational_match_rate)} | {_value(comparison.dense_reranked_false_operational_match_rate)} | {_value(comparison.hybrid_reranked_false_operational_match_rate)} | {_value(comparison.hybrid_false_operational_match_rate_delta_vs_keyword)} | {_value(comparison.hybrid_false_operational_match_rate_delta_vs_dense_rerank)} |",
        "",
        "## Calibration interpretation",
        "",
        f"- {_interpret_mrr(comparison)}",
        f"- {_interpret_safety(comparison)}",
        "- Decision: this calibration report does not promote any retrieval path. Anti-anchoring policy and held-out evaluation remain separate gates.",
        "",
        "## Hybrid-only diagnostics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| False-operational matches | {metrics.false_operational_match_count}/{metrics.safety_evaluable_case_count} |",
        f"| p50 SIE score latency (ms) | {metrics.p50_score_latency_ms} |",
        f"| p95 SIE score latency (ms) | {metrics.p95_score_latency_ms} |",
        f"| p50 seed candidate count | {metrics.p50_seed_candidate_count} |",
        f"| p95 seed candidate count | {metrics.p95_seed_candidate_count} |",
        "",
        "## Case outcomes",
        "",
        "| Eval case | Keyword top-k | Dense top-k | Hybrid seed | Reranked top-k | First acceptable rank | Unsafe top-1 | Failure labels |",
        "|---|---|---|---|---|---:|---:|---|",
    ]
    for outcome in report.outcomes:
        lines.append(
            "| "
            + " | ".join(
                (
                    outcome.eval_id,
                    ", ".join(outcome.keyword_candidate_ids) or "none",
                    ", ".join(outcome.dense_candidate_ids) or "none",
                    ", ".join(outcome.hybrid_seed_candidate_ids) or "none",
                    ", ".join(outcome.reranked_candidate_ids) or "none",
                    str(outcome.first_acceptable_rank)
                    if outcome.first_acceptable_rank is not None
                    else "N/A",
                    str(outcome.top_1_is_unsafe).lower(),
                    ", ".join(outcome.failure_labels) or "none",
                )
            )
            + " |"
        )
    lines.extend(["", "## Known limits", ""])
    lines.extend(f"- {limit}" for limit in report.known_limits)
    lines.append("")
    return "\n".join(lines)


def _value(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.4f}"


def _interpret_mrr(comparison: FourWayRetrievalComparison) -> str:
    delta = comparison.hybrid_mrr_delta_vs_dense_rerank
    if delta is None:
        return "Hybrid exact-precedent ranking could not be compared because one or both metrics were not applicable."
    if delta > 0:
        return f"Hybrid-plus-rerank improved exact-precedent ranking by {delta:.4f} relative to dense-plus-rerank on this calibration set; this is not a promotion claim."
    if delta < 0:
        return f"Hybrid-plus-rerank was lower on exact-precedent ranking by {abs(delta):.4f} relative to dense-plus-rerank on this calibration set; no improvement is claimed."
    return "Hybrid-plus-rerank tied dense-plus-rerank on exact-precedent ranking for this calibration set."


def _interpret_safety(comparison: FourWayRetrievalComparison) -> str:
    delta = comparison.hybrid_false_operational_match_rate_delta_vs_dense_rerank
    if delta is None:
        return "Hybrid safety proxy could not be compared because one or both metrics were not applicable."
    if delta < 0:
        return f"Hybrid-plus-rerank reduced the false-operational-match rate by {abs(delta):.4f} relative to dense-plus-rerank on this calibration set; later policy and held-out evaluation remain required."
    if delta > 0:
        return f"Hybrid-plus-rerank increased the false-operational-match rate by {delta:.4f} relative to dense-plus-rerank on this calibration set; it is not eligible for promotion."
    return "Hybrid-plus-rerank tied dense-plus-rerank on the false-operational-match rate for this calibration set."
