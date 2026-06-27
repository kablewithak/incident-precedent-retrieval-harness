"""Import only a manifest-verified, test-only procedure-asymmetry fixture archive."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from incident_precedent_harness.evaluation.procedure_asymmetry_fixture_import import (
    MARKDOWN_REPORT_RELATIVE_PATH,
    JSON_REPORT_RELATIVE_PATH,
    ProcedureAsymmetryFixtureImportError,
    TARGET_RELATIVE_PATH,
    verify_and_import_procedure_asymmetry_fixture,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and import the accepted procedure-asymmetry proposal into an "
            "isolated test-only evaluation path."
        )
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        required=True,
        help="Repository root containing src/, data/, docs/, and evidence_vault/.",
    )
    parser.add_argument(
        "--proposal-archive",
        type=Path,
        required=True,
        help="Path to the accepted procedure-asymmetry V2 proposal ZIP.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        report = verify_and_import_procedure_asymmetry_fixture(
            repository_root=args.repository_root,
            proposal_archive=args.proposal_archive,
        )
    except (ProcedureAsymmetryFixtureImportError, FileExistsError, ValueError) as error:
        print(
            json.dumps(
                {
                    "fixture_import_kind": "procedure_asymmetry_fixture_import",
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
                "fixture_import_kind": "procedure_asymmetry_fixture_import",
                "status": "passed",
                "decision": report.decision.value,
                "controlled_card_count": report.controlled_card_count,
                "runtime_case_count": report.runtime_case_count,
                "expected_outcome_count": report.expected_outcome_count,
                "selector_contract_pass_rate": 1.0,
                "imported_fixture_path": report.imported_fixture_path,
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
