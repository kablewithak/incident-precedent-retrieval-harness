# Frozen Typed-Triage Promotion Gate

## Scope

This write-once report compares the frozen deterministic keyword-plus-policy baseline with the current typed triage packet boundary.
The semantic layer remains advisory-only. It must not change policy authority, retained precedent IDs, missing facts, or candidate procedure eligibility.

## Freeze verification

- Scope: `heldout_tranche_01`
- Manifest: `data/evals/heldout/HELDOUT_FREEZE_MANIFEST.json`
- Manifest SHA-256: `5fbb4372582db66a96e9718394776a3dcbde8f6c7447cefc0c1e5beaf2f63535`
- Verified frozen cases: `12`

## Baseline comparison

- Baseline report kind: `heldout_keyword_policy_evaluation`
- Baseline promotion status: `blocked`
- Baseline decision-state accuracy: `1.0`
- Baseline case-contract pass rate: `0.9167`
- Baseline blocked cases: `EVAL-110`

## Candidate boundary

- Policy candidate source: `deterministic_keyword_top_5`
- Semantic advisory source: `local_sie_dense_top_5`
- Procedure execution authorization: `false` by contract.
- Provisional p95 end-to-end latency budget: `1500 ms`

## Gate decision

**Decision: BLOCK**

### Rationale

- The underlying frozen keyword-plus-policy baseline is blocked; the typed advisory wrapper cannot promote a blocked policy path.
- The underlying policy violates one or more frozen evidence, procedure, or missing-fact contracts.

## Metrics

| Metric | Value |
|---|---:|
| Frozen held-out cases | 12 |
| Typed-triage expected-state accuracy | 1.0 |
| Policy baseline parity | 1.0 |
| Policy case-contract pass rate | 0.9167 |
| Semantic advisory available | 11/12 |
| Unexpected semantic degraded | 0 |
| Provider-degraded cases | 1 |
| Provider-degraded safe resolution rate | 1.0 |
| Procedure execution authorized | 0 |
| P50 end-to-end latency | 68 ms |
| P95 end-to-end latency | 85 ms |
| Blocked cases | EVAL-110 |

## Case outcomes

| Eval case | Expected | Baseline | Typed triage | Policy parity | Semantic advisory | Procedures authorized | Pipeline latency | Failure labels |
|---|---|---|---|---:|---|---:|---:|---|
| EVAL-101 | evidence_found | evidence_found | evidence_found | true | available | false | 68 ms | none |
| EVAL-102 | evidence_found | evidence_found | evidence_found | true | available | false | 51 ms | none |
| EVAL-103 | evidence_found | evidence_found | evidence_found | true | available | false | 52 ms | none |
| EVAL-104 | insufficient_precedent | insufficient_precedent | insufficient_precedent | true | available | false | 77 ms | none |
| EVAL-105 | insufficient_precedent | insufficient_precedent | insufficient_precedent | true | available | false | 60 ms | none |
| EVAL-106 | insufficient_precedent | insufficient_precedent | insufficient_precedent | true | available | false | 53 ms | none |
| EVAL-107 | insufficient_precedent | insufficient_precedent | insufficient_precedent | true | available | false | 36 ms | none |
| EVAL-108 | insufficient_precedent | insufficient_precedent | insufficient_precedent | true | available | false | 80 ms | none |
| EVAL-109 | insufficient_precedent | insufficient_precedent | insufficient_precedent | true | available | false | 85 ms | none |
| EVAL-110 | evidence_found_with_conflict | evidence_found_with_conflict | evidence_found_with_conflict | true | available | false | 81 ms | required_acceptable_precedent_missing, unexpected_retained_precedent |
| EVAL-111 | evidence_found_with_conflict | evidence_found_with_conflict | evidence_found_with_conflict | true | available | false | 81 ms | none |
| EVAL-112 | provider_degraded | provider_degraded | provider_degraded | true | provider_degraded | false | 2 ms | none |

## Non-claims

- This is a frozen 12-case tranche, not the final planned 36-case held-out evaluation set.
- The semantic advisory remains non-authoritative; it cannot alter the active keyword-policy decision, retained precedents, missing facts, or procedure eligibility.
- A promote_advisory_only decision does not promote a semantic retriever, diagnose root cause, authorize a procedure, or establish production readiness.
- A blocked or insufficient-evidence result is evidence, not a reason to tune held-out inputs, labels, thresholds, ranking behavior, or policy rules.
- This local synthetic-data run does not establish customer-data validation, production provider reliability, load behavior, or production incident-response safety.
