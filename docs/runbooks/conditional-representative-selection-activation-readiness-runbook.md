# Conditional Representative-Selection Activation Readiness Runbook

## Purpose

Validate the ADR-0033 conditional representative-selection integration without
changing the frozen Tranche 02 assets or rerunning any immutable comparison.

The integration has exactly one permitted effect:

```text
policy admission
-> optional typed selector refinement
-> displayed representative precedent set
```

The following remain policy-owned and unchanged:

- top-level decision state;
- missing-critical-fact requirements;
- candidate-procedure eligibility and withholding;
- provider-degraded behavior;
- human-review requirement; and
- procedure execution authorization.

## Preconditions

- Work from the dedicated integration branch.
- `main` was clean before branching.
- Do not modify:
  - `data/evals/heldout/tranche_02_future_heldout/`;
  - `evidence_vault/reports/tranche-02-future-heldout-freeze.json`; or
  - `evidence_vault/reports/tranche-02-future-heldout-comparison.json`.
- No local SIE or Docker process is required. These are deterministic policy
  integration controls.

## Validate deterministic behavior

```powershell
python -m pytest .\tests\unit\test_conditional_representative_selection.py

python -m pytest .\tests\unit\test_conditional_selection_activation_readiness.py

python -m pytest .\tests\unit
```

## Run the readiness report once

```powershell
python .\scripts\run_conditional_representative_selection_activation_readiness.py `
    --repository-root .
```

Expected decision:

```text
implementation_validated_activation_blocked
```

This is the expected safe result. It means the implementation controls passed,
but selector activation is still blocked pending a separately governed,
selection-aware end-to-end frozen promotion gate.

Expected evidence paths:

```text
evidence_vault/reports/conditional-representative-selection-activation-readiness.json
docs/reports/conditional-representative-selection-activation-readiness.md
```

## Refusal behavior

The runner refuses to overwrite either report. Do not rerun it after a
successful first run.

## Do not do

- Do not treat the readiness result as production authorization.
- Do not change policy rules, retrieval rank, procedures, or frozen assets to
  improve a readiness result.
- Do not let a display refinement replace the policy decision in a UI.
- Do not interpret a selected historical representative as diagnosis,
  remediation, or procedure authorization.
