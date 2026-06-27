# EVAL-110 Representative-Selection Autopsy Runbook

## Purpose

Create one immutable diagnostic report for the frozen EVAL-110 representative-selection divergence.

The autopsy reads three existing evidence sources:

```text
1. data/evals/heldout/HELDOUT_FREEZE_MANIFEST.json
2. evidence_vault/reports/heldout-tranche-01-keyword-policy.json
3. evidence_vault/reports/frozen-typed-triage-promotion-gate.json
```

It does **not** start Docker, call local SIE, rebuild the dense index, rerun retrieval, or change any policy behavior.

## Preconditions

- You are on `eval/eval-110-representative-selection-failure-autopsy`.
- The frozen typed-triage promotion-gate PR has been merged.
- The three evidence sources above exist and have not been edited.
- The held-out freeze manifest verifies before the script reads EVAL-110.
- Do not modify EVAL-110, any incident card, ranking behavior, policy rule, or procedure metadata for this autopsy.

## Deterministic validation

```powershell
python -m pytest .\tests\unit\test_eval_110_representative_selection_autopsy.py

python -m pytest .\tests\unit
```

## Run once

```powershell
python .\scripts\run_eval_110_representative_selection_autopsy.py --repository-root .
```

Expected outputs:

```text
evidence_vault/reports/eval-110-representative-selection-autopsy.json
docs/reports/eval-110-representative-selection-autopsy.md
```

The script writes the two artifacts once. A repeat run must refuse rather than overwrite them.

## Read the verdict correctly

### `undocumented_conflict_rule`

The recorded policy state is correct, but one same-family representative displaced the frozen expected representative because the active path uses first-compatible retention rather than a reviewed within-family selection rule.

This is a diagnostic conclusion. It does not activate the strict-dominance selector, authorize rank-based tie breaking, or justify changing held-out labels.

### `policy_selection_defect`

A future version may issue this verdict only when the evidence proves the active selection behavior violates an already-approved selection contract.

### `expected_contract_defect`

A future version may issue this verdict only when the frozen expected contract is internally inconsistent with reviewed typed evidence. This requires a documented data-defect process and new freeze revision; it is never fixed in place.

### `insufficient_evidence`

The required baseline, promotion, manifest, or typed-card evidence was unavailable or did not meet the narrow diagnostic criteria. Preserve the refusal or report and perform design review before any change.

## Non-claims

The report does not prove a remediation, a new promotion status, semantic retrieval quality, production readiness, or customer-data safety. Procedures remain evidence only and are never executable.
