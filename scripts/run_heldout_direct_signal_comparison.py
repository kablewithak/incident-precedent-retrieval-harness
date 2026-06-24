"""Compare ADR-0008 against the immutable held-out keyword-policy baseline once."""

from __future__ import annotations

import argparse
from pathlib import Path

from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.evaluation.comparison import (
    COMPARISON_JSON_RELATIVE_PATH,
    COMPARISON_MARKDOWN_RELATIVE_PATH,
    HANDOVER_MARKDOWN_RELATIVE_PATH,
    HeldoutComparisonIntegrityError,
    build_heldout_direct_signal_comparison,
    write_heldout_direct_signal_comparison,
)
from incident_precedent_harness.retrieval import JsonDatasetRepository, KeywordRetriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one documented comparison of ADR-0008 against the immutable "
            "Held-Out Tranche 01 baseline. The command preserves baseline evidence "
            "and refuses to overwrite comparison artifacts."
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
        help="Number of lexical candidates passed to the policy for provider-available cases.",
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
    cases = repository.load_heldout_cases()

    try:
        report = build_heldout_direct_signal_comparison(
            repository_root=root,
            retriever=KeywordRetriever(incidents),
            policy=AntiAnchoringDecisionPolicy(),
            incidents=incidents,
            procedures=procedures,
            cases=cases,
            top_k=args.top_k,
        )
        write_heldout_direct_signal_comparison(
            report,
            json_path=root / COMPARISON_JSON_RELATIVE_PATH,
            markdown_path=root / COMPARISON_MARKDOWN_RELATIVE_PATH,
            handover_path=root / HANDOVER_MARKDOWN_RELATIVE_PATH,
        )
    except HeldoutComparisonIntegrityError as error:
        print(f"Held-out comparison refused: {error}")
        return 2
    except FileExistsError as error:
        print(f"Held-out comparison refused: {error}")
        return 3

    print(
        "Held-out direct-signal comparison complete: "
        f"conclusion={report.comparison_summary.conclusion}, "
        f"status={report.comparison_run.promotion_gate.status}, "
        f"improved_cases={','.join(report.comparison_summary.improved_case_ids) or 'none'}, "
        f"remaining_blocked_cases={','.join(report.comparison_run.metrics.blocked_case_ids) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
