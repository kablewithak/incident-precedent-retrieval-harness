# ADR-0010: Connection-Pool Representative-Selection Preview

## Status

Proposed for calibration-only validation. Not activated in the live decision policy.

## Context

The frozen held-out comparison remains blocked because the current anti-anchoring
policy keeps the first compatible card encountered for a family. That couples the
representative evidence card to lexical retriever order.

The rollback exposed a second issue: `required_verification_facts` are
verification prerequisites, not statements that a fact should be present. A
selector must not rank cards by how many prerequisite facts happen to be
confirmed, contradicted, or unknown. Doing so can prefer a generic card with a
shorter prerequisite list and regress missing-fact or false-operational-match
behavior.

The immediate blocker concerns `connection_pool_exhaustion`. The smallest safe
intervention is therefore a calibration-only preview for that family. It must
reuse existing compatibility policy and must not change the current policy,
retriever, held-out artifacts, or historical comparison result.

## Decision

Add a separate preview path:

```text
keyword candidate pool
-> existing AntiAnchoringDecisionPolicy evaluated per candidate
-> compatible connection-pool cards only
-> explicit, data-declared context and intake-cue comparison
-> one preview representative or an explicit tie
```

The preview uses only:

1. Existing policy compatibility for each card in isolation.
2. Card-declared change context.
3. Card-declared distinguishing intake cues stored in a reviewed local profile
   artifact.

The preview must not use:

- lexical rank;
- lexical score;
- incident identifier to choose a winner;
- procedure identifier;
- calibration labels as a selection input;
- held-out inputs, labels, artifacts, manifests, or reports;
- counts of `required_verification_facts` by status.

When declared signals cannot distinguish eligible cards, the preview returns a
tie. Identifier order may stabilize serialized display only after a tie has
already been declared.

## Why this is a preview

The active `AntiAnchoringDecisionPolicy` and ADR-0009 comparison must remain
reproducible. This preview creates calibration evidence for a potential
representative-selection contract without changing production-shaped behavior.
A later, separately approved activation slice may use the preview evidence to
design a constrained policy integration and predeclare a new held-out comparison.

## Calibration gate

Run:

```powershell
python -m pytest .\tests\unit
python .\scripts\run_connection_pool_representative_preview.py --repository-root . --top-k 5
```

The preview passes its calibration gate only when:

```text
unsafe_selection_count = 0
active_policy_changed = false
heldout_loaded = false
rank/score reversal test passes
true tie remains explicit
```

This does not prove that the active policy has improved, authorize a held-out
comparison, prove semantic retrieval, or establish production readiness.
