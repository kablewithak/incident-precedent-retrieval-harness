# ADR-0014: Strict-Dominance Integration Boundary and Tranche 02 Preconditions

## Status

**Accepted for integration design only.**

This ADR does not connect the strict-dominance selector to
`AntiAnchoringDecisionPolicy`, change normal evidence packets, add a new decision
state, load held-out data, or authorize a Tranche 02 comparison.

## Context

The repository now has three distinct, committed assets:

```text
1. AntiAnchoringDecisionPolicy
   - decides whether a ranked historical card is compatible enough to remain
     candidate evidence;
   - owns the five typed decision states;
   - controls missing-fact and procedure-withholding behavior.

2. Schema-derived selection contracts
   - RepresentativeSelectionIntake;
   - validated card selection_signature values;
   - cardinality and provenance-like source-field constraints.

3. StrictDominanceRepresentativeSelector
   - calibration-only;
   - compares already-admitted cards within connection_pool_exhaustion;
   - returns a single representative only when one card strictly dominates;
   - otherwise preserves the non-dominated set as an explicit tie.
```

The isolated selector calibration passed all ten dedicated fixtures. That is useful
evidence about the selector contract. It is not evidence that the active
anti-anchoring policy may be changed.

The integration review found two material gaps.

### Gap 1: the active policy loses the candidate pool too early

`AntiAnchoringDecisionPolicy.evaluate(...)` currently iterates ranked candidates,
retains the first compatible card for each incident family, and suppresses later
compatible cards in the same family.

Current shape:

```text
ranked candidates
-> compatibility assessment
-> first retained card per family
-> PolicyDecisionResult
```

This means the selector cannot be inserted after the current loop: by that point,
the policy has already discarded the same-family cards the selector must compare.

### Gap 2: normal policy evaluation has no typed selection intake

The active policy consumes `EvalCase`, whose structured facts support compatibility,
missing-fact, and procedure rules. `EvalCase` does not contain
`RepresentativeSelectionIntake`.

The strict-dominance selector deliberately requires separate typed evidence:

```text
service
component
change_context
operational_signal_families
contradicted_signal_families
```

It must not infer those values from free text, retrieval score, evaluation labels,
or an untracked cue layer.

Therefore, activation cannot be a narrow call to the selector inside
`policy.py`. It requires an explicit integration contract and separate
calibration/hold-out assets.

## Decision

Use a staged integration path that preserves the existing policy as the admission
authority and proves integration behavior before it can alter evidence selection.

```text
retrieval
-> policy admission (all compatible cards retained internally by family)
-> policy decision-state precedence
-> same-family selection shadow trace
-> explicit representative or explicit tie
-> future activation only after Tranche 02
```

The immediate next implementation must be an **admission-preserving refactor with
shadow-only selection tracing**, not active representative replacement.

## Core Invariants

The following must remain true through all integration work.

### Decision-state ownership

Only `AntiAnchoringDecisionPolicy` assigns the existing final states:

```text
provider_degraded
insufficient_precedent
evidence_found_with_conflict
missing_critical_facts
evidence_found
```

The selector must not assign, replace, or reinterpret these states.

### State precedence

The active precedence remains:

```text
1. provider_degraded
2. insufficient_precedent
3. evidence_found_with_conflict
4. missing_critical_facts
5. evidence_found
```

A representative-selection outcome is presentation/evidence-selection metadata,
not a sixth decision state.

### Admission before selection

A selector input may contain only cards that the compatibility policy already
admitted.

```text
policy-rejected card
-> never reaches selector

selector result
-> never revives a rejected card
```

### No silent lexical fallback

When strict dominance cannot select one card, the result is an explicit
non-dominated tie.

The integration may not recover the old behavior:

```text
first lexical candidate
-> hidden same-family representative
```

Identifiers may be sorted only for deterministic serialization after the tie set
is already determined.

### Procedure safety remains more conservative than selection

The selector has no authority to make a procedure eligible.

A future activation must keep procedure visibility governed by deterministic
procedure eligibility and must prove that a within-family tie cannot silently
select or privilege a procedure. If tied cards imply different eligible procedure
paths, the policy must preserve human review and withhold a preferred procedure.

### Missing facts remain policy facts

`required_verification_facts` remain verification and procedure-safety inputs.
They are not a strict-dominance dimension and are not counted as positive selection
evidence.

### Failure does not become false confidence

If a same-family candidate pool cannot be selected because a typed selection intake
is unavailable, a schema signature is missing, or the family is unsupported:

```text
- do not use lexical rank;
- retain the policy-safe candidate set;
- record a trace-safe selection-unavailable reason;
- withhold any newly preferred procedure behavior;
- do not claim selector activation.
```

The five existing decision states remain unchanged until an activation ADR proves
the exact user-facing contract.

## Integration Model

### 1. Internal family admission set

Introduce a private, typed intermediate contract, conceptually:

```text
FamilyAdmissionSet
- incident_family
- admitted_card_ids
- assessments
- policy_missing_facts
- policy_rejection_reasons
```

This is not a public API and does not replace `PolicyDecisionResult`.

Its purpose is to retain **all** compatible cards per family long enough for a
shadow selector to inspect them. It must preserve the existing assessment
semantics and must not use rank as an admission input.

### 2. Selection shadow trace

Introduce a separate trace-only contract, conceptually:

```text
FamilyRepresentativeSelectionTrace
- incident_family
- admitted_candidate_ids
- selection_intake_present
- selector_invoked
- selection_state: single_representative | explicit_tie | unavailable
- representative_incident_ids
- unavailable_reason
- candidate_evidence
```

The trace must contain only IDs, enum values, structured alignments, and safe
reasons. It must not contain raw intake narrative, raw provider payloads, raw
retriever scores, or evaluation labels.

### 3. Shadow mode does not change current results

For the first integration slice:

```text
PolicyDecisionResult remains the external result.
retained_precedent_ids remain produced by the current policy contract.
candidate_procedure_ids remain produced by the current policy contract.
selection output is emitted only as a calibration/shadow trace.
```

The purpose is to prove:

```text
same inputs
-> unchanged active decision state
-> unchanged procedure behavior
-> new inspectable family candidate pool
-> selector trace available only when typed intake is supplied
```

### 4. No automatic conversion from EvalCase

`EvalCase` must not be extended by deriving a selection intake from
`input_summary`.

For integration calibration, use an explicit bridge fixture that holds:

```text
policy_case_id
selection_intake
expected_selection_trace
```

The policy case and selection intake remain separate typed assets. This prevents
evaluation labels or free-text parsing from leaking into selection behavior.

## Required Calibration Proof Before Tranche 02

Before authoring a new held-out tranche, the integration shadow harness must prove:

1. **Decision-state invariance**
   - all existing calibration cases retain their expected policy decision state.

2. **Procedure invariance**
   - existing calibration procedure IDs and procedure-withholding outcomes remain
     unchanged in shadow mode.

3. **Provider-degraded bypass**
   - `provider_degraded` produces no selection invocation.

4. **Insufficient-precedent bypass**
   - zero admitted cards produces no selection invocation.

5. **Cross-family conflict preservation**
   - multiple admitted families retain conflict behavior; any family-level
     selection trace cannot choose a preferred cross-family procedure.

6. **Single-card bypass**
   - a family with one admitted card produces a deterministic
     `not_applicable_single_candidate` trace and does not call strict dominance.

7. **Same-family selection invariance**
   - reversing candidate order changes neither the shadow selection outcome nor
     the active policy result.

8. **Tie safety**
   - an explicit within-family tie does not cause a new preferred procedure.

9. **Schema/input failure safety**
   - unsupported family, missing signature, or absent typed selection intake
     creates trace-safe `unavailable` behavior and never falls back to lexical
     order.

10. **No hidden data dependency**
    - the shadow runner does not load held-out case folders, freeze manifests,
      baseline artifacts, comparison reports, or promotion reports.

## Fresh Tranche 02 Preconditions

Tranche 01 remains immutable and valid historical evidence for the previous
keyword-policy and direct-signal work. It is not unseen promotion evidence for
representative selection.

A new Tranche 02 may be authored only after the shadow integration calibration
above is committed and reviewed.

### Minimum Tranche 02 shape

At least 12 frozen cases:

```text
4 single-representative cases
3 explicit within-family ties
2 selection-unavailable / insufficient typed-evidence cases
2 identity or change-context mismatch cases
1 cross-family conflict preservation case
```

Each case needs separate contracts for:

```text
policy decision state
acceptable / unsafe precedence evidence
selection intake
expected selection state
expected representative IDs or explicit tie set
expected procedure visibility behavior
acceptance reason
failure-label intent
```

### Freeze protocol

```text
1. Author cases and labels separate from implementation.
2. Validate schema and case completeness.
3. Review every accept/reject reason.
4. Commit case files.
5. Create a manifest with SHA-256 hashes.
6. Freeze the manifest.
7. Exclude Tranche 02 from implementation bundles.
8. Do not alter selector, schema vocabulary, thresholds, or labels after freeze.
9. Run exactly one predeclared comparison.
```

No activation claim is allowed before that comparison passes its decision-state,
procedure-safety, tie-preservation, and representative-selection contracts.

## Implementation Sequence

### Slice E1 — admission-preserving shadow integration

- Refactor internal policy flow to retain compatible cards by family.
- Add typed family-admission and shadow-trace contracts.
- Do not change public `PolicyDecisionResult`.
- Do not change representative IDs or procedure output.
- Add calibration bridge fixtures with explicit selection intake.
- Add invariance tests and a shadow report.
- Do not load held-out data.

### Slice E2 — fresh Tranche 02 authoring and freeze

- Author a separate selection-integrated held-out tranche.
- Validate and freeze it.
- Do not modify runtime selection behavior.

### Slice E3 — activation proposal

- Predeclare an activation comparison.
- Run once against frozen Tranche 02.
- Block activation on any decision-state regression, unsafe procedure surfacing,
  lexical fallback, selector-unavailable silent fallback, or incorrect
  representative/tie behavior.

## Commercial Translation

This boundary demonstrates a buyer-relevant reliability discipline:

> The system does not silently replace a policy-safe evidence path with a new
> ranking heuristic. It first proves that a representative-selection rule can be
> observed in shadow mode without changing safety decisions, procedure controls,
> or historical evaluation evidence, then requires a fresh frozen test tranche
> before activation.

This is evidence for an AI System Evaluation Audit or RAG Reliability Improvement
Sprint focused on retrieval safety, regression governance, and traceable release
decisions.

## Non-Claims

This ADR does not:

- activate strict-dominance selection;
- alter `AntiAnchoringDecisionPolicy`;
- alter `PolicyDecisionResult`;
- alter keyword retrieval;
- alter procedure eligibility;
- add a sixth final decision state;
- reopen Tranche 01;
- create or freeze Tranche 02;
- validate dense retrieval, reranking, or SIE extraction;
- validate real incident data;
- establish production readiness;
- authorize diagnosis, remediation, or procedure execution.
