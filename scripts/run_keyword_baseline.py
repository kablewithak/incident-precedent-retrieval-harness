"""Run the deterministic keyword baseline against calibration fixtures only."""

from __future__ import annotations

import argparse
from pathlib import Path

from incident_precedent_harness.retrieval import JsonDatasetRepository, KeywordRetriever
from incident_precedent_harness.retrieval.reporting import run_keyword_baseline, write_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run deterministic lexical retrieval on calibration fixtures."
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing data/, docs/, and evidence_vault/.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of ranked candidates to retain per calibration case.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.top_k < 1:
        raise SystemExit("--top-k must be at least 1")
    root = args.repository_root.resolve()
    repository = JsonDatasetRepository(root)
    incidents = repository.load_incidents()
    cases = repository.load_calibration_cases()
    report = run_keyword_baseline(
        retriever=KeywordRetriever(incidents),
        cases=cases,
        top_k=args.top_k,
    )
    write_report(
        report,
        json_path=root / "evidence_vault" / "reports" / "keyword-baseline-calibration.json",
        markdown_path=root / "docs" / "reports" / "keyword-baseline-calibration.md",
    )
    print(
        "Keyword baseline complete: "
        f"{report.corpus_incident_count} incidents, "
        f"{report.calibration_case_count} calibration cases, "
        f"MRR={report.metrics.correct_precedent_mrr}, "
        f"false_operational_match_rate={report.metrics.false_operational_match_rate}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
