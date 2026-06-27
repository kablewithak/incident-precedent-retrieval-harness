# Representative-Selection Calibration Readiness Gate Runbook

## Purpose

Measure whether the standalone strict-dominance representative selector satisfies the
fixed, typed `selection_calibration` contract while preserving a hard activation
block.

This run does not use Docker, SIE, lexical retrieval, dense retrieval, or held-out
fixtures.

## Preconditions

- Run from the dedicated evaluation branch.
- The repository is clean before applying this slice.
- `data/evals/selection_calibration/` and incident-card schema contracts are present.
- Do not add EVAL-110 or any frozen held-out label to calibration data.
- Do not modify `AntiAnchoringDecisionPolicy` in this slice.

## Deterministic verification

```powershell
python -m pytest .\tests\unit\test_selection_calibration_readiness.py

python -m pytest .\tests\unit
```

## Run the gate once

```powershell
python .\scripts\run_selection_calibration_readiness_gate.py --repository-root .
```

Expected evidence paths:

```text
evidence_vault/reports/representative-selection-calibration-readiness.json
docs/reports/representative-selection-calibration-readiness.md
```

The command returns a successful process result for:

```text
calibration_passed_activation_blocked
```

That means the known calibration contract passed while selector activation remains
explicitly blocked.

A second invocation refuses to overwrite the evidence pair.

## Read the decision correctly

### `calibration_passed_activation_blocked`

The selector matches known calibration cases and fixed order-invariance checks.
It is still not authorized for active-policy use.

### `calibration_blocked`

At least one fixed calibration contract or order-invariance check failed.
Preserve the report. Do not repair it with rank ordering, incident IDs, or held-out
labels.

### `insufficient_evidence`

The gate could not measure a required calibration category, such as order
invariance. Preserve the report and repair the calibration harness, not the active
policy.

## Next boundary after this gate

A future slice may author an independent, fresh held-out proposal for an activation
candidate. That proposal must be blind to frozen EVAL-110 labels and must not change
the active policy until the new evaluation design is reviewed.

## Non-claims

This run does not:

- prove that selector activation will pass held-out evaluation;
- improve retrieval;
- authorize procedures;
- use customer data;
- establish a production or deployment claim.
