"""Run the frozen held-out tranche once for the current keyword-plus-policy configuration."""

from __future__ import annotations

import argparse
from pathlib import Path

from incident_precedent_harness.decisions.policy import AntiAnchoringDecisionPolicy
from incident_precedent_harness.evaluation.heldout import (
    JSON_REPORT_RELATIVE_PATH,
    MARKDOWN_REPORT_RELATIVE_PATH,
    HeldoutManifestIntegrityError,
    run_frozen_heldout_evaluation,
    write_heldout_report,
)
from incident_precedent_harness.retrieval import JsonDatasetRepository, KeywordRetriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the frozen held-out tranche once. A blocked gate is a valid "
            "evidence result and exits successfully after report creation."
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
        help="Number of lexical candidates sent to the policy for provider-available cases.",
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
        report = run_frozen_heldout_evaluation(
            repository_root=root,
            retriever=KeywordRetriever(incidents),
            policy=AntiAnchoringDecisionPolicy(),
            incidents=incidents,
            procedures=procedures,
            cases=cases,
            top_k=args.top_k,
        )
        write_heldout_report(
            report,
            json_path=root / JSON_REPORT_RELATIVE_PATH,
            markdown_path=root / MARKDOWN_REPORT_RELATIVE_PATH,
        )
    except HeldoutManifestIntegrityError as error:
        print(f"Held-out evaluation refused: {error}")
        return 2
    except FileExistsError as error:
        print(f"Held-out evaluation refused: {error}")
        return 3

    print(
        "Held-out evaluation complete: "
        f"status={report.promotion_gate.status}, "
        f"decision_state_accuracy={report.metrics.decision_state_accuracy}, "
        f"case_contract_pass_rate={report.metrics.case_contract_pass_rate}, "
        f"blocked_cases={','.join(report.metrics.blocked_case_ids) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
