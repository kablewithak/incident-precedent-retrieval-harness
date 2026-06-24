# Held-Out Tranche 01 — Failure Autopsy

## Scope

This trace reads the committed blocked held-out baseline. It does not rerun retrieval or policy, modify frozen inputs, or claim an intervention result.

## Baseline linkage

- Baseline report: `evidence_vault/reports/heldout-tranche-01-keyword-policy.json`
- Baseline SHA-256: `4518cc80b4e6864bbf1d19fc6e76047787fffa09d9bc58c3f080d23f5aa65a96`
- Baseline repository revision: `edcf8c8e7f2a79559858e07607fd8c5104a30d31`
- Held-out manifest: `data/evals/heldout/HELDOUT_FREEZE_MANIFEST.json`
- Held-out manifest SHA-256: `5fbb4372582db66a96e9718394776a3dcbde8f6c7447cefc0c1e5beaf2f63535`
- Verified frozen cases: `12`
- Baseline gate: **BLOCKED**

## Findings

### EVAL-102: false_conflict_from_contextual_signal

- Expected state: `evidence_found`
- Actual state: `evidence_found_with_conflict`
- Failure labels: `decision_state_mismatch, unexpected_retained_precedent, candidate_procedure_contract_mismatch`
- Ranked IDs: `INC-005, INC-002, INC-011, INC-009, INC-012`
- Retained IDs: `INC-005, INC-011`
- Expected acceptable IDs: `INC-005`
- Unexpected retained IDs: `INC-011`

#### Candidate fact trace

| Incident | Family | Rank | Retained | Confirmed required facts | Contradicted required facts | Unknown required facts |
|---|---|---:|---:|---:|---:|---:|
| INC-005 | database_migration_lock_contention | 1 | true | 4 | 0 | 0 |
| INC-002 | queue_backlog_consumer_failure | 2 | false | 2 | 1 | 0 |
| INC-011 | connection_pool_exhaustion | 3 | true | 2 | 3 | 0 |
| INC-009 | connection_pool_exhaustion | 4 | false | 3 | 2 | 0 |
| INC-012 | connection_pool_exhaustion | 5 | false | 3 | 2 | 0 |

#### Diagnosis

A connection-pool precedent was retained even though both direct pool signals were contradicted. The remaining confirmed active-connection fact is contextual evidence, not sufficient direct evidence of pool exhaustion. That over-retention manufactured a conflict and withheld the expected migration-lock procedure.

#### Intervention boundary

Calibration-only intervention: require at least one direct connection-pool signal (pool utilization or acquisition latency) before admitting the connection-pool family. Do not change frozen held-out cases or rerun this tranche until calibration regressions are reviewed.

### EVAL-110: within_family_representative_ambiguity

- Expected state: `evidence_found_with_conflict`
- Actual state: `evidence_found_with_conflict`
- Failure labels: `required_acceptable_precedent_missing, unexpected_retained_precedent`
- Ranked IDs: `INC-012, INC-011, INC-009, INC-003, INC-010`
- Retained IDs: `INC-012, INC-003`
- Expected acceptable IDs: `INC-003, INC-009`
- Unexpected retained IDs: `INC-012`

#### Candidate fact trace

| Incident | Family | Rank | Retained | Confirmed required facts | Contradicted required facts | Unknown required facts |
|---|---|---:|---:|---:|---:|---:|
| INC-012 | connection_pool_exhaustion | 1 | true | 4 | 1 | 0 |
| INC-011 | connection_pool_exhaustion | 2 | false | 4 | 1 | 0 |
| INC-009 | connection_pool_exhaustion | 3 | false | 4 | 1 | 0 |
| INC-003 | queue_backlog_consumer_failure | 4 | true | 4 | 0 | 0 |
| INC-010 | connection_pool_exhaustion | 5 | false | 4 | 1 | 0 |

#### Diagnosis

The decision state retained the intended incident-family direction, but lexical rank selected an unexpected representative within that same family. The current policy keeps the first compatible card per family, so its final evidence card is coupled to retriever order rather than a reviewed within-family selection contract. Relevant fact-coverage traces: INC-012: confirmed=4, contradicted=1, unknown=0; INC-011: confirmed=4, contradicted=1, unknown=0; INC-009: confirmed=4, contradicted=1, unknown=0; INC-010: confirmed=4, contradicted=1, unknown=0.

#### Intervention boundary

Design intervention, not a tie-break patch: define a reviewed within-family evidence-selection contract or add a discriminative structured fact. Do not use incident ID order, raw lexical rank, or held-out labels as a hidden selector.

## Non-claims

- This report reads recorded held-out evidence; it does not rerun retrieval or policy scoring.
- Frozen held-out cases, labels, hashes, ranking configuration, and decision policy are not modified by this autopsy.
- The intervention boundaries are hypotheses for calibration-only work, not proof that a fix will pass held-out evaluation.
- This report does not establish semantic retrieval quality, live SIE extraction readiness, customer-data readiness, or production incident-response safety.
