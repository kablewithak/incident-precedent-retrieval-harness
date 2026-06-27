# Procedure-Asymmetry Fixture Import

## Scope

This write-once receipt records validation and isolated import of the accepted test-only procedure-asymmetry fixture proposal.
It does not load active policy, retrieval, held-out evaluation, or provider infrastructure.

## Decision

**Decision: IMPORTED_TEST_ONLY**

## Integrity summary

- Proposal archive: `procedure-asymmetry-adversarial-fixture-proposal-v2.zip`
- Proposal archive SHA-256: `86603235f0c4c3e0de47ba2a4fd07a62fc49495d53a366e832cd4f27934c40b8`
- Non-manifest assets verified: `15`
- Controlled cards: `4`
- Runtime cases: `3`
- Expected outcomes: `3`
- Derivation assertions: `4`
- Imported fixture path: `data/evals/procedure_asymmetry_fixture`

## Aggregate verification

| Aggregate | Formula | Result |
|---|---|---|
| inputs_sha256 | canonical_json_inventory_records_v2 | pass |
| expected_outcomes_sha256 | canonical_json_inventory_records_v2 | pass |
| governance_sha256 | canonical_json_inventory_records_v2 | pass |
| documentation_sha256 | canonical_json_inventory_records_v2 | pass |
| all_non_manifest_assets_sha256 | canonical_json_inventory_records_v2 | pass |

## Isolated selector outcomes

| Case | Expected | Actual | Result |
|---|---|---|---|
| PAF-T02-001 | single_representative: INC-014 | single_representative: INC-014 | pass |
| PAF-T02-002 | single_representative: INC-014 | single_representative: INC-014 | pass |
| PAF-T02-003 | single_representative: INC-014 | single_representative: INC-014 | pass |

## Non-claims

- This imports an isolated, test-only evaluation fixture; it does not add cards to data/incidents or procedures to data/procedures.
- This run does not load retrieval, held-out cases, or AntiAnchoringDecisionPolicy.
- The strict-dominance selector remains isolated and non-authoritative after this import.
- The report does not freeze Tranche 02, authorize selector activation, authorize procedures, or establish production or customer-data readiness.
