"""Inspect a JSONL historical-incident export without writing repository data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from incident_precedent_harness.ingestion.inspection import (
    ImportBatchReadError,
    inspect_import_batch,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a controlled historical incident JSONL import batch."
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to a UTF-8 JSONL file.")
    parser.add_argument(
        "--batch-id",
        required=True,
        help="Stable lowercase batch identifier for the inspection report.",
    )
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    try:
        report = inspect_import_batch(input_path=arguments.input, batch_id=arguments.batch_id)
    except ImportBatchReadError as error:
        print(
            json.dumps(
                {
                    "batch_id": arguments.batch_id,
                    "input_file_name": arguments.input.name,
                    "ready_for_human_review": False,
                    "failure_code": "input_unreadable",
                    "safe_message": str(error),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    print(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0 if report.ready_for_human_review else 2


if __name__ == "__main__":
    raise SystemExit(main())
