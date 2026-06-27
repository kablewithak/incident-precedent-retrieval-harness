# Tranche 02 Future-Held-Out Comparison Runbook

## Purpose

Run the single predeclared, write-once comparison between the isolated
strict-dominance selector and the frozen Tranche 02 evaluator-only outcomes.

## Preconditions

- `main` includes the governed Tranche 02 freeze boundary.
- The working tree is clean.
- Unit tests pass.
- The following evidence exists and has not been altered:
  - `data/evals/heldout/tranche_02_future_heldout/`;
  - `TRANCHE_02_FUTURE_HELDOUT_FREEZE_MANIFEST.json`;
  - `evidence_vault/reports/tranche-02-future-heldout-freeze.json`.
- No comparison receipt already exists.

## Run

```powershell
python .\scripts\run_tranche_02_future_heldout_comparison.py `
    --repository-root .
```

## Expected evidence

The command writes once:

```text
evidence_vault/reports/tranche-02-future-heldout-comparison.json
docs/reports/tranche-02-future-heldout-comparison.md
```

A `comparison_blocked` result is valid evidence. Preserve it; do not modify
frozen cases, outcomes, selector code, or thresholds to rerun the tranche.

## Write-once behavior

A successful or blocked comparison receipt must not be overwritten. A later
attempt is refused. Do not delete a receipt to force a rerun.

## Interpretation

`comparison_passed_activation_blocked` means only that the isolated selector
matched the frozen Tranche 02 oracle and the negative controls rejected before
selector execution. It does not activate representative selection.
