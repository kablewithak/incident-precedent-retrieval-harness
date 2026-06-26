# ADR-0017: Admission-Preserving Shadow Selection Integration

## Status

**Accepted for E1 shadow integration only.**

## Context

The repository now has:

1. a deterministic anti-anchoring policy that owns final decision state,
   missing-fact, conflict, and procedure behavior;
2. schema-derived representative-selection contracts for connection-pool cards;
3. a calibrated strict-dominance selector that remains non-authoritative; and
4. ADR-0016's documented legacy rank sensitivity under counterfactual changes to
   ranked candidates.

The policy previously discarded later compatible cards in an incident family
before a selector could inspect them. E1 needs the full compatibility-admitted
same-family pool while preserving every active `PolicyDecisionResult` field for
identical inputs.

## Decision

Add `AntiAnchoringDecisionPolicy.evaluate_with_shadow(...)` beside the existing
`evaluate(...)` method.

Both methods call the same private evaluation core. The core preserves the
legacy first-compatible-card public behavior while also retaining a private,
trace-safe `FamilyAdmissionSet` for every compatibility-admitted family.

```text
ranked candidates
-> compatibility assessment
-> complete family admission set (shadow-only)
-> legacy first-compatible retained card (active contract unchanged)
-> policy decision state / procedure gate
-> optional typed same-family selection trace
```

`evaluate(...)` still returns only `PolicyDecisionResult`.

`evaluate_with_shadow(...)` returns:

```text
PolicyShadowEvaluationResult
- policy_result
- family_admission_sets
- selection_traces
```

The shadow result is an internal calibration artifact. It is not a new product
response contract and cannot alter the active policy result.

## Typed Bridge Contract

Normal `EvalCase` remains unchanged. E1 accepts a separate
`PolicyShadowRequest` containing explicit `FamilySelectionIntakeBinding` values.

A binding may contain only:

```text
incident_family
RepresentativeSelectionIntake
```

No runtime path derives selection evidence from:

- `input_summary` free text;
- retriever rank, score, or matched terms;
- incident identifier order;
- procedure metadata;
- evaluation labels; or
- held-out data.

## Trace States

For every policy-admitted family, shadow evaluation emits one of these states:

```text
not_applicable_single_candidate
unavailable
single_representative
explicit_tie
```

They are trace states, not evidence decision states.

- One admitted card produces `not_applicable_single_candidate` without calling
  the selector.
- Missing typed selection input produces `unavailable` without lexical fallback.
- Unsupported families produce `unavailable` even when typed input is supplied.
- A missing schema-derived signature produces `unavailable` without a rank or ID
  fallback.
- Only a typed, supported, multi-card connection-pool family may call the
  strict-dominance selector.

## Invariants

E1 must preserve all of the following.

1. **Same-input public invariance**: for identical ranked candidates,
   `evaluate(...) == evaluate_with_shadow(...).policy_result` across every public
   `PolicyDecisionResult` field.
2. **Decision ownership**: only the active policy assigns the five typed evidence
   decision states.
3. **Procedure invariance**: selection traces never surface, suppress, reorder,
   or prefer a procedure.
4. **Cross-family conflict preservation**: a family-level shadow representative
   cannot resolve an active cross-family conflict.
5. **Tie safety**: an explicit within-family tie remains trace-only.
6. **Order invariance of selection traces**: a fixed admission set and fixed typed
   selection intake produce the same trace under candidate-order reversal.
7. **Legacy rank sensitivity observation**: counterfactual reversal of policy
   ranked candidates may alter legacy policy fields. E1 reports that difference;
   it does not normalize or repair it.
8. **No held-out dependency**: the E1 runner loads only incidents, procedures,
   calibration cases, and E1 shadow bridge fixtures.

## Calibration Evidence

The E1 fixture set contains eight explicit bridge cases covering:

- provider-degraded bypass;
- insufficient-precedent bypass;
- absent typed intake;
- typed connection-pool single representative;
- explicit within-family tie;
- cross-family conflict with procedure withholding;
- unsupported-family unavailability; and
- no lexical fallback.

The runner also checks every existing policy calibration case for exact
same-input public-result invariance and records the EVAL-009 legacy
rank-sensitivity counterfactual.

## Non-Claims

This ADR does not:

- activate representative selection;
- alter retained precedent IDs;
- alter missing-fact aggregation;
- alter procedure eligibility or procedure visibility;
- alter retrieval;
- reopen Tranche 01;
- create or compare Tranche 02;
- claim a representative-selection improvement; or
- claim production readiness.
