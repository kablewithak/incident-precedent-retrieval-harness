# Held-Out Evaluation Constitution — Tranche 01

## Purpose

This document freezes the first held-out evaluation tranche for Related Incident Evidence.
It creates an untouched diagnostic boundary before any dense retrieval, reranking, threshold adjustment, policy adjustment, or procedure-eligibility change.

This is **not** the final planned 36-case held-out set. It is a 12-case tranche aligned to the three incident families currently authored in the RelayOps archive:

- `queue_backlog_consumer_failure`
- `database_migration_lock_contention`
- `connection_pool_exhaustion`

## Frozen assets

```text
12 cases: data/evals/heldout/EVAL-101.json through EVAL-112.json
1 integrity manifest: data/evals/heldout/HELDOUT_FREEZE_MANIFEST.json
```

The manifest records SHA-256 hashes for every held-out case. Repository tests fail if any case content changes without a corresponding, deliberate manifest revision.

## Case groups

| Group | Count | Purpose |
|---|---:|---|
| Standard positive | 3 | Verify one compatible precedent/procedure path per authored family. |
| False-operational-match | 3 | Verify that rate-limit, provider, and cache patterns do not inherit an unrelated procedure. |
| No-precedent | 3 | Verify abstention for unrepresented feature-flag, authentication, and worker-crash-loop patterns. |
| Conflicting precedent | 2 | Verify no preferred procedure when two materially different families remain plausible. |
| Provider degraded | 1 | Verify explicit degraded output rather than invented semantic confidence. |

## Isolation rules

Held-out cases must never be used to tune:

- BM25 weights, stopwords, tokenization, or ranking tie-breaks;
- dense embeddings, reranker profiles, candidate count, or thresholds;
- deterministic compatibility rules;
- missing-fact or conflict rules;
- prompts, extraction labels, canonicalization, or procedure eligibility logic.

A case may be changed only for a documented data defect. The change must:

1. identify the defect and affected expected behavior;
2. create a new manifest revision with new hashes;
3. retain the old revision in change history;
4. rerun every baseline and candidate pipeline report;
5. state whether prior comparisons remain comparable.

## Evaluation posture

This tranche contains structured fact observations because the product is expected to operate on structured intake evidence. Those observations are inputs to the deterministic policy, not hidden evaluator-only ground truth.

The expected decision state, acceptable precedent IDs, unsafe precedent IDs, and expected procedure IDs are evaluation labels. They must never be passed into a retrieval, inference, or policy prompt.

## Current non-claims

This freeze does not prove:

- semantic retrieval quality;
- held-out promotion-gate eligibility;
- all eight planned incident families;
- source-grounded final-record verification;
- live SIE extraction readiness;
- customer-data or production incident-response readiness.
