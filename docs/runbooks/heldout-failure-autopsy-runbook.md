# Held-Out Failure Autopsy Runbook

## Purpose

Create a one-time trace report for the already committed blocked held-out
baseline. The autopsy is diagnostic only. It does not rerun the held-out
evaluation, change retrieval or policy behavior, modify frozen cases, or permit
tuning against held-out labels.

## Preconditions

- The repository working tree is clean.
- `evidence_vault/reports/heldout-tranche-01-keyword-policy.json` exists and is
  committed from the frozen baseline run.
- `data/evals/heldout/HELDOUT_FREEZE_MANIFEST.json` verifies.
- Unit tests pass.

## Run

```powershell
python .\scripts\run_heldout_failure_autopsy.py --repository-root .
```

## Expected output

```text
Held-out failure autopsy complete: blocked_cases=EVAL-102,EVAL-110, findings=2
```

The command writes exactly once:

- `docs/reports/heldout-tranche-01-failure-autopsy.md`
- `evidence_vault/reports/heldout-tranche-01-failure-autopsy.json`

A rerun must refuse to overwrite either file. That refusal protects the trace;
it is not a pipeline failure.

## Safety rules

- Do not edit a held-out case, its freeze manifest, or expected contract while
  investigating the result.
- Do not rerun `run_heldout_evaluation.py` under the same configuration.
- Do not interpret an autopsy hypothesis as an improvement claim.
- Build any proposed intervention against calibration fixtures first, then
  compare it with this committed baseline through a separately versioned
  held-out evaluation run.
