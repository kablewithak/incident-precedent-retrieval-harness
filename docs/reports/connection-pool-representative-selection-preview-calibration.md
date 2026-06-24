# Connection-Pool Representative-Selection Preview — Calibration

## Boundary

This is a calibration-only preview. It does not change `AntiAnchoringDecisionPolicy`, the keyword retriever, held-out artifacts, or promotion-gate behavior.

## Summary

- Preview cases: 3
- Safe selections: 3
- Unsafe selections: 0
- Active policy changed: false
- Held-out loaded: false

## Outcomes

| Case | Selected cards | Acceptable selection | Unsafe selection |
|---|---|---:|---:|
| EVAL-009 | INC-009 | true | false |
| EVAL-010 | INC-010 | true | false |
| EVAL-011 | INC-011 | true | false |

## Known limits

- Calibration-only preview; no held-out case is loaded or scored.
- The active AntiAnchoringDecisionPolicy remains unchanged.
- This preview applies only to the authored connection_pool_exhaustion family.
- Selection uses declared profile cues after current policy compatibility; it does not use lexical rank, lexical score, incident ID, procedure ID, or evaluation labels.
- A passed preview does not authorize a held-out comparison or a production claim.
