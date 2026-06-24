# Held-Out Direct-Signal Comparison Runbook

## Purpose

Run one controlled comparison of ADR-0008 against the immutable Held-Out
Tranche 01 keyword-plus-policy baseline.

## Preconditions

- Work is on the dedicated comparison branch.
- ADR-0008 calibration evidence is already merged to `main`.
- The working tree is clean after committing comparison code.
- The committed baseline evidence exists at:
  `evidence_vault/reports/heldout-tranche-01-keyword-policy.json`.
- Do not edit `data/evals/heldout/`, its manifest, baseline evidence, or autopsy
  evidence.

## Command

```powershell
python -m pytest .\tests\unit
python .\scripts\run_heldout_direct_signal_comparison.py --repository-root . --top-k 5
```

## Expected outputs

The command writes exactly once:

- `docs/reports/heldout-tranche-01-direct-signal-comparison.md`;
- `evidence_vault/reports/heldout-tranche-01-direct-signal-comparison.json`;
- `docs/handover/Incident_Precedent_Retrieval_Harness_Handover_002_Post_Intervention_Comparison.md`.

It refuses to overwrite any of these paths.

## Review checklist

- The comparison references the same held-out manifest SHA-256 as the baseline.
- The baseline artifact is linked by SHA-256 and repository revision.
- `EVAL-102` either improves or remains blocked for a documented reason.
- No previously passing case regresses.
- Remaining blocked cases are explicitly listed.
- The comparison conclusion is preserved even when the strict gate remains
  blocked.

## Stop conditions

Stop and investigate; do not create a new comparison artifact if:

- unit tests fail;
- manifest verification fails;
- the baseline report is missing or malformed;
- the command reports a regression;
- any comparison evidence path already exists;
- generated output indicates altered case IDs, manifest hash, retriever, top-k,
  or promotion thresholds.

A blocked result is valid evidence. Do not modify held-out cases or rerun the
same configuration to seek a different result.
