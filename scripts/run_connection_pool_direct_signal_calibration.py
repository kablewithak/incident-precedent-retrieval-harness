"""Record the calibration-only direct connection-pool signal intervention."""

from __future__ import annotations

import argparse
from pathlib import Path

from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.decisions.reporting import run_policy_calibration, write_report
from incident_precedent_harness.retrieval import JsonDatasetRepository, KeywordRetriever


REPORT_STEM = "connection-pool-direct-signal-calibration"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the calibration-only connection-pool direct-signal intervention. "
            "This command does not load held-out cases."
        )
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
        help="Number of lexical candidates sent to the policy.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.top_k < 1:
        raise SystemExit("--top-k must be at least 1")

    root = args.repository_root.resolve()
    repository = JsonDatasetRepository(root)
    incidents = repository.load_incidents()
    procedures = repository.load_procedures()
    cases = repository.load_calibration_cases()

    report = run_policy_calibration(
        retriever=KeywordRetriever(incidents),
        policy=AntiAnchoringDecisionPolicy(),
        incidents=incidents,
        procedures=procedures,
        cases=cases,
        top_k=args.top_k,
    )
    write_report(
        report,
        json_path=root / "evidence_vault" / "reports" / f"{REPORT_STEM}.json",
        markdown_path=root / "docs" / "reports" / f"{REPORT_STEM}.md",
    )
    print(
        "Connection-pool direct-signal calibration complete: "
        f"decision_state_accuracy={report.metrics.decision_state_accuracy}, "
        f"false_operational_matches={report.metrics.false_operational_match_count}, "
        f"unsafe_procedures={report.metrics.unsafe_procedure_surfacing_count}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
