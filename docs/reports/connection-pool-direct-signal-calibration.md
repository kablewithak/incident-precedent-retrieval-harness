# Anti-Anchoring Policy Calibration Report

## Scope

This report evaluates deterministic compatibility, abstention, missing-fact, conflict, and procedure gates on calibration fixtures only.
It is not a semantic-retrieval or production-safety claim.

## Metrics

| Metric | Value |
|---|---:|
| Decision-state accuracy | 1.0 |
| False-operational matches surfaced | 0 |
| Unsafe procedures surfaced | 0 |
| No-precedent abstention accuracy | 1.0 |
| Conflict-state accuracy | 1.0 |
| Missing-fact exact-match rate | 1.0 |

## Case outcomes

| Eval case | Expected | Actual | Retained precedents | Candidate procedures | Missing facts | Unsafe precedent | Unsafe procedure |
|---|---|---|---|---|---|---:|---:|
| EVAL-001 | evidence_found | evidence_found | INC-003 | RB-001 | none | false | false |
| EVAL-002 | missing_critical_facts | missing_critical_facts | INC-003 | none | consumer_error_rate, error_rate_by_component, worker_deployment_version | false | false |
| EVAL-003 | insufficient_precedent | insufficient_precedent | none | none | none | false | false |
| EVAL-004 | provider_degraded | provider_degraded | none | none | none | false | false |
| EVAL-005 | evidence_found | evidence_found | INC-005 | RB-002 | none | false | false |
| EVAL-006 | missing_critical_facts | missing_critical_facts | INC-007 | none | active_database_connections, error_rate_by_component, migration_lock_waits | false | false |
| EVAL-007 | evidence_found | evidence_found | INC-003 | RB-001 | none | false | false |
| EVAL-008 | insufficient_precedent | insufficient_precedent | none | none | none | false | false |
| EVAL-009 | evidence_found | evidence_found | INC-009 | RB-003 | none | false | false |
| EVAL-010 | missing_critical_facts | missing_critical_facts | INC-010 | none | database_connection_acquire_latency, database_connection_pool_utilization, migration_lock_waits | false | false |
| EVAL-011 | evidence_found_with_conflict | evidence_found_with_conflict | INC-011, INC-003 | none | consumer_error_rate, database_connection_pool_utilization | false | false |
| EVAL-012 | insufficient_precedent | insufficient_precedent | none | none | none | false | false |

## Known limits

- Calibration-only report; held-out cases are not loaded or scored.
- Policy uses explicit structured evaluation facts; it does not perform free-text extraction.
- This prototype supports only the three authored incident families.
- Candidate procedures remain non-executable investigation artifacts.
- No semantic-provider, dense-retrieval, reranking, or warm-latency claim is made.
