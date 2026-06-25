"""Validate calibration fixtures for a future representative selector.

The command validates typed fixture integrity only. It deliberately does not
load held-out cases, invoke the active policy, or execute selection logic.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from incident_precedent_harness.domain.selection_calibration import (
    RepresentativeSelectionExpectationState,
)
from incident_precedent_harness.evals.selection_calibration import (
    load_selection_calibration_cases,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate representative-selection calibration fixtures without "
            "executing selector or policy behavior."
        )
    )
    parser.add_argument(
        "--repository-root",
        default=".",
        help="Repository root containing incident cards and selection calibration fixtures.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    cases = load_selection_calibration_cases(Path(args.repository_root).resolve())
    single_representative_count = sum(
        case.expected_outcome.state
        is RepresentativeSelectionExpectationState.SINGLE_REPRESENTATIVE
        for case in cases
    )
    explicit_tie_count = sum(
        case.expected_outcome.state
        is RepresentativeSelectionExpectationState.EXPLICIT_TIE
        for case in cases
    )
    order_invariance_groups = {
        case.order_invariance_group
        for case in cases
        if case.order_invariance_group is not None
    }

    print("REPRESENTATIVE SELECTION CALIBRATION FIXTURE VALIDATION")
    print("---------------------------------------------------------")
    print(f"selection_calibration_cases={len(cases)}")
    print(f"single_representative_cases={single_representative_count}")
    print(f"explicit_tie_cases={explicit_tie_count}")
    print(f"order_invariance_groups={len(order_invariance_groups)}")
    print("active_policy_changed=false")
    print("heldout_loaded=false")
    print("selector_executed=false")
    print("status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
