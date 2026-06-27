# Procedure-Asymmetry Fixture Validator and Import Runbook

## Purpose

Validate and import the already accepted V2 procedure-asymmetry proposal archive as
an isolated, test-only evaluation fixture.

This is an archive-integrity and selector-regression boundary. It does not start
Docker, call SIE, load retrieval, change active policy, or modify the held-out set.

## Required source input

Use the exact accepted V2 archive from the earlier governed authoring flow:

```text
procedure-asymmetry-adversarial-fixture-proposal-v2.zip
```

A duplicate download with a suffix such as `(1)` is acceptable only when it is
byte-identical to the accepted archive. Do not rebuild, rename internal files, or
edit the archive before validation.

## Preconditions

- Work on the dedicated fixture-validator branch.
- `main` was clean before creating the branch.
- The accepted V2 archive is available locally.
- Do not edit the archive contents.
- Do not pre-create `data/evals/procedure_asymmetry_fixture/`.
- Do not create report files before the importer runs.

## Deterministic verification

```powershell
python -m pytest .\tests\unit\test_procedure_asymmetry_fixture_import.py

python -m pytest .\tests\unit
```

## Import once

Use the downloaded archive path:

```powershell
$proposal = Get-ChildItem `
    -Path "$HOME\Downloads" `
    -File `
    -Filter "procedure-asymmetry-adversarial-fixture-proposal-v2*.zip" |
    Select-Object -First 1 -ExpandProperty FullName

$proposal

python .\scripts\import_procedure_asymmetry_fixture.py `
    --repository-root . `
    --proposal-archive $proposal
```

Expected output shape:

```json
{
  "fixture_import_kind": "procedure_asymmetry_fixture_import",
  "status": "passed",
  "decision": "imported_test_only",
  "controlled_card_count": 4,
  "runtime_case_count": 3,
  "expected_outcome_count": 3
}
```

Expected imported fixture path:

```text
data/evals/procedure_asymmetry_fixture/
```

Expected evidence paths:

```text
evidence_vault/reports/procedure-asymmetry-fixture-import.json
docs/reports/procedure-asymmetry-fixture-import.md
```

## Case-scoped controlled-card behavior

The V2 archive contains two controlled card sets with the same incident IDs:
`PAV-001-procedure-asymmetric` and `PAV-002-procedure-neutral-control`.
This is intentional. The importer reads the runtime case's
`controlled_card_set_id` and passes only that set to the isolated selector.

The V2 outcome assets use `expected_outcome_kind` and
`expected_representative_ids`. Those reviewer-controlled fields are accepted only
from `expected_outcomes/`; they remain forbidden in `inputs/cases/`.

## Read a refusal correctly

A refusal means the archive has not been imported. Common legitimate reasons:

- archive path missing or ambiguous;
- wrong root layout or wrong file count;
- raw file hash or byte-count mismatch;
- unsupported aggregate encoding;
- missing PAV-001 / INC-013 `unsafe_procedure_ids` provenance declaration;
- expected outcomes leaking into runtime inputs;
- runtime case references an unknown controlled card set;
- selector result diverging from the accepted V2 oracle;
- destination or report already exists.

Preserve the refusal JSON. Do not manually copy an archive asset around a failed gate.

## Non-claims

This run does not:

- alter `data/incidents/`, `data/procedures/`, or active policy;
- run a Tranche 02 evaluation or freeze;
- activate strict-dominance representative selection;
- authorize procedures;
- call a provider or establish an SIE, customer-data, deployment, or production claim.
