# ADR-0016: Legacy Rank-Sensitivity Counterfactual Clarification

## Status

**Accepted for E1 planning.**

This ADR corrects an infeasible counterfactual invariant in ADR-0015 before
admission-preserving shadow-integration code is merged.

## Context

ADR-0015 correctly separated two concerns:

1. exact active-policy invariance for identical inputs; and
2. strict-dominance trace invariance under same-family candidate-order reversal.

It also attempted to require that a counterfactual reversal of the ranked policy
input preserve the active policy's decision state, procedure IDs, missing facts,
and conflict summary.

A focused E1 implementation check showed that this is not true for the current
legacy policy.

For the existing `EVAL-009` calibration input:

```text
canonical ranked order
-> first compatible connection-pool card: INC-009
-> evidence_found
-> RB-003 eligible

reversed ranked order
-> first compatible connection-pool card: INC-012
-> missing_critical_facts
-> procedures withheld
```

The state changes because the legacy policy computes missing facts and procedure
eligibility from the **first retained card per family**. Different same-family
cards have different required verification facts and procedure prerequisites.

This is not a shadow-integration regression. It is an existing legacy coupling
between retrieval order, visible representative card choice, decision state, and
procedure visibility.

E1 must not hide, normalize, or repair that coupling. Doing so would change the
active policy contract during a trace-only slice.

## Decision

### 1. Same-input public invariance remains the E1 hard gate

For identical policy inputs, including identical ranked candidate order:

```text
baseline AntiAnchoringDecisionPolicy.evaluate(...)
==
AntiAnchoringDecisionPolicy.evaluate_with_shadow(...).policy_result
```

Every public `PolicyDecisionResult` field must remain identical.

### 2. Shadow trace order invariance remains required

For a fixed policy-admitted same-family candidate pool and fixed typed
`RepresentativeSelectionIntake`:

```text
candidate order A
-> shadow strict-dominance trace

candidate order B
-> identical shadow strict-dominance trace
```

The strict-dominance trace must remain invariant for:

- selection state;
- representative IDs or explicit tie set;
- candidate evidence relationships; and
- unavailable or bypass reason.

The shadow trace must never become a lexical-rank or identifier fallback.

### 3. Reversed policy-rank behavior is diagnostic observation, not an E1 gate

A counterfactual reversal of the **policy ranked candidates** may change legacy
public behavior. E1 must therefore record, not require equality for, all of the
following fields:

```text
- decision_state;
- retained_precedent_ids;
- candidate_procedure_ids;
- missing_critical_facts;
- conflict_summary; and
- safety_notes.
```

For each ordering, E1 must still prove same-input shadow invariance:

```text
active policy result for order A
==
shadow policy result for order A

active policy result for order B
==
shadow policy result for order B
```

A cross-order difference is a **legacy rank-sensitivity observation**. It is not
an activation signal, not a shadow failure, and not a reason to change the public
policy result in E1.

### 4. The observation becomes a future activation constraint

Any future representative-selection activation proposal must explicitly address
that legacy rank sensitivity exists beyond presentation metadata. It affects
missing-fact and procedure behavior.

Therefore, activation requires a separate ADR that defines how a selected or tied
same-family evidence set interacts with:

- missing-fact aggregation;
- procedure eligibility;
- cross-family conflict precedence;
- explicit within-family ties; and
- the public `PolicyDecisionResult` contract.

No such change is permitted in E1 or Tranche 02 authoring.

## Revised E1 Acceptance Criteria

E1 may proceed only when all of the following pass:

1. exact public-result invariance for every existing calibration case with
   identical ranked input;
2. provider-degraded and insufficient-precedent paths invoke no selector;
3. one admitted card yields a deterministic single-candidate bypass trace;
4. multiple admitted cards with no typed selection intake yield explicit
   trace-safe `unavailable` behavior;
5. typed connection-pool bridge input yields trace-only selector output;
6. explicit within-family ties do not change procedure visibility;
7. cross-family conflict remains unchanged and withholds procedures;
8. shadow trace outputs are invariant when the admitted same-family candidate
   order is reversed;
9. counterfactual legacy rank sensitivity is fully reported, including every
   changed public policy field, without being normalized or repaired; and
10. no held-out assets, freeze manifests, baseline comparisons, or promotion
    reports are loaded.

## Non-Claims

This ADR does not:

- change `AntiAnchoringDecisionPolicy` public behavior;
- change missing-fact aggregation or procedure eligibility;
- activate strict-dominance selection;
- create, load, freeze, or compare Tranche 02;
- reopen Tranche 01;
- claim that legacy policy behavior is order-invariant;
- establish a safe activation path; or
- establish production readiness.
