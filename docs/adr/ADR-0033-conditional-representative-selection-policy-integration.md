# ADR-0033: Conditional Representative-Selection Policy Integration

- **Status:** Accepted for implementation; not yet active
- **Date:** 2026-06-27
- **Decision owner:** Incident Precedent Retrieval Harness
- **Related evidence:**
  - ADR-0013 calibration-only strict-dominance selector
  - procedure-asymmetry fixture import and comparison receipts
  - Tranche 02 future-held-out freeze receipt
  - Tranche 02 future-held-out comparison receipt
- **Scope:** Local, synthetic-data, evaluation harness only

## Context

The repository contains `StrictDominanceRepresentativeSelector`, a deterministic,
typed selector that compares only:

- service alignment;
- component alignment;
- change-context alignment;
- matching operational-signal families; and
- contradicted operational-signal families.

It does not use retrieval rank, candidate order, incident identifiers as a
tie-breaker, procedure metadata, procedure availability, active-policy state,
or evaluator outcomes.

The selector has passed:

1. calibration-only representative-selection evidence;
2. a governed procedure-asymmetry regression fixture;
3. a frozen, independently authored Tranche 02 comparison:
   - 10/10 valid selector cases matched the frozen oracle;
   - 2/2 invalid or mixed-family controls rejected before selector execution;
   - candidate-order invariance passed.

Those results prove isolated selector conformance. They do not by themselves
authorize a change to the active incident-evidence policy.

## Decision

Approve a **narrow policy-integration implementation** for
`connection_pool_exhaustion` only. This ADR does not itself activate the
selector.

The integration must preserve the existing `AntiAnchoringDecisionPolicy` as the
sole authority for:

- admission or rejection of historical evidence;
- all five top-level evidence decision states;
- missing-critical-fact behavior;
- conflict behavior;
- procedure eligibility and withholding;
- provider-degraded behavior; and
- human-review requirements.

The selector is permitted only as a post-admission representative-refinement
step for an already policy-admitted, same-family candidate pool.

## Integration contract

The future implementation may invoke representative selection only when all
conditions hold:

1. the existing policy has already admitted at least two historical candidates;
2. every admitted candidate belongs to `connection_pool_exhaustion`;
3. every candidate has a schema-derived `selection_signature`;
4. a validated `RepresentativeSelectionIntake` is available; and
5. the top-level policy result is not `provider_degraded` or
   `insufficient_precedent`.

The policy must call the selector with only:

```text
validated RepresentativeSelectionIntake
candidate incident IDs from the policy-admitted pool
the corresponding approved historical incident cards
```

### Permitted effect

- `single_representative` may narrow the displayed representative-precedent set
  to the one strict-dominance winner.
- `explicit_tie` must preserve the complete non-dominated candidate set.
- The output must include trace-safe selection status and reason evidence.

### Prohibited effect

The integration must not allow selector output to:

- set or override a top-level evidence decision state;
- suppress a policy-detected conflict;
- make a procedure eligible or ineligible;
- change missing-fact requirements;
- alter provider-degraded handling;
- alter retrieval candidate generation, scores, or rank;
- consume expected-outcome files, held-out labels, procedure metadata, or
  procedure availability;
- use candidate serialization order or incident identifiers as a preference
  signal; or
- authorize remediation or procedure execution.

## Fail-closed behavior

If selector preconditions are not met, or if `SelectionInputError` occurs:

1. do not select a representative;
2. preserve the complete existing policy-admitted candidate set;
3. leave the existing top-level policy decision unchanged;
4. record a trace-safe `selection_not_applied` status and reason; and
5. do not silently substitute retrieval rank, candidate order, or procedure
   metadata as a tie-breaker.

Unsupported incident families remain selector-ineligible until separately
evaluated, governed, and approved.

## Required implementation evidence

The activation implementation PR must include:

1. a typed integration result model or equivalent validated boundary;
2. unit tests demonstrating that all five top-level policy states remain
   policy-owned;
3. tests for single-winner narrowing, explicit-tie preservation, invalid
   selector input, unsupported-family bypass, and absent-signature bypass;
4. tests proving procedures, required facts, and top-level state are unchanged
   by the selector;
5. tests proving selector errors preserve the policy-admitted set rather than
   creating an arbitrary winner;
6. a recorded activation-readiness report with:
   - existing-policy baseline;
   - policy-integrated intervention;
   - fixed cases;
   - failure labels;
   - trace review fields; and
   - explicit activation decision;
7. `python -m pytest .\tests\unit` passing; and
8. no edits to frozen Tranche 02 assets, freeze receipt, or comparison receipt.

The Tranche 02 comparison must not be rerun or overwritten. It remains an
immutable evidence record.

## Consequences

### Positive

- The local demo can represent one carefully constrained,
  typed representative-selection behavior.
- The system preserves ambiguity rather than manufacturing a winner.
- The active policy remains the safety authority.

### Costs and limits

- Activation scope is intentionally one incident family only.
- The selector cannot resolve cross-family ambiguity.
- A passing isolated selector does not establish production readiness,
  customer-data safety, or operational incident-response effectiveness.

## Non-claims

This decision does not:

- authorize production deployment;
- authorize customer-data ingestion;
- authorize automated remediation or procedure execution;
- claim that retrieval is correct or that incidents are diagnosed;
- establish support for other incident families; or
- replace the active anti-anchoring policy with the selector.
