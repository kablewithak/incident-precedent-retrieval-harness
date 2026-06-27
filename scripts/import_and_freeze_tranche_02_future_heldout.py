"""Validate and freeze the acceptance-audited future-held-out Tranche 02 archive."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from incident_precedent_harness.evaluation.tranche_02_future_holdout_freeze import (
    JSON_REPORT_RELATIVE_PATH,
    MARKDOWN_REPORT_RELATIVE_PATH,
    TARGET_RELATIVE_PATH,
    Tranche02FutureHeldoutFreezeError,
    validate_and_freeze_tranche_02_future_heldout,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the acceptance-audited V2 future-held-out Tranche 02 archive and "
            "freeze only its runtime inputs and evaluator outcomes."
        )
    )
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--proposal-archive", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repository_root.resolve()
    try:
        report = validate_and_freeze_tranche_02_future_heldout(
            repository_root=root,
            proposal_archive=args.proposal_archive,
        )
    except (Tranche02FutureHeldoutFreezeError, FileExistsError) as error:
        print(
            json.dumps(
                {
                    "freeze_kind": "tranche_02_future_heldout_freeze",
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
                "freeze_kind": report.report_kind,
                "status": "passed",
                "decision": report.decision.value,
                "runtime_case_count": report.runtime_case_count,
                "expected_outcome_count": report.expected_outcome_count,
                "source_archive_asset_count": report.source_archive_asset_count,
                "frozen_fixture_path": TARGET_RELATIVE_PATH.as_posix(),
                "evidence_json": JSON_REPORT_RELATIVE_PATH.as_posix(),
                "evidence_markdown": MARKDOWN_REPORT_RELATIVE_PATH.as_posix(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
