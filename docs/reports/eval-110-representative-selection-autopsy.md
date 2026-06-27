# EVAL-110 — Representative-Selection Autopsy

## Scope

This report reads recorded frozen baseline and typed-triage promotion evidence. It does not rerun retrieval, policy, or semantic inference and does not modify held-out inputs or active policy behavior.

## Evidence chain

- Held-out manifest: `data/evals/heldout/HELDOUT_FREEZE_MANIFEST.json`
- Held-out manifest SHA-256: `5fbb4372582db66a96e9718394776a3dcbde8f6c7447cefc0c1e5beaf2f63535`
- Verified frozen cases: `12`
- Baseline report: `evidence_vault/reports/heldout-tranche-01-keyword-policy.json`
- Baseline SHA-256: `4518cc80b4e6864bbf1d19fc6e76047787fffa09d9bc58c3f080d23f5aa65a96`
- Typed-triage promotion report: `evidence_vault/reports/frozen-typed-triage-promotion-gate.json`
- Typed-triage promotion SHA-256: `22af8427e859f13b616051a09873c08295149923903474eed85f3e6f8b9f87c9`

## Recorded divergence

- Expected state: `evidence_found_with_conflict`
- Baseline state: `evidence_found_with_conflict`
- Ranked candidate IDs: `INC-012, INC-011, INC-009, INC-003, INC-010`
- Retained precedent IDs: `INC-012, INC-003`
- Expected acceptable IDs: `INC-003, INC-009`
- Omitted required IDs: `INC-009`
- Unexpected retained IDs: `INC-012`
- Failure labels: `required_acceptable_precedent_missing, unexpected_retained_precedent`

## Typed-triage authority parity

- Policy matches baseline: `true`
- Typed state matches frozen expectation: `true`
- Typed decision state: `evidence_found_with_conflict`
- Semantic advisory available: `true`
- Procedure execution authorized: `false`

## Candidate trace

| Incident | Family | Rank | Retained | Expected acceptable | Confirmed facts | Contradicted facts | Unknown facts | Signature signals |
|---|---|---:|---:|---:|---:|---:|---:|---|
| INC-012 | connection_pool_exhaustion | 1 | true | false | 4 | 1 | 0 | connection_pool_pressure, queue_backlog, retry_amplification |
| INC-011 | connection_pool_exhaustion | 2 | false | false | 4 | 1 | 0 | connection_pool_pressure, active_connection_pressure, readiness_failure, component_error_pressure |
| INC-009 | connection_pool_exhaustion | 3 | false | true | 4 | 1 | 0 | connection_pool_pressure, active_connection_pressure |
| INC-003 | queue_backlog_consumer_failure | 4 | true | true | 4 | 0 | 0 | none |
| INC-010 | connection_pool_exhaustion | 5 | false | false | 4 | 1 | 0 | connection_pool_pressure, authentication_failure, readiness_failure, component_error_pressure |

## Verdict

**UNDOCUMENTED_CONFLICT_RULE**

### Reasons

- The active policy retained higher-ranked INC-012 while the frozen contract required INC-009; both are connection_pool_exhaustion cards.
- The recorded decision state remains correct, so the divergence is within-family representative selection rather than conflict-state detection.
- The current active path suppresses later compatible candidates in the same family, making the retained representative depend on fixed retrieval order without an active reviewed selection rule.

### Remediation boundary

Do not patch ranks, incident IDs, retrieval order, held-out labels, or active policy on this branch. A separate calibration-only design slice must define and evaluate a typed within-family representative-selection contract before any activation proposal.

## Non-claims

- This autopsy reads recorded frozen evidence; it does not rerun retrieval, policy, or semantic inference.
- The held-out fixture, labels, hashes, candidate ordering, policy rules, procedure eligibility, and semantic-advisory authority are unchanged.
- The verdict is a diagnostic classification, not proof that any remediation will pass the frozen tranche.
- No procedure is authorized, and no production, customer-data, or incident-response safety claim follows from this report.
