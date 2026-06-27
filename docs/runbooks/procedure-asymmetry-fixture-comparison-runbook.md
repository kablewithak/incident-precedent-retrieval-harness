# Procedure-Asymmetry Fixture Comparison Runbook

## Purpose

Evaluate the imported, manifest-verified procedure-asymmetry fixture against the
standalone strict-dominance selector and record whether the selector remains
insensitive to candidate order and governed procedure posture.

This run is test-only. It does not use Docker, SIE, lexical retrieval, dense
retrieval, held-out fixtures, the active incident corpus, or
`AntiAnchoringDecisionPolicy`.

## Preconditions

- PR #37 or an equivalent manifest-verified import must already be present.
- The repository must contain:
  - `data/evals/procedure_asymmetry_fixture/`
  - `evidence_vault/reports/procedure-asymmetry-fixture-import.json`
- Do not edit fixture assets after import.
- Do not run this harness until the unit suite passes.
- Do not modify active policy, retrieval, source incident cards, or procedure
  assets in this slice.

## Validation

```powershell
python -m pytest .\tests\unit\test_procedure_asymmetry_comparison.py

python -m pytest .\tests\unit
```

## Run once

```powershell
python .\scripts\run_procedure_asymmetry_fixture_comparison.py --repository-root .
```

Expected evidence paths:

```text
evidence_vault/reports/procedure-asymmetry-fixture-comparison.json
docs/reports/procedure-asymmetry-fixture-comparison.md
```

A second run refuses to overwrite either report.

## Read the decision correctly

### `comparison_passed_activation_blocked`

All three fixed cases matched their expected outcomes. Candidate order reversal and
procedure-neutral control parity held.

This is not selector activation authorization.

### `comparison_blocked`

One or more fixed comparison properties failed. Preserve the report. Do not repair
the fixture by changing incident IDs, candidate order, procedure metadata, or
expected outcomes.

### `insufficient_evidence`

The import receipt or manifest integrity boundary was unavailable. Repair the
evidence chain rather than evaluating the selector.

## Non-claims

This run does not:

- freeze Tranche 02;
- activate strict-dominance selection;
- change `AntiAnchoringDecisionPolicy`;
- improve retrieval;
- authorize a procedure;
- use customer data;
- establish production, deployment, or operational readiness.
