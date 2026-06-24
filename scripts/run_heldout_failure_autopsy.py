"""Create one trace-only autopsy from the committed blocked held-out baseline."""

from __future__ import annotations

import argparse
from pathlib import Path

from incident_precedent_harness.evaluation.autopsy import (
    AUTOPSY_JSON_RELATIVE_PATH,
    AUTOPSY_MARKDOWN_RELATIVE_PATH,
    HeldoutBaselineIntegrityError,
    build_heldout_failure_autopsy,
    write_heldout_failure_autopsy,
)
from incident_precedent_harness.retrieval import JsonDatasetRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read the committed blocked held-out baseline and produce a write-once "
            "failure autopsy without rescoring frozen cases."
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
        report = build_heldout_failure_autopsy(
            repository_root=root,
            incidents=repository.load_incidents(),
            cases=repository.load_heldout_cases(),
        )
        write_heldout_failure_autopsy(
            report,
            json_path=root / AUTOPSY_JSON_RELATIVE_PATH,
            markdown_path=root / AUTOPSY_MARKDOWN_RELATIVE_PATH,
        )
    except HeldoutBaselineIntegrityError as error:
        print(f"Held-out failure autopsy refused: {error}")
        return 2
    except FileExistsError as error:
        print(f"Held-out failure autopsy refused: {error}")
        return 3

    print(
        "Held-out failure autopsy complete: "
        f"blocked_cases={','.join(report.blocked_case_ids)}, "
        f"findings={len(report.findings)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
