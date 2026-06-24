"""Calibration-only keyword-baseline reporting with explicit scope limits."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from incident_precedent_harness.domain.incident_data import EvalCase
from incident_precedent_harness.retrieval.keyword import KeywordRetriever
from incident_precedent_harness.retrieval.models import (
    KeywordBaselineMetrics,
    KeywordBaselineReport,
    KeywordCaseOutcome,
)


def run_keyword_baseline(
    *,
    retriever: KeywordRetriever,
    cases: tuple[EvalCase, ...],
    top_k: int = 5,
) -> KeywordBaselineReport:
    """Run a fixed calibration baseline without claiming decision-policy behavior."""

    outcomes: list[KeywordCaseOutcome] = []
    for case in cases:
        started = perf_counter()
        candidates = retriever.rank(case.input_summary, top_k=top_k)
        latency_ms = (perf_counter() - started) * 1000
        candidate_ids = tuple(candidate.incident_id for candidate in candidates)
        incident_families = retriever.incident_families_by_id
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
        failure_labels: list[str] = []
        if case.acceptable_precedent_ids and first_acceptable_rank is None:
            failure_labels.append("retrieval_miss")
        if top_1_is_unsafe:
            failure_labels.append("false_operational_match")
        if case.expected_decision_state.value == "insufficient_precedent" and candidate_ids:
            failure_labels.append("lexical_candidate_returned_without_abstention_policy")
        outcomes.append(
            KeywordCaseOutcome(
                eval_id=case.eval_id,
                expected_decision_state=case.expected_decision_state.value,
                candidate_ids=candidate_ids,
                candidate_incident_families=candidate_incident_families,
                expected_incident_families=expected_incident_families,
                acceptable_precedent_ids=case.acceptable_precedent_ids,
                unsafe_precedent_ids=case.unsafe_precedent_ids,
                first_acceptable_rank=first_acceptable_rank,
                top_1_is_unsafe=top_1_is_unsafe,
                query_latency_ms=round(latency_ms, 4),
                failure_labels=tuple(failure_labels),
            )
        )

    return KeywordBaselineReport(
        generated_at=datetime.now(UTC),
        corpus_incident_count=len(retriever._documents),
        calibration_case_count=len(cases),
        top_k=top_k,
        tokenization=retriever.tokenization_name,
        ranking_algorithm=retriever.algorithm_name,
        metrics=_metrics(tuple(outcomes)),
        outcomes=tuple(outcomes),
        known_limits=(
            "Calibration-only report; held-out cases are not loaded or scored.",
            "Lexical ranking does not assign a final decision state.",
            "Lexical ranking does not surface or authorize a candidate investigation procedure.",
            "A candidate returned for an insufficient-precedent case is recorded as a baseline limitation, not treated as acceptable evidence.",
            "Latency reflects local in-memory lexical ranking only; it is not a live-provider latency claim.",
        ),
    )


def write_report(report: KeywordBaselineReport, *, json_path: Path, markdown_path: Path) -> None:
    """Write machine-readable and reviewer-readable report artifacts."""

    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")


def _metrics(outcomes: tuple[KeywordCaseOutcome, ...]) -> KeywordBaselineMetrics:
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
    latencies = tuple(outcome.query_latency_ms for outcome in outcomes)

    return KeywordBaselineMetrics(
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
        p50_query_latency_ms=round(_percentile(latencies, 0.5), 4),
        p95_query_latency_ms=round(_percentile(latencies, 0.95), 4),
    )


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


def _render_markdown(report: KeywordBaselineReport) -> str:
    metrics = report.metrics
    lines = [
        "# Keyword Baseline Calibration Report",
        "",
        "## Scope",
        "",
        "This report measures deterministic lexical ranking on the calibration split only.",
        "It does not assign product decision states, surface procedures, or establish safe operational applicability.",
        "",
        "## Configuration",
        "",
        f"- Corpus incident cards: `{report.corpus_incident_count}`",
        f"- Calibration cases: `{report.calibration_case_count}`",
        f"- Top K: `{report.top_k}`",
        f"- Tokenization: {report.tokenization}",
        f"- Ranking: {report.ranking_algorithm}",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Correct-precedent MRR | {metrics.correct_precedent_mrr if metrics.correct_precedent_mrr is not None else 'not applicable'} |",
        f"| Incident-family Recall@5 | {metrics.incident_family_recall_at_5 if metrics.incident_family_recall_at_5 is not None else 'not applicable'} |",
        f"| Safety-evaluable cases | {metrics.safety_evaluable_case_count} |",
        f"| Safe top-1 rate | {metrics.safe_precedent_top_1_rate if metrics.safe_precedent_top_1_rate is not None else 'not applicable'} |",
        f"| False-operational matches | {metrics.false_operational_match_count}/{metrics.safety_evaluable_case_count} |",
        f"| False-operational-match rate | {metrics.false_operational_match_rate if metrics.false_operational_match_rate is not None else 'not applicable'} |",
        f"| p50 lexical query latency (ms) | {metrics.p50_query_latency_ms} |",
        f"| p95 lexical query latency (ms) | {metrics.p95_query_latency_ms} |",
        "",
        "## Case outcomes",
        "",
        "| Eval case | Expected state | Top candidates | First acceptable rank | Unsafe top-1 | Baseline failure labels |",
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
