"""Evaluation boundaries and reporting for frozen test tranches."""

from incident_precedent_harness.evaluation.heldout import (
    HeldoutEvaluationReport,
    HeldoutManifestIntegrityError,
    run_frozen_heldout_evaluation,
    verify_heldout_freeze,
    write_heldout_report,
)

__all__ = [
    "HeldoutEvaluationReport",
    "HeldoutManifestIntegrityError",
    "run_frozen_heldout_evaluation",
    "verify_heldout_freeze",
    "write_heldout_report",
]
