# Procedure-Asymmetry Adversarial Fixture — Acceptance Audit

## Verdict

`CONDITIONAL_REJECTION_NOT_FROZEN_NOT_IMPORTABLE`

The blinded proposal is technically strong, structurally separate, and its three expected representative outcomes agree with the current strict-dominance contract in a reconstructed check. It is **not authorized for repository import or Tranche 02 freeze** because one controlled procedure-field mutation is undeclared in the provenance registry.

This is an integrity failure in fixture governance, not a selector failure.

## Audit identity

| Field | Value |
|---|---|
| Audit ID | `PAF-AUDIT-001` |
| Proposal archive | `procedure-asymmetry-adversarial-fixture-proposal.zip` |
| Proposal archive SHA-256 | `1290a90d622e9beef670426b17c53fb703b682bfb59f451c7f7e97d25307810e` |
| Proposal manifest SHA-256 | `f66f93c075c81519ec8819ac275c063302d545a624337569f4f22f625d42aeb7` |
| Governance baseline | `bb76952 (PR #25 merged; user-provided checkpoint)` |
| Scope | ADR-0019 governed test-only procedure-asymmetry fixture proposal |
| Activation authority | None |

## Passed checks

| Check | Result | Evidence |
|---|---|---|
| Package structure | Pass | Required authoring assets and separate runtime/expected-outcome paths are present. |
| Manifest integrity | Pass | `14/14` listed non-manifest assets matched raw-byte hashes and byte counts; all declared aggregate hashes matched. |
| Typed schema validation | Pass | `4/4` controlled cards validated as `HistoricalIncidentCard`; `3/3` typed intakes validated as `RepresentativeSelectionIntake`. |
| Selector-oracle compatibility | Pass, compatibility only | `PAF-T02-001` through `PAF-T02-003` each produced `single_representative: INC-014` under a reconstructed PR #18 strict-dominance selector. |
| Procedure-neutral control | Pass | PAV-001 and PAV-002 preserve selection signatures and non-procedure card fields; only procedure-list fields differ set-to-set. |
| Test-only containment | Attested | The governance registry prohibits active-policy, retrieval, selector-calibration, E1, and production load paths. |

## Blocking finding: undeclared procedure mutation

`PAF-AUDIT-001-F01`

| Field | Evidence |
|---|---|
| Controlled card | `PAV-001-procedure-asymmetric/INC-013` |
| Declared source card | `INC-009` |
| Source `unsafe_procedure_ids` | `["RB-002"]` |
| Controlled `unsafe_procedure_ids` | `[]` |
| Governance-declared perturbations | `incident_id`, `title` |
| Missing declaration | `unsafe_procedure_ids` |

The actual changed fields are:

```text
incident_id
title
unsafe_procedure_ids
```

The governance registry declares only:

```text
incident_id
title
```

The fixture is specifically designed to test that procedure metadata cannot alter representative selection. Therefore every procedure-field perturbation must be mechanically declared. Leaving one mutation undeclared makes the adversarial condition unauditable.

## Case disposition

| Case | Disposition | Reason |
|---|---|---|
| `PAF-T02-001` | Conditionally retain after V2 provenance correction | Primary adversarial property is diagnostic and the expected outcome is contract-compatible. |
| `PAF-T02-002` | Conditionally retain after V2 provenance correction | Valid order-reversal partner; shares the primary card set and provenance blocker. |
| `PAF-T02-003` | Conditionally retain after V2 provenance correction | Valid procedure-neutral control; shares the proposal manifest and reviewed lineage. |

## Required V2 correction

Do not modify this reviewed proposal in place. Reissue a new archive with a new manifest.

The minimal correction is:

1. Add `unsafe_procedure_ids` to the PAV-001 / INC-013 `field_level_perturbations_from_source` registry entry.
2. Record that removal of source `RB-002` is a test-only isolation step for the intended `RB-003` availability asymmetry.
3. Recompute all affected file and aggregate hashes.
4. Add a deterministic derivation assertion: for every controlled card, actual changed fields must exactly equal declared perturbation fields.
5. Preserve the three runtime-input assets and three expected-outcome assets byte-for-byte.

### Inputs that must remain byte-identical

```text
PAF-T02-001.input.json  a40190593160a369002d3b5ef65e4ca2da01bafdd4032b3a69bace463cb88239
PAF-T02-002.input.json  d49be9364e4fe1026d4045739a76f61567b37e9910c0c605c78b07e1c0daeb8a
PAF-T02-003.input.json  c1d9cc827e49f4aead69c11c9efca6d2935f6938e86fb5759f575fd4776b11ec
```

### Expected outcomes that must remain byte-identical

```text
PAF-T02-001.expected.json  2fff96e617c582a845cf065859656ee3c3928341d2070570a7678c92e48d4cf1
PAF-T02-002.expected.json  6fdbe0d5cbdf559486e86c9223566d0bcfec10d6a4e0a995a2b8dc488086a3ea
PAF-T02-003.expected.json  58703aceb062cf164f1aa09f605add3ad7556663f9f757320a7dbe6889d38961
```

## Non-claims

- No Tranche 02 fixture is accepted, frozen, imported, or evaluated.
- No selector activation is authorized.
- No active policy, procedure, retrieval, retained precedent, missing-fact, or decision-state behavior has changed.
- The selector compatibility check is not a formal Tranche 02 comparison result.
