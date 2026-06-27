"""Write one frozen-evidence autopsy for the EVAL-110 selection divergence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from incident_precedent_harness.evaluation.eval_110_representative_selection_autopsy import (
    AUTOPSY_JSON_RELATIVE_PATH,
    AUTOPSY_MARKDOWN_RELATIVE_PATH,
    Eval110RepresentativeSelectionAutopsyError,
    build_eval_110_representative_selection_autopsy,
    write_eval_110_representative_selection_autopsy,
)
from incident_precedent_harness.evaluation.heldout import HeldoutManifestIntegrityError
from incident_precedent_harness.retrieval import JsonDatasetRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read frozen EVAL-110 baseline and typed-triage evidence once; emit a "
            "write-once representative-selection diagnostic without rerunning retrieval."
        )
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing data/, docs/, and evidence_vault/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repository_root.resolve()
    repository = JsonDatasetRepository(root)

    try:
        report = build_eval_110_representative_selection_autopsy(
            repository_root=root,
            incidents=repository.load_incidents(),
            cases=repository.load_heldout_cases(),
        )
        write_eval_110_representative_selection_autopsy(
            report,
            json_path=root / AUTOPSY_JSON_RELATIVE_PATH,
            markdown_path=root / AUTOPSY_MARKDOWN_RELATIVE_PATH,
        )
    except (HeldoutManifestIntegrityError, Eval110RepresentativeSelectionAutopsyError) as error:
        print(
            json.dumps(
                {
                    "autopsy_kind": "eval_110_representative_selection_autopsy",
                    "status": "refused",
                    "safe_message": str(error),
                },
                indent=2,
            )
        )
        return 2
    except FileExistsError as error:
        print(
            json.dumps(
                {
                    "autopsy_kind": "eval_110_representative_selection_autopsy",
                    "status": "refused",
                    "safe_message": str(error),
                },
                indent=2,
            )
        )
        return 3

    print(
        json.dumps(
            {
                "autopsy_kind": "eval_110_representative_selection_autopsy",
                "status": "passed",
                "target_eval_id": report.target_eval_id,
                "verdict": report.verdict.value,
                "retained_precedent_ids": report.retained_precedent_ids,
                "omitted_required_precedent_ids": report.omitted_required_precedent_ids,
                "unexpected_retained_precedent_ids": report.unexpected_retained_precedent_ids,
                "evidence_json": AUTOPSY_JSON_RELATIVE_PATH.as_posix(),
                "evidence_markdown": AUTOPSY_MARKDOWN_RELATIVE_PATH.as_posix(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
