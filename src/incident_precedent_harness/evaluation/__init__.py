"""Evaluation boundaries and reporting for frozen test tranches."""

from incident_precedent_harness.evaluation.autopsy import (
    HeldoutBaselineIntegrityError,
    HeldoutFailureAutopsyReport,
    build_heldout_failure_autopsy,
    write_heldout_failure_autopsy,
)
from incident_precedent_harness.evaluation.heldout import (
    HeldoutEvaluationReport,
    HeldoutManifestIntegrityError,
    run_frozen_heldout_evaluation,
    verify_heldout_freeze,
    write_heldout_report,
)

__all__ = [
    "HeldoutBaselineIntegrityError",
    "HeldoutEvaluationReport",
    "HeldoutFailureAutopsyReport",
    "HeldoutManifestIntegrityError",
    "build_heldout_failure_autopsy",
    "run_frozen_heldout_evaluation",
    "verify_heldout_freeze",
    "write_heldout_failure_autopsy",
    "write_heldout_report",
]
