# ADR-0012: Schema-Derived Representative-Selection Contract

## Status

**Proposed design decision. No runtime selector, active-policy change, or held-out comparison is authorized by this document.**

## Context

The current `AntiAnchoringDecisionPolicy` has a valid safety role: it determines whether a historical incident is compatible enough to remain candidate evidence. It must remain independent from lexical ranking and must continue to control the five typed decision states.

The current within-family issue is narrower:

```text
ranked candidates
-> policy-compatible cards in one incident family
-> which card, if any, may be presented as the representative reference?
```

PR #13 introduced a calibration-only connection-pool preview. It correctly remained separate from the active policy and preserved explicit ties. PR #14 then blocked its activation and any new Tranche 01 comparison because the preview used a weak sidecar cue layer:

- free-text cues were not tied to versioned incident-card fields;
- cue counts could multiply correlated aliases;
- normalized substring matching was too permissive;
- profile coverage was not proven for every eligible card;
- Tranche 01 representative expectations had already been observed during diagnosis.

The current corpus schema offers useful candidate-side facts:

```text
service
component
change_context
started_after_change
symptoms
observability_signals
required_verification_facts
```

But the first four are partly free text, and `EvalCase` currently provides only a free-text summary plus structured verification-fact statuses. It does **not** carry a typed, decision-independent service, component, change-context, or operational-signal representation for representative selection.

Therefore, a selector that reads free-text summaries directly would recreate the prohibited sidecar-cue problem under a different name.

## Decision

Build a representative-selection contract only after the data contracts are hardened around **typed, schema-derived selection evidence**.

The contract must be:

```text
candidate card schema
+ typed selection intake
+ existing compatibility policy
-> family-level evidence vectors
-> strict dominance or explicit tie
```

The selector may select a single representative only when one policy-compatible card has **strictly stronger structured evidence** than every other policy-compatible card in the same family.

When structured evidence does not distinguish candidates safely, the outcome is an explicit tie. It must never fall back to lexical rank, lexical score, incident identifier, procedure identifier, or arbitrary insertion order.

## Contract Boundary

### The existing policy remains the admission gate

Representative selection does not decide whether a family is compatible.

The pipeline remains:

```text
retrieval
-> current deterministic anti-anchoring compatibility policy
-> policy-compatible candidates in one family
-> representative-selection contract
-> selected representative OR explicit tie
```

A card rejected by the existing policy cannot be revived by representative selection.

The selector must remain a separate calibration-only module until a later activation ADR is accepted.

### Required new typed contracts

#### 1. Controlled candidate identity fields

Introduce controlled vocabulary for the values that can legitimately distinguish a candidate:

```text
RelayService
RelayComponent
OperationalSignalFamily
```

`HistoricalIncidentCard` must migrate from free-text selection fields to validated typed values, or contain a validated `selection_signature` that is mechanically consistent with its canonical fields.

A candidate signature must contain only:

```text
service
component
change_context
operational_signal_families
```

It may include source-field references and a review rationale, but it must not contain evaluator-created keywords, broad natural-language aliases, incident labels, or expected outcomes.

Every selection-signature entry must reference an existing card field and pass validation that the source reference actually exists.

#### 2. Typed selection intake

Introduce a separate, typed `RepresentativeSelectionIntake` for calibration and future held-out cases:

```text
service: RelayService | None
component: RelayComponent | None
change_context: ChangeContext | None
operational_signal_families: tuple[OperationalSignalFamily, ...]
contradicted_signal_families: tuple[OperationalSignalFamily, ...]
```

This is input evidence, not a label. It must never contain:

```text
acceptable_precedent_ids
unsafe_precedent_ids
expected_decision_state
expected_candidate_procedure_ids
incident_id
procedure_id
retriever rank
retriever score
```

`EvalCase.observed_facts` remains the current policy input. The new selection intake is a distinct, typed representation for deciding whether one already-compatible card is a stronger representative.

#### 3. Signal-family mapping

A signal family is the smallest independent operational concept that may contribute to representative selection.

The initial connection-pool vocabulary should remain deliberately small:

```text
connection_pool_pressure
active_connection_pressure
queue_backlog
consumer_failure
component_error_pressure
rollout_or_version_change
migration_lock_contention
authentication_failure
readiness_failure
retry_amplification
```

A card may expose each signal family at most once, even when multiple source phrases describe it. For example, pool-utilization and acquisition-latency text may both support `connection_pool_pressure`, but they cannot become two score increments.

A typed mapping from canonical card fields to `OperationalSignalFamily` must be visible, versioned, validated, and reviewed. It cannot be a separate untracked cue file.

## Selection Rule

### Evidence vector

For every policy-compatible card in one family, construct:

```text
identity_alignment:
  exact_component_match
  service_only_match
  unknown
  explicit_mismatch

change_context_alignment:
  exact_match
  unknown
  explicit_mismatch

signal_alignment:
  matching_signal_families
  contradicted_signal_families
```

Each evidence family contributes at most once.

No raw aggregate score is permitted.

### Dominance, not weighted ranking

Candidate A strictly dominates candidate B only when all of the following hold:

1. A is no worse than B on identity alignment.
2. A is no worse than B on change-context alignment.
3. A has no additional contradicted signal family that B avoids.
4. A contains every matching operational-signal family that B contains.
5. A is strictly stronger on at least one of those dimensions.

The selector may return a single representative only when one candidate strictly dominates **every** other policy-compatible candidate in the family.

Otherwise:

```text
representative_selection_state = explicit_tie
```

An explicit tie is valid, safe output. It is not a failure to be hidden with rank order.

### Explicit mismatch handling

An explicit mismatch does not independently reject a candidate from the evidence packet. Existing compatibility policy retains that authority.

However, a card with an explicit mismatch cannot be the sole selected representative when another policy-compatible card has equal or stronger evidence without that mismatch.

### No evidence means no single winner

When the selection intake has no typed information that distinguishes policy-compatible cards:

```text
representative_selection_state = explicit_tie
```

Unknown must never be converted into weak support. Missing input must never create a confident single-card result.

## Prohibited Inputs and Behaviors

The selector must not use:

- lexical retrieval rank;
- lexical retrieval score;
- dense-retrieval score;
- reranker score;
- incident or procedure identifier;
- candidate list order;
- `required_verification_facts` counts or cardinality;
- candidate procedure availability;
- severity;
- recovery state;
- region;
- broad free-text substring matches;
- manually authored sidecar cues without canonical source-field references;
- calibration labels;
- held-out labels or manifests;
- case-specific branches.

`required_verification_facts` remain prerequisites for safe procedure eligibility and missing-fact presentation. They are not positive representative-selection evidence.

## Schema Validation Gates

A schema-derived selection signature is valid only when:

1. Every authored connection-pool card has exactly one signature.
2. No signature exists for a non-connection-pool card in this initial slice.
3. Signature `service`, `component`, and `change_context` equal the parent card fields.
4. Every signal family cites one or more canonical card source fields.
5. Every cited source field exists on the parent card.
6. Duplicate signal families are rejected.
7. No free-text alias, cue, expected outcome, or incident identifier is used as a selection signal.
8. Selection intake contains no evaluation-label fields.
9. An unprofiled but policy-compatible card produces validation failure in calibration setup, never a silent omission.
10. Serialization order is deterministic only after the outcome is already a tie.

## Required Calibration Cases

Do not reuse existing calibration cases as the only proof. Add a dedicated selection-calibration set with at least these cases:

| Case type | Contract to prove |
|---|---|
| Exact component match | A component match strictly dominates a service-only or mismatch card. |
| Service match only | Service alignment can help, but cannot override stronger direct contradictions. |
| Exact change-context match | A context match distinguishes otherwise comparable cards. |
| Unknown context | Unknown context does not create support. |
| Correlated source phrases | Two phrases mapped to one signal family contribute once. |
| Distinct signal families | Different independent signal families can create dominance. |
| Explicit mismatch | A mismatched card cannot become a sole winner over a non-mismatched compatible card. |
| No distinguishing evidence | The output is an explicit tie. |
| Candidate-order reversal | Reversing rank and score leaves the result unchanged. |
| Incomplete corpus coverage | Missing signature coverage fails validation rather than changing selection silently. |
| Existing-policy invariance | The active policy and ADR-0009 comparison result remain unchanged. |

All new cases are calibration only. They must be stored separately from Tranche 01 and may not mutate its files.

## Fresh Held-Out Tranche 02 Rules

A new held-out tranche is required before any representative-selection activation claim.

### Freeze sequence

```text
1. Commit this contract and schema-validation rules.
2. Author calibration cases and validate the selector only on calibration.
3. Create Tranche 02 cases and labels separately.
4. Freeze a manifest with hashes and acceptance reasons.
5. Do not include Tranche 02 files in selector implementation bundles.
6. Do not alter selector logic, signal vocabulary, thresholds, or annotations after freeze.
7. Run one predeclared comparison against Tranche 02 only after calibration passes.
```

### Tranche 02 composition

For this narrow boundary, target at least 12 cases:

```text
4 single-representative positive cases
3 explicit-tie cases
2 identity/context mismatch cases
2 missing-evidence cases
1 cross-family conflict preservation case
```

Every case must define expected decision state separately from expected representative behavior. A selector must not be allowed to alter decision-state precedence, procedure withholding, provider-degraded handling, or cross-family conflict behavior.

Tranche 01 remains immutable historical evidence and an observed diagnostic set for this boundary. It is not a blind promotion gate for the new selector.

## Implementation Sequence

### Slice A — contract and schema hardening

- Add this ADR.
- Add controlled selection enums and typed signature/intake contracts.
- Add schema validation.
- Migrate the current connection-pool cards only.
- Do not change active policy.
- Do not add a selector.
- Do not load held-out cases.

### Slice B — calibration fixtures

- Add dedicated selection-calibration cases.
- Add contract tests for coverage, source references, cardinality, and prohibited fields.
- Do not change active policy.
- Do not generate a promotion claim.

### Slice C — isolated selector

- Implement strict-dominance selection on typed evidence vectors.
- Add rank/score reversal tests.
- Add explicit-tie tests.
- Add active-policy invariance tests.
- Generate a calibration-only report.

### Slice D — fresh evaluation tranche

- Freeze Tranche 02.
- Preserve it outside normal implementation design bundles.
- Run one predeclared comparison only after review confirms calibration safety.

## Acceptance Criteria for Any Future Activation Proposal

A future activation ADR may be considered only when:

```text
- every candidate signature validates;
- every selection intake validates;
- no sidecar cue layer exists;
- no lexical rank, lexical score, identifier, or order reaches selection logic;
- each operational signal family contributes at most once;
- explicit ties are preserved;
- the active policy remains behaviorally unchanged until activation;
- calibration proves no unsafe representative selection;
- a fresh held-out Tranche 02 is frozen before comparison;
- the comparison preserves decision-state, procedure-withholding, and provider-degraded contracts.
```

## Commercial Translation

This work creates a buyer-visible reliability proof:

> The harness does not treat the first plausible historical incident as a recommendation. It defines what evidence is allowed to distinguish similar precedents, preserves ambiguity when the evidence does not discriminate, and requires a fresh frozen evaluation tranche before a selection rule can be promoted.

That supports an AI System Evaluation Audit or RAG Reliability Improvement Sprint focused on unsafe retrieval, evidence selection, and regression governance.

## Non-Claims

This ADR does not:

- activate a representative selector;
- change `AntiAnchoringDecisionPolicy`;
- change the keyword retriever;
- reopen Tranche 01;
- validate semantic retrieval, reranking, or SIE extraction;
- validate real incident data;
- establish production readiness;
- authorize incident diagnosis, remediation, or procedure execution.
