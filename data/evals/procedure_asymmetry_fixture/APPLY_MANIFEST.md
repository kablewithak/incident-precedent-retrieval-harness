# APPLY MANIFEST — Procedure-Asymmetry Adversarial Fixture Proposal

## Status

`PROPOSAL_ONLY_NOT_FROZEN_NOT_EVALUATED`

This archive is a governed test-only proposal. It must not be copied into `data/incidents`, active procedure data, active-policy fixtures, selector-calibration fixtures, E1 fixtures, retrieval paths, or production configuration.

## Required layout

```text
proposed_procedure_asymmetry_fixture/
  inputs/
    cases/
    controlled_cards/
    governance/
  expected_outcomes/
  manifest.json
  authoring_ledger.md
  rejected_case_ideas.md
  APPLY_MANIFEST.md
```

## Case composition

A complete case is intentionally distributed across four isolated assets:

1. `inputs/cases/<case_id>.input.json` — runtime case envelope; contains the typed selection intake, candidate IDs, family, source IDs, and controlled card-set ID. It contains no expected outcome or rationale.
2. `inputs/controlled_cards/<card_set_id>/` — case-scoped, test-only `HistoricalIncidentCard` variants. Each set must be loaded only for the case(s) that reference it.
3. `inputs/governance/procedure_asymmetry_governance.json` — test-only provenance, perturbation, and containment metadata. It must never be passed to the selector and contains no expected representative or oracle rationale.
4. `expected_outcomes/<case_id>.expected.json` — reviewer-controlled expected outcome and oracle rationale. It must remain unavailable to runtime selector code until comparison time.

## Future harness preconditions

A future Tranche 02 fixture validator/comparison harness must, before selector execution:

1. validate every `selection_intake` as `RepresentativeSelectionIntake`;
2. validate every selected controlled card as `HistoricalIncidentCard`;
3. load cards case-by-case, not as a global incident corpus;
4. reject card-set, candidate-ID, family, or source-derivation mismatches before selection;
5. verify the candidate pool belongs to one incident family;
6. verify that `PAV-001` and `PAV-002` differ only in the declared procedure-list fields after canonical normalization;
7. pass only the typed intake and validated cards/signatures to the selector;
8. withhold `expected_outcomes/` and governance metadata until the comparison phase;
9. classify any mismatch with the Tranche 02 failure taxonomy, without mutating fixtures after a run.

## Required assertions when this proposal is evaluated

- The primary adversarial case must match its reviewer-controlled expected-outcome asset even though a competing candidate has more favorable test-only procedure metadata, the lower incident ID, and first input position.
- The order-reversal partner must produce the same expected representative as the primary case.
- The procedure-neutral control must preserve the same expected typed-selection outcome as the primary case.
- Any invalid card, intake, family, card-set mapping, or manifest mismatch fails closed before selector execution.
- The fixture cannot be loaded by active policy, retrieval, or production paths.

## Integrity verification

`manifest.json` records SHA-256 and byte counts for every proposal asset except itself, plus deterministic aggregate hashes for input, expected-outcome, governance, and documentation asset groups. Aggregate hashes are SHA-256 of UTF-8 lines sorted by relative path in this exact form:

```text
<relative-path>\x00<file-sha256>\x00<byte-count>\n
```

The archive itself is not an activation or freeze artifact. A reviewer must create new frozen manifests and record the evaluated selector and repository commits before any formal Tranche 02 run.

## V2 provenance remediation controls

This V2 reissue is the only approved remediation surface from the reviewed V1
proposal. It adds `inputs/governance/controlled_card_derivation_assertions.json`
and declares `unsafe_procedure_ids` for `PAV-001-procedure-asymmetric` /
`INC-013`.

The assertion file must be verified before any selector comparison. It records,
for each controlled card, source and controlled digests, actual changed fields,
declared permitted fields, and exact field-set equality.

The V2 manifest inventories every non-manifest asset with `relative_path`,
`sha256`, `byte_count`, and `group`. Aggregate hashes are SHA-256 over
path-sorted canonical JSON inventory records with those four fields. This
integrity rule supersedes the V1 line-encoding description above for this V2
reissue only.
