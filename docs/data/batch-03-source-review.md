# Batch 03 Source Review — Connection-Pool Variants and Conflict Case

## Purpose

Batch 03 introduces four fictional RelayOps records in the
`connection_pool_exhaustion` family, one bounded Candidate Investigation
Procedure, and four calibration cases. It also creates the first explicit
`evidence_found_with_conflict` calibration case.

All incident cards remain `controlled_variant`. No card in this batch claims to
be a real PostHog or PostgreSQL event. No public narrative, implementation
identifier, production metric, infrastructure name, or remediation instruction
has been copied into the RelayOps assets.

## Proposed source linkage

| RelayOps asset | Proposed source records | Retained general mechanism | Removed or prohibited |
|---|---|---|---|
| `INC-009` | `SRC-006`, `SRC-012` | connection acquisition delay under database stress; active connections near an operational boundary | source service names, exact timeout values, direct configuration changes |
| `INC-010` | `SRC-006` | reduced connection tolerance plus retry amplification can turn database stress into service unavailability | source timeline, error text, deployment identifiers, remediation sequence |
| `INC-011` | `SRC-007` | resource pressure can delay pool initialization, reduce healthy capacity, and create readiness failures | source pod counts, CPU percentages, infrastructure layout, direct operational fixes |
| `INC-012` | `SRC-007`, `SRC-012` | retry pressure and pool acquisition delay can coexist with delivery backlog | source cache mechanics, customer impact figures, connection-limit values |
| `RB-003` | `SRC-012` | compare utilization, acquisition latency, active connections, and lock-wait evidence before treating a precedent as applicable | any instruction to increase connection limits, alter pool settings, or restart services |
| `EVAL-011` | `SRC-006`, `SRC-007` | pool-init pressure and deployment-linked capacity loss can be simultaneously plausible but operationally divergent | any claim that either precedent identifies the current root cause |

## New verification-fact vocabulary

Batch 03 adds three controlled verification facts:

- `database_connection_pool_utilization`
- `database_connection_acquire_latency`
- `database_connection_limit`

They are evidence fields only. They do not authorize a responder or system to
change pool settings, `max_connections`, timeout values, or service capacity.

## Conflict case rationale

`EVAL-011` is accepted because it creates a real policy dilemma rather than a
keyword trick:

- a worker rollout and readiness failures make the queue-consumer record
  plausible;
- pool acquisition latency and high active connections make the
  connection-pool record plausible;
- migration lock waits are absent, so the migration-lock family is unsafe;
- neither candidate procedure may be selected because the decisive facts are
  incomplete and the investigation paths diverge.

The correct expected state is `evidence_found_with_conflict`, with no preferred
candidate procedure.

## Review required before source-grounded promotion

Before any Batch 03 record can become `source_grounded`:

1. Verify each proposed source URL and its applicability to the retained
   mechanism.
2. Confirm that no source wording, exact operational identifier, or remediation
   instruction remains in the RelayOps artifact.
3. Record the exact individual source date and transformation note in a
   `ProvenanceRecord`.
4. Obtain explicit human verification and set `human_verified: true`.
