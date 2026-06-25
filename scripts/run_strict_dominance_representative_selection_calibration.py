"""Run calibration-only evaluation for the strict-dominance selector.

This runner loads only the dedicated selection-calibration fixtures and incident
cards. It does not load held-out cases, invoke retrieval, or alter the active
anti-anchoring policy.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from incident_precedent_harness.decisions.strict_dominance_selection import (
    StrictDominanceRepresentativeSelector,
)
from incident_precedent_harness.evals.selection_calibration import (
    load_selection_calibration_cases,
)
from incident_precedent_harness.retrieval.repository import JsonDatasetRepository


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate strict-dominance representative selection on calibration fixtures."
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        required=True,
        help="Repository root containing src/, data/, docs/, and evidence_vault/.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repository_root = args.repository_root.resolve()
    repository = JsonDatasetRepository(repository_root)
    incidents = repository.load_incidents()
    cases = load_selection_calibration_cases(repository_root)
    selector = StrictDominanceRepresentativeSelector()

    outcomes: list[dict[str, object]] = []
    passed_case_ids: list[str] = []
    failed_case_ids: list[str] = []

    for case in cases:
        result = selector.select(
            intake=case.selection_intake,
            candidate_incident_ids=case.candidate_incident_ids,
            incidents=incidents,
        )
        expected_state = case.expected_outcome.state.value
        expected_ids = list(case.expected_outcome.representative_incident_ids)
        actual_state = result.selection_state.value
        actual_ids = list(result.representative_incident_ids)
        passed = actual_state == expected_state and actual_ids == expected_ids
        (passed_case_ids if passed else failed_case_ids).append(case.selection_case_id)
        outcomes.append(
            {
                "selection_case_id": case.selection_case_id,
                "passed": passed,
                "expected_state": expected_state,
                "actual_state": actual_state,
                "expected_representative_incident_ids": expected_ids,
                "actual_representative_incident_ids": actual_ids,
                "candidate_count": len(case.candidate_incident_ids),
                "reason": result.selection_reason,
            }
        )

    report = {
        "report_kind": "strict_dominance_representative_selection_calibration",
        "generated_at": datetime.now(UTC).isoformat(),
        "contract_version": "representative-selection-v1",
        "selection_calibration_case_count": len(cases),
        "passed_case_ids": passed_case_ids,
        "failed_case_ids": failed_case_ids,
        "strict_dominance_contract_pass_rate": round(len(passed_case_ids) / len(cases), 4),
        "active_policy_changed": False,
        "heldout_loaded": False,
        "retrieval_loaded": False,
        "selector_activation_claim": False,
        "outcomes": outcomes,
        "non_claims": [
            "This report does not activate representative selection in AntiAnchoringDecisionPolicy.",
            "This report does not evaluate held-out cases or establish promotion eligibility.",
            "This report does not claim production incident-response safety or retrieval improvement.",
        ],
    }

    markdown = _render_markdown(report)
    json_path = repository_root / "evidence_vault" / "reports" / "strict-dominance-representative-selection-calibration.json"
    markdown_path = repository_root / "docs" / "reports" / "strict-dominance-representative-selection-calibration.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown, encoding="utf-8")

    print("STRICT-DOMINANCE REPRESENTATIVE SELECTION CALIBRATION")
    print("---------------------------------------------------")
    print(f"selection_calibration_cases={len(cases)}")
    print(f"passed_cases={len(passed_case_ids)}")
    print(f"failed_cases={len(failed_case_ids)}")
    print(f"strict_dominance_contract_pass_rate={report['strict_dominance_contract_pass_rate']}")
    print("active_policy_changed=false")
    print("heldout_loaded=false")
    print("retrieval_loaded=false")
    print("selector_activation_claim=false")
    print(f"status={'PASS' if not failed_case_ids else 'BLOCKED'}")
    print(f"markdown_report={markdown_path}")
    print(f"machine_report={json_path}")
    return 0 if not failed_case_ids else 1


def _render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Strict-Dominance Representative-Selection Calibration Report",
        "",
        "## Scope",
        "",
        "This report evaluates only the standalone strict-dominance selector on "
        "dedicated selection-calibration fixtures. It does not load held-out cases, "
        "invoke retrieval, change the active policy, or authorize activation.",
        "",
        "## Result",
        "",
        f"- Selection calibration cases: `{report['selection_calibration_case_count']}`",
        f"- Passed cases: `{len(report['passed_case_ids'])}`",
        f"- Failed cases: `{len(report['failed_case_ids'])}`",
        f"- Contract pass rate: `{report['strict_dominance_contract_pass_rate']}`",
        "- Active policy changed: `false`",
        "- Held-out loaded: `false`",
        "- Retrieval loaded: `false`",
        "- Selector activation claim: `false`",
        "",
        "## Case Outcomes",
        "",
        "| Case | Result | Expected | Actual |",
        "|---|---|---|---|",
    ]
    for outcome in report["outcomes"]:
        status = "PASS" if outcome["passed"] else "BLOCKED"
        expected = f"{outcome['expected_state']}: {', '.join(outcome['expected_representative_incident_ids'])}"
        actual = f"{outcome['actual_state']}: {', '.join(outcome['actual_representative_incident_ids'])}"
        lines.append(f"| {outcome['selection_case_id']} | {status} | {expected} | {actual} |")

    lines.extend([
        "",
        "## Non-claims",
        "",
    ])
    lines.extend(f"- {claim}" for claim in report["non_claims"])
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
