# Batch 01 Source Review — Queue Backlog Caused by Consumer Failure

## Purpose

Batch 01 is the first corpus-authoring slice. It deliberately creates
**controlled variants**, not source-grounded records. The source links below
inform mechanisms and failure shapes, but the generated RelayOps cards are not
allowed to claim `source_grounded` status until a human completes the promotion
checklist.

This is intentional: the schema requires `human_verified: true` for a
source-grounded record, and the repository must not manufacture that assertion.

## Batch shape

| Asset | Count | Current state |
|---|---:|---|
| Controlled variant incident cards | 4 | validated by Pydantic tests |
| Candidate investigation procedures | 1 | validated by Pydantic tests |
| Calibration cases | 4 | validated by Pydantic tests |
| Held-out cases | 0 | intentionally untouched |

All four cards use the one primary family:
`queue_backlog_consumer_failure`.

## Proposed source linkage

| RelayOps card | Proposed source | Retained general mechanism | Removed or changed |
|---|---|---|---|
| INC-001 | SRC-008 | worker memory failure can repeatedly remove consumer capacity and grow a task backlog | source organization, dates, counts, cache implementation, direct remediation |
| INC-002 | SRC-009 | slow database writes can delay processing and create a recoverable event backlog | source database internals, exact metrics, cloud provider, recovery steps |
| INC-003 | SRC-006 | a deployment-adjacent connection threshold can cause worker startup failure and retry amplification | source service names, exact timeout, source incident timeline, rollback details |
| INC-004 | SRC-007 | an unrelated rollout plus resource pressure can reduce healthy consumer capacity and amplify cache/database load | source organization, exact resource values, exact infrastructure names, direct remediation |

## Promotion checklist

Before changing any Batch 01 record from `controlled_variant` to
`source_grounded`, the reviewer must confirm all of the following:

1. The associated source URL resolves and is listed in `source-manifest.md`.
2. The source mechanism matches the row above at a high level.
3. The RelayOps card contains no copied narrative, numbers, service names,
   people, source-system identifiers, or direct operational commands.
4. The transformation remains plausible within the fixed RelayOps topology.
5. The card's safety labels and procedure applicability are independently
   reviewed; source similarity does not prove they are safe.
6. The provenance object is added with `human_verified: true` only after the
   reviewer actually completed steps 1–5.

## Why this is useful before promotion

The four cards give the baseline retrieval work a coherent, typed, source-linked
starter family. Keeping them controlled prevents a misleading source-grounded
claim while preserving the path to verified provenance later.

## Non-claims

Batch 01 does not prove a source-grounded final corpus, real incident recall,
retrieval quality, safe procedure applicability, held-out performance, or
production incident-response readiness.
