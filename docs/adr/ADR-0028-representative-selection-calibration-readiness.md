# ADR-0028: Representative-Selection Calibration Readiness Gate

- **Status:** Accepted
- **Date:** 2026-06-27
- **Decision owners:** Incident Precedent Retrieval Harness
- **Scope:** Standalone `connection_pool_exhaustion` representative-selection calibration only

## Context

The frozen EVAL-110 autopsy established a real boundary failure:

```text
Expected retained evidence: INC-003, INC-009
Active-policy retained evidence: INC-003, INC-012
```

The decision state remained correct. The divergence was within-family representative
selection: `INC-009` and `INC-012` are both connection-pool candidates, while the
active policy intentionally retains the first compatible card in a family.

A strict-dominance selector already exists as a schema-first, calibration-only
component. Its fixed calibration suite contains typed candidate signatures,
explicit-tie cases, and an exact reversed-order pair. It is not active policy
authority.

The autopsy does not authorize copying EVAL-110 into calibration or tuning the
selector to match its held-out label. That would contaminate the frozen tranche.

## Decision

Add a write-once calibration-readiness gate that:

1. Loads only `data/evals/selection_calibration/` and approved incident cards.
2. Runs the standalone strict-dominance selector against every fixed calibration case.
3. Measures exact expected-state and representative-ID parity.
4. Measures order invariance only through fixed canonical/reversed fixture pairs.
5. Confirms candidate scope remains limited to `connection_pool_exhaustion`.
6. Emits one explicit decision:

```text
calibration_passed_activation_blocked
calibration_blocked
insufficient_evidence
```

7. Writes a separately named JSON and Markdown evidence pair once.

A passing calibration result must still state that activation is blocked.

## Why activation remains blocked after calibration pass

Calibration proves the selector matches its known typed contract. It does not prove
that activating it inside the anti-anchoring policy will preserve safety on unseen
cases.

Activation requires, at minimum:

- a separate activation ADR;
- an independently authored future held-out tranche that is not reused as
  selector-calibration material;
- a new policy-integrated promotion gate;
- explicit regression review across all active incident families.

## Consequences

### Positive

- The project separates selector correctness from selector authority.
- Candidate order remains measured as a non-authoritative invariant.
- The EVAL-110 failure does not become a hidden rank patch or held-out tuning loop.
- Future activation can be assessed against a clear decision record.

### Negative

- The immediate output remains an activation block even if calibration is perfect.
- The selector remains limited to one incident family.
- This does not yet resolve the frozen EVAL-110 outcome.

These are deliberate constraints. Evidence-first boundaries are preferable to
promoting a narrowly calibrated selector into a safety-sensitive path.

## Alternatives rejected

### Activate strict dominance after its existing calibration report

Rejected. Existing calibration is necessary but does not test policy integration or
independent future cases.

### Change EVAL-110 expected IDs to match current active rank order

Rejected. The held-out manifest is frozen. Changing it would erase diagnostic
evidence.

### Use EVAL-110 as a new calibration fixture

Rejected. The label and outcome have already been observed. Reusing it would
contaminate future selection calibration.

### Patch active policy ordering directly

Rejected. Incident IDs, lexical rank, and case-specific retrieval order are not a
reviewed representative-selection contract.

## Verification

The implementation must prove:

- all fixed selection calibration cases are evaluated;
- fixed contract parity is measured exactly;
- the canonical/reversed order pair is invariant;
- no held-out or retrieval path is loaded;
- active policy and selector authority remain unchanged;
- evidence cannot be overwritten.

## Non-claims

This ADR does not activate selector output, modify retrieval, authorize a procedure,
claim held-out improvement, establish production readiness, or validate customer
data.
