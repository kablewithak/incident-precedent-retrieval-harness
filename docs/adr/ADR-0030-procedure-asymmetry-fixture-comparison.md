# ADR-0030: Procedure-Asymmetry Fixture Comparison Boundary

- **Status:** Accepted
- **Date:** 2026-06-27
- **Decision owners:** Incident Precedent Retrieval Harness
- **Scope:** Imported, test-only procedure-asymmetry fixture and isolated strict-dominance selector

## Context

PR #37 imported the accepted V2 procedure-asymmetry fixture only after verifying
its archive topology, manifest inventory, raw asset hashes, aggregate hashes,
typed schemas, controlled-card provenance, and isolated selector oracle.

Import evidence alone proves that a governed fixture was copied into the repository.
It does not provide a separately inspectable comparison report that can detect:

- post-import fixture drift;
- candidate-order leakage;
- procedure-metadata leakage;
- accidental use of a global incident map that collapses two controlled card sets
  sharing the same incident identifiers.

The fixture deliberately contains:

- a primary procedure-asymmetric case where `INC-013` has a more favourable
  test-only procedure posture, appears first, and has the lower identifier;
- an exact reversed-order partner;
- a procedure-neutral control with matching typed selection signatures.

## Decision

Add a write-once comparison harness that:

1. Requires the existing write-once import receipt to prove an
   `imported_test_only` import with the accepted V2 counts.
2. Re-verifies the current imported fixture file set, asset hashes, byte counts,
   and manifest aggregate hashes before evaluation.
3. Loads only fixture-local controlled cards, runtime inputs, and separately
   stored expected outcomes.
4. Preserves controlled-card-set identity. It never flattens repeated incident IDs
   across the procedure-asymmetric and procedure-neutral card sets.
5. Evaluates the standalone strict-dominance selector against all three accepted
   cases.
6. Measures exact state and representative-ID parity, order invariance, and
   procedure-neutral control parity.
7. Records expected reason codes only as evaluator diagnostics. They are never
   passed to the selector.
8. Emits one decision:

```text
comparison_passed_activation_blocked
comparison_blocked
insufficient_evidence
```

9. Writes a separately named JSON and Markdown evidence pair once.

## Consequences

### Positive

- The imported fixture cannot silently drift after import.
- Candidate-order and procedure-metadata leakage are regression-tested from
  actual controlled cards, not inferred from a report summary.
- The harness preserves the intentional duplicate incident IDs across controlled
  card sets without making identifier order a selection input.
- The evidence chain is inspectable: import receipt → manifest integrity →
  comparison result.

### Negative

- The harness is intentionally limited to three test-only cases and one incident
  family.
- A passing result still does not change `AntiAnchoringDecisionPolicy`.
- A passing result is not independent future held-out activation evidence.

## Alternatives rejected

### Treat the import receipt as sufficient comparison evidence

Rejected. The receipt proves import-time validation but cannot detect later on-disk
fixture drift or establish a distinct comparison trace.

### Load controlled cards into one global incident-ID map

Rejected. `INC-013` and `INC-014` exist in two card sets with different procedure
postures. A global map would silently erase the adversarial/control distinction.

### Pass expected reason codes into the selector

Rejected. They are evaluator diagnostics and would contaminate the model boundary
with outcome material.

### Activate strict dominance when the comparison passes

Rejected. Activation requires a separate ADR, policy-integration evidence,
independently authored future held-out cases, and a promotion gate.

## Verification

The implementation must prove:

- import receipt preconditions are satisfied;
- imported manifest inventory and aggregate hashes still match disk;
- all three fixture cases evaluate;
- the primary and reversed-order partner retain the same result;
- the procedure-asymmetric and procedure-neutral variants retain the same
  typed-selection result;
- no retrieval, held-out, active-policy, or selector activation path is used;
- comparison reports cannot be overwritten.

## Non-claims

This ADR does not freeze Tranche 02, modify active policy, change retrieval,
authorize procedures, establish customer-data readiness, or claim production
readiness.
