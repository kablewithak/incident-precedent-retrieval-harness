"""Run the write-once frozen Tranche 02 comparison gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from incident_precedent_harness.evaluation.tranche_02_future_holdout_comparison import (
    JSON_REPORT_RELATIVE_PATH,
    MARKDOWN_REPORT_RELATIVE_PATH,
    Tranche02FutureHeldoutComparisonError,
    run_tranche_02_future_heldout_comparison,
    write_tranche_02_future_heldout_comparison_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the governed frozen Tranche 02 selector comparison once."
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        required=True,
        help="Repository root containing frozen Tranche 02 assets.",
    )
    args = parser.parse_args()

    root = args.repository_root.resolve()
    try:
        report = run_tranche_02_future_heldout_comparison(repository_root=root)
        write_tranche_02_future_heldout_comparison_report(
            report=report,
            json_path=root / JSON_REPORT_RELATIVE_PATH,
            markdown_path=root / MARKDOWN_REPORT_RELATIVE_PATH,
        )
    except (Tranche02FutureHeldoutComparisonError, FileExistsError) as error:
        print(
            json.dumps(
                {
                    "status": "refused",
                    "error_type": type(error).__name__,
                    "message": str(error),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    print(
        json.dumps(
            {
                "status": "passed"
                if report.comparison_decision.value
                == "comparison_passed_activation_blocked"
                else "blocked",
                "comparison_kind": "tranche_02_future_heldout_comparison",
                "decision": report.comparison_decision.value,
                "valid_selector_case_count": report.metrics.valid_selector_case_count,
                "pre_selector_rejection_case_count": report.metrics.pre_selector_rejection_case_count,
                "valid_case_contract_pass_rate": report.metrics.valid_case_contract_pass_rate,
                "order_invariance_passed": report.metrics.order_invariance_passed,
                "evidence_json": JSON_REPORT_RELATIVE_PATH.as_posix(),
                "evidence_markdown": MARKDOWN_REPORT_RELATIVE_PATH.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
