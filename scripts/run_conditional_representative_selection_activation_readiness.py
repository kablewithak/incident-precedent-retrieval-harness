"""Run the write-once ADR-0033 conditional-selection readiness report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from incident_precedent_harness.evaluation.conditional_selection_activation_readiness import (
    JSON_REPORT_RELATIVE_PATH,
    MARKDOWN_REPORT_RELATIVE_PATH,
    run_conditional_selection_activation_readiness,
    write_conditional_selection_activation_readiness_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run conditional representative-selection activation-readiness controls."
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        required=True,
        help="Repository root containing source-grounded RelayOps assets.",
    )
    arguments = parser.parse_args()
    root = arguments.repository_root.resolve()

    report = run_conditional_selection_activation_readiness(repository_root=root)
    write_conditional_selection_activation_readiness_report(
        report=report,
        json_path=root / JSON_REPORT_RELATIVE_PATH,
        markdown_path=root / MARKDOWN_REPORT_RELATIVE_PATH,
    )
    print(
        json.dumps(
            {
                "status": "passed"
                if report.decision.value
                == "implementation_validated_activation_blocked"
                else "blocked",
                "readiness_kind": report.report_kind,
                "decision": report.decision.value,
                "fixed_case_count": report.fixed_case_count,
                "contract_pass_rate": report.contract_pass_rate,
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
