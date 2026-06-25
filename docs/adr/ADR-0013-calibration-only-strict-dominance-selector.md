# ADR-0013: Calibration-Only Strict-Dominance Representative Selector

## Status

Accepted for calibration-only implementation.

This ADR does **not** activate representative selection in
`AntiAnchoringDecisionPolicy`, authorize a held-out comparison, or establish
promotion eligibility.

## Context

ADR-0012 defined the schema-derived representative-selection contract after the
previous sidecar-cue preview was blocked. PR #16 added validated selection
signatures to the four authored `connection_pool_exhaustion` cards. PR #17 then
added a dedicated, typed selection-calibration fixture set.

The active anti-anchoring policy remains responsible for:

```text
retrieval candidate admission
compatibility checks
five final decision states
procedure withholding
cross-family conflict
missing-fact presentation
provider-degraded behavior
```

The new selector has one narrower responsibility:

```text
already policy-admitted cards in one family
-> can one card be a stronger representative?
-> one representative OR explicit tie
```

## Decision

Implement `StrictDominanceRepresentativeSelector` as a standalone,
calibration-only module.

It accepts only:

```text
RepresentativeSelectionIntake
candidate incident IDs
validated HistoricalIncidentCard selection signatures
```

It does not import or inspect:

```text
AntiAnchoringDecisionPolicy
keyword retrieval
rank
score
procedure metadata
evaluation labels
held-out cases
held-out manifests
promotion-gate artifacts
```

## Evidence Dimensions

Each candidate is evaluated with independent, typed dimensions:

```text
service alignment:
  match / unknown / mismatch

component alignment:
  match / unknown / mismatch

change-context alignment:
  match / unknown / mismatch

matching signal families:
  set intersection of intake and candidate signature

contradicted signal families:
  set intersection of intake contradictions and candidate signature
```

Service and component remain separate dimensions. This avoids an unstated
priority rule where a service match silently outweighs a component match, or
vice versa.

Each operational-signal family is counted at most once because the signature
schema deduplicates families before selector execution.

## Strict-Dominance Rule

Candidate A strictly dominates candidate B only when:

1. A is no worse on service, component, and change-context alignment.
2. A contains every intake-confirmed operational-signal family matched by B.
3. A has no contradicted signal family that B avoids.
4. A is strictly stronger on at least one of those dimensions.

The selector uses no aggregate score, weight, rank, or identifier tie-breaker.

### Outcome

```text
one non-dominated candidate
-> single_representative

two or more non-dominated candidates
-> explicit_tie
```

Candidate identifiers are sorted only after the non-dominated outcome is known
so report serialization is stable. Identifier order never participates in
selection.

## Failure Behavior

The selector raises a typed input-boundary error when a caller supplies:

- fewer than two candidates;
- duplicate candidate IDs;
- an unknown candidate;
- a non-connection-pool candidate in the current scoped implementation;
- a candidate without a schema-derived selection signature.

This prevents silent omission from a family-level selection pool.

## Calibration Gate

The selector must pass all ten dedicated `selection_calibration` fixtures,
including:

- three exact representative cases;
- three explicit-tie cases;
- an exact candidate-order reversal pair;
- contradiction avoidance;
- no-evidence behavior;
- schema coverage validation.

The calibration runner must write a Markdown and JSON report showing:

```text
selection_calibration_case_count
passed_cases
failed_cases
strict_dominance_contract_pass_rate
active_policy_changed=false
heldout_loaded=false
retrieval_loaded=false
selector_activation_claim=false
```

## Consequences

### Positive

- The representative choice is inspectable and traceable.
- The implementation does not recreate lexical-rank or free-text-cue coupling.
- The selector preserves ties rather than hiding uncertainty.
- Existing policy behavior and the immutable Tranche 01 evidence remain unchanged.

### Cost

- A strict partial order intentionally yields ties in ambiguous cases.
- This slice proves only calibration contract conformance.
- No activation or safety claim is available until a separate integration design,
  a fresh frozen Tranche 02, and a predeclared comparison are complete.

## Non-claims

This ADR does not claim:

- active runtime use;
- retrieval improvement;
- held-out success;
- production incident-response readiness;
- customer-data validation;
- safe remediation guidance.
