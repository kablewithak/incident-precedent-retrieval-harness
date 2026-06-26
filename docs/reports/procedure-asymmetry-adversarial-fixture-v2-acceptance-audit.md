# Procedure-Asymmetry Adversarial Fixture V2 — Acceptance Audit

## Decision

`ACCEPTED_FOR_GOVERNED_TEST_ONLY_REPOSITORY_IMPORT_ONLY`

This audit accepts the V2 proposal as a constrained provenance remediation. It may proceed to a dedicated, case-scoped repository-import and validator slice.

This decision does **not** freeze Tranche 02, activate representative selection, alter `AntiAnchoringDecisionPolicy`, alter retrieval or procedure behavior, or support a production or customer-data claim.

## Binary audit results

| Gate | Result | Evidence |
|---|---:|---|
| Required proposal root | pass | `proposed_procedure_asymmetry_fixture/` present |
| Delivered files | pass | 16 files including `manifest.json` |
| Manifest inventory | pass | 15/15 non-manifest assets matched raw-byte SHA-256 and byte count |
| Aggregate hashes | pass | inputs, expected outcomes, governance, documentation, and all-non-manifest aggregates matched |
| V2 allowed change boundary | pass | Exactly five modified/new paths; every path was allowed |
| Immutable V1 assets | pass | runtime inputs 3/3; expected outcomes 3/3; controlled cards 4/4; rejected ideas 1/1 |
| Source-to-controlled derivation | pass | 4/4 exact field-set assertions passed |
| V1 finding PAF-AUDIT-001-F01 | remediated | PAV-001 / INC-013 now declares `unsafe_procedure_ids` |
| Typed schema validation | pass | controlled cards 4/4; typed selection intakes 3/3 |
| Strict-dominance oracle replay | pass | PAF-T02-001 through PAF-T02-003 selected `INC-014` |
| Order reversal | pass | PAF-T02-001 and PAF-T02-002 both select `INC-014` |
| Procedure-neutral control parity | pass | PAF-T02-003 still selects `INC-014` |

## Provenance remediation verification

The V2 archive changes only:

```text
inputs/governance/procedure_asymmetry_governance.json
inputs/governance/controlled_card_derivation_assertions.json
authoring_ledger.md
APPLY_MANIFEST.md
manifest.json
```

No runtime input, expected-outcome asset, controlled-card JSON asset, or rejected-case asset drifted from the supplied V2 remediation baseline.

For PAV-001 / INC-013, the actual source-to-controlled differences are exactly:

```text
incident_id
title
unsafe_procedure_ids
```

Those fields exactly equal the V2 declared perturbation fields. The controlled-card variant removes source `RB-002` from `unsafe_procedure_ids` only to isolate the test-only `RB-003` procedure-availability asymmetry.

## Adversarial property

In the primary set, `INC-013` is the procedure-favored candidate, has the lower incident ID, and appears first in PAF-T02-001. Typed selection evidence nevertheless strictly favors `INC-014`.

The order-reversal partner preserves the same expected winner. The procedure-neutral control removes the procedure contrast while preserving the typed-selection winner. This makes the fixture diagnostic of forbidden procedure metadata, identifier, or order leakage rather than a procedure-driven oracle.

## Oracle replay boundary

The audit replayed the three cases against the isolated strict-dominance contract from the calibrated selector boundary:

```text
PAF-T02-001 -> single_representative / INC-014
PAF-T02-002 -> single_representative / INC-014
PAF-T02-003 -> single_representative / INC-014
```

This is a proposal acceptance check, not a full active-policy or Tranche 02 evaluation run.

## Required next gate

Import the V2 assets only through a dedicated case-scoped fixture validator. That validator must:

1. validate the manifest and aggregate hashes before loading any case;
2. validate every controlled-card derivation assertion;
3. reject global incident-corpus loading;
4. withhold governance and expected outcomes from selector inputs;
5. compare selector results only after validation;
6. keep the fixture outside active policy, retrieval, source incident data, and production paths.

## Non-claims

- No Tranche 02 freeze.
- No selector activation.
- No active-policy, retrieval, procedure, or decision-state behavior change.
- No production, deployment, customer-data, or operational-readiness claim.
