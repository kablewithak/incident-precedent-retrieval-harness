# ADR-0015: Shadow-Integration Order-Invariance Clarification

## Status

**Accepted for E1 planning.**

This ADR corrects one infeasible E1 proof obligation in ADR-0014 without
activating representative selection or changing runtime policy behavior.

## Context

ADR-0014 correctly requires that the strict-dominance selector must not use
retrieval rank, lexical score, candidate-list order, or identifiers as a
selection tie-break.

It also correctly keeps the first integration slice shadow-only:

```text
- PolicyDecisionResult remains the external result.
- retained_precedent_ids remain produced by the current policy contract.
- candidate_procedure_ids remain produced by the current policy contract.
- selection output is trace-only.
```

However, ADR-0014 also stated that reversing candidate order must change neither
the shadow-selection outcome nor the active policy result.

The current `AntiAnchoringDecisionPolicy` exposes `retained_precedent_ids` and
implements its legacy visible representative behavior by retaining the first
compatible ranked card within an incident family. Therefore, a counterfactual
reversal of two compatible same-family ranked candidates can change the legacy
visible retained incident ID even when decision state, missing facts, and
procedure behavior remain unchanged.

E1 cannot make the entire existing `PolicyDecisionResult` order-invariant
without doing one of the following unsafe things:

```text
1. changing the public policy contract during a shadow-only slice;
2. introducing a new hidden representative tie-breaker; or
3. using incident identifiers as a representative-selection rule.
```

All three are prohibited by ADR-0014.

## Decision

Clarify the E1 proof obligations as follows.

### 1. Same-input active-policy invariance

For identical inputs, including identical ranked candidate order:

```text
baseline active policy result
==
shadow-enabled active policy result
```

Equality covers every public `PolicyDecisionResult` field:

```text
- decision_state
- retained_precedent_ids
- candidate_procedure_ids
- missing_critical_facts
- conflict_summary
- assessments
- safety_notes
```

### 2. Shadow-selection order invariance

For a fixed same-family admitted candidate set and fixed typed
`RepresentativeSelectionIntake`:

```text
candidate order A
-> shadow selection outcome

candidate order B
-> identical shadow selection outcome
```

The following shadow fields must be invariant:

```text
- selection_state
- representative_incident_ids
- candidate evidence relationships
- unavailable / bypass reason where selection is not invoked
```

Identifiers may be sorted only for deterministic trace serialization after the
selector has already determined the non-dominated set.

### 3. Legacy-policy rank-sensitivity is observed, not repaired

For counterfactual candidate-order reversals, E1 must prove that the following
active-policy safety semantics remain unchanged:

```text
- decision_state
- candidate_procedure_ids
- missing_critical_facts
- conflict summary / cross-family withholding behavior
```

If `retained_precedent_ids` changes because the legacy first-compatible policy
exposes a different same-family card, that difference must be recorded as
**legacy representative rank sensitivity**. It is not an E1 failure and must
not be hidden, normalized, or used to activate the selector.

### 4. Activation remains blocked

No selector output may replace, reorder, suppress, or promote
`retained_precedent_ids` in E1.

Any future change to the public representative shown in `PolicyDecisionResult`
requires:

```text
- a separate activation ADR;
- a frozen Tranche 02;
- a predeclared comparison;
- zero decision-state regressions;
- zero unsafe procedure-surfacing regressions;
- correct explicit-tie behavior; and
- no lexical, score, list-order, or identifier fallback.
```

## Revised E1 Acceptance Criteria

E1 may proceed only when its shadow runner proves:

1. exact public-result invariance for each existing calibration case run with
   identical retrieval output;
2. provider-degraded and insufficient-precedent paths invoke no selector;
3. one admitted card yields a deterministic single-candidate bypass trace;
4. multiple admitted cards with no typed selection intake yield an explicit,
   trace-safe unavailable result;
5. typed connection-pool input produces only a selector trace, never public
   output changes;
6. selector trace outputs are invariant to candidate order;
7. cross-family conflict and procedure withholding remain unchanged;
8. any counterfactual legacy retained-ID difference is reported as legacy rank
   sensitivity rather than silently repaired;
9. no held-out assets, freeze manifests, baseline comparisons, or promotion
   artifacts are loaded.

## Non-Claims

This ADR does not:

- modify `AntiAnchoringDecisionPolicy`;
- modify `PolicyDecisionResult`;
- activate representative selection;
- alter procedure eligibility;
- change retrieval behavior;
- create, load, freeze, or compare Tranche 02;
- reopen Tranche 01;
- claim representative-selection improvement, production readiness, or
  customer-data validation.
