# Labeling Guide — Related Incident Evidence

## Labeling goal

Labels exist to test whether the retrieval harness surfaces **operationally
compatible historical evidence** without anchoring a responder on a plausible but
unsafe lookalike.

They are not root-cause labels and they are not execution instructions.

## Incident records

Every historical incident card must have:

- one primary `incident_family`;
- a RelayOps service and component;
- change context and whether onset followed a change;
- symptoms and observability signals;
- a safe fictional narrative;
- required verification facts;
- linked, safe, and unsafe candidate procedure IDs;
- origin and provenance controls.

## Candidate investigation procedures

A procedure must be written as a bounded investigation artifact:

- use `inspect`, `compare`, `confirm`, or `review`;
- do not use `restart`, `rollback`, `execute`, `fix`, or `resolve`;
- name explicit non-applicability conditions;
- name verification prerequisites;
- list out-of-scope actions.

A procedure is not eligible merely because an embedding score is high.

## Eval cases

Each case is accepted only when it is diagnostic:

| Case type | Required contract |
|---|---|
| Standard positive | Compatible precedent(s), safe procedure where all prerequisites exist |
| False operational match | Unsafe lookalike IDs explicitly named |
| No precedent | No acceptable precedent or candidate procedure |
| Conflict | At least two acceptable precedents with divergent paths; no preferred procedure |
| Provider failure | Explicit degraded expected state and failure label |

## Accept/reject reasons for new hard cases

Store an `acceptance_reason` that explains why the case exposes a real weakness.
Reject cases that are trivial, ambiguous, duplicate, ungrounded, or only reward
keyword overlap.

## Held-out freeze rule

Calibration cases may guide thresholds and policy design. Held-out cases may not.
After freeze, do not alter labels, IDs, or expected states except to repair a
documented data defect.
