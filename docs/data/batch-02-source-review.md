# Batch 02 Source Review — Migration-Related Database Lock Contention

## Purpose

Batch 02 adds four **controlled variants** in the fixed
`database_migration_lock_contention` family, one bounded Candidate Investigation
Procedure, and four calibration cases. It deliberately adds the project’s first
explicit false-operational-match cases.

The controlled-variant posture remains intentional. The repository has not yet
completed person-by-person review sufficient to set `human_verified: true` and
therefore must not label these cards `source_grounded`.

## Batch shape

| Asset | Count | Current state |
|---|---:|---|
| Controlled variant incident cards | 4 | Pydantic-validated |
| Candidate investigation procedures | 1 | Pydantic-validated |
| New calibration cases | 4 | Pydantic-validated |
| Held-out cases | 0 | intentionally untouched |

## Proposed source linkage

| RelayOps asset | Proposed source | Retained general mechanism | Removed or changed |
|---|---|---|---|
| INC-005 | SRC-010, SRC-011 | incompatible database lock waits can delay writes and reduce downstream throughput | real schema, query, database identifiers, timelines, remediation |
| INC-006 | SRC-010, SRC-011 | a long transaction can hold a conflicting lock while dependent writes wait | source terminology beyond general locking, all implementation details |
| INC-007 | SRC-009, SRC-010 | database-side processing delay can create a queue backlog while consumers remain healthy | source organization, database internals, metrics, recovery steps |
| INC-008 | SRC-010, SRC-011 | lock-related write delay can increase active connections and application latency | all source-specific connection behavior and operational changes |
| RB-002 | SRC-010, SRC-011 | lock waits and concurrent activity are verification facts, not proof or remediation instructions | SQL commands, session termination, lock-setting changes |

## Anti-anchoring case introduced

`EVAL-005` is the first hard false-operational-match case.

It resembles a Batch 01 event because it has a queue backlog after a change. It
must still prefer the migration-contention family when migration lock waits,
database write latency, and healthy consumer status are confirmed. The queue
consumer procedures from Batch 01 are unsafe for that case.

`EVAL-007` tests the reverse error: confirmed worker readiness failures after a
deployment must not be displaced by database-migration wording or queue overlap.

## Promotion checklist

Before changing any Batch 02 record from `controlled_variant` to
`source_grounded`, the reviewer must confirm:

1. The exact source URL resolves and is listed in `source-manifest.md`.
2. The retained mechanism is accurate at a general level.
3. The RelayOps card contains no copied narrative, source organization name,
   production identifier, exact metric, source timeline, or remediation detail.
4. The card remains plausible inside the RelayOps topology.
5. Procedure applicability and unsafe labels were reviewed independently from
   source similarity.
6. A provenance object is added with `human_verified: true` only after steps
   1–5 are completed.

## Non-claims

Batch 02 does not prove source-grounded status, retrieval quality, a tuned
similarity threshold, safe procedure eligibility in runtime, held-out
performance, or production incident-response readiness.
