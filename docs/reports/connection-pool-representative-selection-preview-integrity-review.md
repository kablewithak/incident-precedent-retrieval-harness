# Connection-Pool Representative-Selection Preview — Integrity Review

## Review boundary

This review inspects the PR #13 calibration-only preview and its declared
profile artifact. It does not execute or modify the active decision policy,
held-out data, the promotion gate, or historical comparison artifacts.

## Verdict

```text
CALIBRATION PREVIEW: retained as exploratory evidence
ACTIVE POLICY ACTIVATION: blocked
NEW TRANCHE 01 COMPARISON: blocked
FRESH FROZEN TRANCHE: required before selection-promotion evidence
```

## What the preview gets right

- It invokes the current policy per candidate and leaves
  `AntiAnchoringDecisionPolicy` unchanged.
- It limits its scope to the authored `connection_pool_exhaustion` family.
- It states that lexical rank and score are excluded from the selection key.
- It emits an explicit tie when declared signals do not separate compatible
  candidates.
- Its generated calibration report records `heldout_loaded=false`.

These are worthwhile harness controls. They prevent the original
first-compatible-card behavior from being silently replaced by a new hidden
retrieval-order rule.

## Why the preview does not pass an activation gate

### 1. Calibration coverage is too small

The preview report contains three selection outcomes. That is useful smoke
evidence, not enough coverage for an evidence-selection contract. It does not
demonstrate robust behavior across:

- ambiguous within-family candidates;
- conflicting lexical and structured signals;
- missing or partial context;
- absent profile signals;
- cue collisions;
- new incident-card additions;
- unprofiled but compatible cards.

### 2. The profile artifact is a sidecar and lacks grounding metadata

The profile records contain a declared change context and free-text
`distinguishing_intake_cues`. They do not state:

- which incident-card field supports each cue;
- whether a cue is a normalized alias, a quoted symptom, a service alias, or
  an evaluator-created shortcut;
- who reviewed the cue;
- when or why it was added;
- whether every eligible connection-pool card is represented.

This allows the sidecar to become an untracked selection-label layer.

### 3. Raw cue counts are not independent evidence

The preview selects on `(context_alignment, number_of_matched_cues)`. Multiple
cues can encode one underlying concept. For example, `auth` and
`authentication` can both match the same intake wording. This produces a score
increase without independent operational evidence.

A successor selector must score distinct evidence families, not count
overlapping aliases.

### 4. Text matching is too permissive

The cue matcher uses normalized substring containment. A short cue may match
inside an unrelated term, and a phrase can match without a meaningful semantic
boundary. This is unsuitable as a promotion-facing evidence contract.

### 5. Tranche 01 no longer qualifies as unseen selection evidence

The EVAL-110 representative-selection expectation was already visible during
failure investigation and preview design. A selector created after that
visibility cannot use a new Tranche 01 result as a blind transfer claim.

The immutable Tranche 01 artifacts remain valid for their original baseline,
direct-signal intervention, and historical diagnosis. They are simply not a
fresh selection-promotion gate.

## Required successor design

The successor must be calibration-only and begin from schema-derived facts:

```text
canonical incident card fields
-> normalized evidence families
-> compatibility-filtered candidate group
-> representative selector or explicit tie
-> calibration report with traceable reasons
```

Minimum evidence families:

1. service/component alignment;
2. explicit change-context alignment;
3. symptom or observability-signal alignment;
4. contradiction or non-applicability evidence.

The selector must treat each family as at most one contribution. It must preserve
a tie whenever the evidence families do not distinguish candidates safely.

## Required successor tests

- profile/card coverage is exact for every eligible family member;
- every annotation cites the supporting card field;
- synonym aliases cannot multiply one score family;
- phrase boundaries prevent partial-token matches;
- retriever rank and score reversal leave the result unchanged;
- unprofiled compatible cards cause a safe tie or explicit validation failure;
- missing evidence cannot produce a false single-card winner;
- the active policy and ADR-0009 comparison behavior remain unchanged.

## Next safe gate

Create and freeze a fresh evaluation tranche only after the successor selector
contract is committed. That tranche must be separated from calibration and must
not be used to tune implementation, annotations, thresholds, or cardinality.

No Tranche 01 representative-selection comparison is permitted in the meantime.

## Non-claims

This review does not claim that PR #13 improves the active policy, that
representative selection is solved, that a future selector will generalize, or
that the project is ready for semantic retrieval, customer data, or production
incident use.
