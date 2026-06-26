# Local SIE Dense + Score Rerank Calibration Report

## Scope

This report compares deterministic keyword retrieval, local-SIE dense retrieval, and SIE score reranking of the fixed dense top-k on calibration fixtures only.
It does not score held-out cases, assign product decision states, select an authoritative precedent, authorize procedures, or constitute a promotion decision.

## Rerank boundary

- Dense top-k: `5`
- SIE score can reorder only those already-retrieved dense candidates.
- The reranker cannot add an incident card absent from dense top-k.
- Provider raw relevance values are not confidence values; provider rank governs ordering.

## Index and provider binding

- Index ID: `local-sie-dense-index-v1`
- Corpus cards: `12`
- Corpus fingerprint: `a2f625fd8f0e880f416144049ddd8e5841f7bf1f34cbdb7c5e515abc04c389f3`
- Encode profile: `local-sie-encode-v1`
- Encode model: `sentence-transformers/all-MiniLM-L6-v2`
- Score profile: `local-sie-score-v1`
- Score model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Vector dimension: `384`
- Query embedding batch latency (ms): `575.0`

## Calibration comparison

| Metric | Keyword | Dense | Dense + SIE score | Rerank minus dense | Rerank minus keyword |
|---|---:|---:|---:|---:|---:|
| Correct-precedent MRR | 1.0000 | 0.9375 | 0.9375 | 0.0000 | -0.0625 |
| Incident-family Recall@5 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| False-operational-match rate | 0.1818 | 0.0909 | 0.0909 | 0.0000 | -0.0909 |

## Calibration interpretation

- SIE score reranking tied dense retrieval on Exact-precedent ranking for this calibration set.
- SIE score reranking tied dense retrieval on False-operational-match rate for this calibration set.
- Decision: this calibration report does not promote any retrieval path. Anti-anchoring policy and held-out evaluation remain separate gates.

## Rerank-only diagnostics

| Metric | Value |
|---|---:|
| Safety-evaluable cases | 11 |
| Safe top-1 rate | 0.9091 |
| False-operational matches | 1/11 |
| p50 SIE score latency (ms) | 164.5 |
| p95 SIE score latency (ms) | 230.45 |

## Case outcomes

| Eval case | Dense top-k | Reranked top-k | First acceptable rank | Unsafe top-1 | Rerank failure labels |
|---|---|---|---:|---:|---|
| EVAL-001 | INC-012, INC-003, INC-007, INC-004, INC-002 | INC-012, INC-003, INC-007, INC-004, INC-002 | 2 | false | none |
| EVAL-002 | INC-004, INC-003, INC-002, INC-001, INC-007 | INC-004, INC-003, INC-002, INC-001, INC-007 | 1 | false | none |
| EVAL-003 | INC-012, INC-001, INC-004, INC-007, INC-003 | INC-012, INC-001, INC-004, INC-007, INC-003 | N/A | false | rerank_candidate_returned_without_abstention_policy |
| EVAL-004 | INC-004, INC-002, INC-001, INC-011, INC-012 | INC-004, INC-002, INC-001, INC-011, INC-012 | N/A | false | none |
| EVAL-005 | INC-005, INC-006, INC-002, INC-007, INC-008 | INC-005, INC-006, INC-002, INC-007, INC-008 | 1 | false | none |
| EVAL-006 | INC-007, INC-012, INC-003, INC-005, INC-006 | INC-007, INC-012, INC-003, INC-005, INC-006 | 1 | false | none |
| EVAL-007 | INC-003, INC-007, INC-012, INC-004, INC-006 | INC-003, INC-007, INC-012, INC-004, INC-006 | 1 | false | none |
| EVAL-008 | INC-008, INC-006, INC-009, INC-005, INC-007 | INC-008, INC-006, INC-009, INC-005, INC-007 | N/A | true | false_operational_match, rerank_candidate_returned_without_abstention_policy |
| EVAL-009 | INC-009, INC-008, INC-006, INC-007, INC-005 | INC-009, INC-008, INC-006, INC-007, INC-005 | 1 | false | none |
| EVAL-010 | INC-010, INC-009, INC-008, INC-011, INC-007 | INC-010, INC-009, INC-008, INC-011, INC-007 | 1 | false | none |
| EVAL-011 | INC-003, INC-007, INC-012, INC-004, INC-010 | INC-003, INC-007, INC-012, INC-004, INC-010 | 1 | false | none |
| EVAL-012 | INC-002, INC-004, INC-006, INC-011, INC-010 | INC-002, INC-004, INC-006, INC-011, INC-010 | N/A | false | rerank_candidate_returned_without_abstention_policy |

## Known limits

- Calibration-only report; held-out cases are not loaded or scored.
- SIE score can reorder only the dense top-k candidate set; it cannot introduce a new incident card.
- Dense-plus-rerank does not assign decision states, select an authoritative precedent, or authorize a procedure.
- Raw relevance values are provider-native ranking evidence, not calibrated probabilities or confidence values.
- A candidate returned for an insufficient-precedent case remains a retrieval limitation until a separate abstention policy is applied.
- Observed provider score latency is synthetic calibration evidence, not a warm-operation or production latency claim.
- This report is not a promotion decision; anti-anchoring policy and held-out evaluation remain separate gates.
