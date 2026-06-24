# Connection-Pool Direct-Signal Calibration Runbook

## Purpose

Validate the narrowly scoped connection-pool admission intervention identified
by the Held-Out Tranche 01 failure autopsy.

## Preconditions

- Work is on a feature branch.
- The working tree is clean after the intervention code commit.
- Do not edit `data/evals/heldout/`, its freeze manifest, the committed held-out
  baseline, or the held-out autopsy artifacts.

## Commands

```powershell
python -m pytest .\tests\unit
python .\scripts\run_connection_pool_direct_signal_calibration.py --repository-root . --top-k 5
```

## Expected evidence

The command writes a separate calibration-only pair:

- `docs/reports/connection-pool-direct-signal-calibration.md`;
- `evidence_vault/reports/connection-pool-direct-signal-calibration.json`.

Review that:

- `EVAL-010` remains `missing_critical_facts`;
- `EVAL-011` remains `evidence_found_with_conflict`;
- no calibration unsafe precedent or procedure is surfaced.

## Stop conditions

Do not rerun the frozen held-out evaluator in this slice.

Stop and investigate before proceeding if tests fail, calibration state accuracy
drops below `1.0`, a calibration unsafe precedent is retained, or an unexpected
procedure appears.
