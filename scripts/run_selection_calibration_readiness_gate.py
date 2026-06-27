"""Run the calibration-only representative-selection readiness gate once."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from incident_precedent_harness.evaluation.selection_calibration_readiness import (
    JSON_REPORT_RELATIVE_PATH,
    MARKDOWN_REPORT_RELATIVE_PATH,
    SelectionCalibrationReadinessError,
    run_selection_calibration_readiness_gate,
    write_selection_calibration_readiness_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate strict-dominance representative selection on dedicated calibration "
            "fixtures. A calibration pass deliberately does not activate the selector."
        )
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing data/, docs/, evidence_vault/, and src/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repository_root.resolve()

    try:
        report = run_selection_calibration_readiness_gate(repository_root=root)
        write_selection_calibration_readiness_report(
            report,
            json_path=root / JSON_REPORT_RELATIVE_PATH,
            markdown_path=root / MARKDOWN_REPORT_RELATIVE_PATH,
        )
    except (SelectionCalibrationReadinessError, FileExistsError) as error:
        print(
            json.dumps(
                {
                    "selection_readiness_kind": "representative_selection_calibration_readiness",
                    "status": "refused",
                    "safe_message": str(error),
                },
                indent=2,
            )
        )
        return 2

    print(
        json.dumps(
            {
                "selection_readiness_kind": report.report_kind,
                "status": "passed",
                "decision": report.decision.value,
                "selection_calibration_case_count": report.metrics.selection_calibration_case_count,
                "selection_contract_pass_rate": report.metrics.selection_contract_pass_rate,
                "order_invariance_pass_rate": report.metrics.order_invariance_pass_rate,
                "active_policy_changed": report.metrics.active_policy_changed,
                "selector_activation_claim": report.metrics.selector_activation_claim,
                "evidence_json": JSON_REPORT_RELATIVE_PATH.as_posix(),
                "evidence_markdown": MARKDOWN_REPORT_RELATIVE_PATH.as_posix(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
