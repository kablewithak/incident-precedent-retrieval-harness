# Tranche 02 Future-Held-Out Freeze Runbook

## Purpose

Freeze the independently authored and acceptance-audited V2 Tranche 02 proposal
without running a selector, changing application policy, or overwriting prior
evidence.

## Preconditions

- `main` is clean.
- PR #39 acceptance-audit artifacts are present:
  `docs/reports/tranche-02-future-heldout-v2-acceptance-audit.json` and `.md`.
- The supplied archive is the approved V2 file:
  `tranche-02-future-heldout-blind-authoring-proposal-v2.zip`.
- The archive SHA-256 is:

```text
a371be0ab28e2b7f742cf682f212d2665e4e2d893004bc73e72c898c3d886fa0
```

- None of these paths already exist:

```text
data/evals/heldout/tranche_02_future_heldout/
evidence_vault/reports/tranche-02-future-heldout-freeze.json
docs/reports/tranche-02-future-heldout-freeze.md
```

## Run

```powershell
$proposal = Join-Path $HOME "Downloads\tranche-02-future-heldout-blind-authoring-proposal-v2.zip"

Get-FileHash -LiteralPath $proposal -Algorithm SHA256

python .\scripts\import_and_freeze_tranche_02_future_heldout.py `
    --repository-root . `
    --proposal-archive "$proposal"
```

## Expected result

```text
status: passed
decision: frozen_test_only
runtime_case_count: 12
expected_outcome_count: 12
source_archive_asset_count: 27
```

## Writes

```text
data/evals/heldout/tranche_02_future_heldout/
  inputs/cases/
  expected_outcomes/
  TRANCHE_02_FUTURE_HELDOUT_FREEZE_MANIFEST.json

evidence_vault/reports/tranche-02-future-heldout-freeze.json
docs/reports/tranche-02-future-heldout-freeze.md
```

## Refusal behavior

A refusal is expected when the acceptance audit is absent, the archive hash differs
from its audited V2 SHA-256, any manifest or asset integrity check fails, runtime
inputs contain evaluator-only fields, the intentional invalid cases do not reject
before selection, or a freeze receipt already exists.

Do not delete a successful freeze target to rerun it. Treat the generated receipt as
immutable evidence. The later comparison gate must consume this frozen location.
