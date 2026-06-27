"""Run the write-once procedure-asymmetry fixture comparison gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from incident_precedent_harness.evaluation.procedure_asymmetry_comparison import (
    JSON_REPORT_RELATIVE_PATH,
    MARKDOWN_REPORT_RELATIVE_PATH,
    ProcedureAsymmetryComparisonError,
    run_procedure_asymmetry_fixture_comparison,
    write_procedure_asymmetry_fixture_comparison_report,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare the imported procedure-asymmetry fixture against the isolated "
            "strict-dominance selector."
        )
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        required=True,
        help="Repository root containing data/, docs/, evidence_vault/, and src/.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repository_root = args.repository_root.resolve()
    json_path = repository_root / JSON_REPORT_RELATIVE_PATH
    markdown_path = repository_root / MARKDOWN_REPORT_RELATIVE_PATH

    try:
        report = run_procedure_asymmetry_fixture_comparison(
            repository_root=repository_root,
        )
        write_procedure_asymmetry_fixture_comparison_report(
            report=report,
            json_path=json_path,
            markdown_path=markdown_path,
        )
    except (ProcedureAsymmetryComparisonError, FileExistsError) as error:
        print(
            json.dumps(
                {
                    "fixture_comparison_kind": "procedure_asymmetry_fixture_comparison",
                    "status": "refused",
                    "safe_message": str(error),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    print(
        json.dumps(
            {
                "fixture_comparison_kind": "procedure_asymmetry_fixture_comparison",
                "status": (
                    "passed"
                    if report.comparison_decision.value
                    == "comparison_passed_activation_blocked"
                    else "blocked"
                ),
                "decision": report.comparison_decision.value,
                "runtime_case_count": report.metrics.runtime_case_count,
                "expected_outcome_count": report.metrics.expected_outcome_count,
                "contract_pass_rate": report.metrics.contract_pass_rate,
                "order_invariance_passed": report.metrics.order_invariance_passed,
                "procedure_asymmetry_present": report.metrics.procedure_asymmetry_present,
                "procedure_neutrality_passed": report.metrics.procedure_neutrality_passed,
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
