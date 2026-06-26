# Local SIE Dense Retrieval Calibration Report

## Scope

This report compares local-SIE embedding retrieval with the deterministic keyword baseline on calibration fixtures only.
It does not score held-out cases, assign product decision states, authorize procedures, or constitute a promotion decision.

## Dense index binding

- Index ID: `local-sie-dense-index-v1`
- Index format: `local-dense-index-v1`
- Corpus cards: `12`
- Corpus fingerprint: `a2f625fd8f0e880f416144049ddd8e5841f7bf1f34cbdb7c5e515abc04c389f3`
- Representation version: `incident-retrieval-representation-v1`
- Encode profile: `local-sie-encode-v1`
- Encode model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector dimension: `384`
- Query embedding batch latency (ms): `985.0`

## Calibration comparison

| Metric | Keyword baseline | Dense retrieval | Dense minus keyword |
|---|---:|---:|---:|
| Correct-precedent MRR | 1.0 | 0.9375 | -0.0625 |
| Incident-family Recall@5 | 1.0 | 1.0 | 0.0 |
| False-operational-match rate | 0.1818 | 0.0909 | -0.0909 |

## Calibration interpretation

- Dense retrieval was lower on exact-precedent ranking by 0.0625 on this calibration set; no exact-ranking improvement is claimed.
- Dense retrieval tied the keyword baseline on incident-family Recall@5 for this calibration set.
- Dense retrieval reduced the calibration false-operational-match rate by 0.0909; this safety proxy still requires later policy and held-out evaluation.
- Decision: this calibration report does not promote either retriever. SIE score reranking, anti-anchoring controls, and held-out evaluation remain separate gates.

## Dense-only diagnostics

| Metric | Value |
|---|---:|
| Safety-evaluable cases | 11 |
| Safe top-1 rate | 0.9091 |
| False-operational matches | 1/11 |
| p50 local cosine latency (ms) | 1.9706 |
| p95 local cosine latency (ms) | 2.3764 |

## Case outcomes

| Eval case | Expected state | Top candidates | First acceptable rank | Unsafe top-1 | Dense failure labels |
|---|---|---|---:|---:|---|
| EVAL-001 | evidence_found | INC-012, INC-003, INC-007, INC-004, INC-002 | 2 | false | none |
| EVAL-002 | missing_critical_facts | INC-004, INC-003, INC-002, INC-001, INC-007 | 1 | false | none |
| EVAL-003 | insufficient_precedent | INC-012, INC-001, INC-004, INC-007, INC-003 | — | false | dense_candidate_returned_without_abstention_policy |
| EVAL-004 | provider_degraded | INC-004, INC-002, INC-001, INC-011, INC-012 | — | false | none |
| EVAL-005 | evidence_found | INC-005, INC-006, INC-002, INC-007, INC-008 | 1 | false | none |
| EVAL-006 | missing_critical_facts | INC-007, INC-012, INC-003, INC-005, INC-006 | 1 | false | none |
| EVAL-007 | evidence_found | INC-003, INC-007, INC-012, INC-004, INC-006 | 1 | false | none |
| EVAL-008 | insufficient_precedent | INC-008, INC-006, INC-009, INC-005, INC-007 | — | true | false_operational_match, dense_candidate_returned_without_abstention_policy |
| EVAL-009 | evidence_found | INC-009, INC-008, INC-006, INC-007, INC-005 | 1 | false | none |
| EVAL-010 | missing_critical_facts | INC-010, INC-009, INC-008, INC-011, INC-007 | 1 | false | none |
| EVAL-011 | evidence_found_with_conflict | INC-003, INC-007, INC-012, INC-004, INC-010 | 1 | false | none |
| EVAL-012 | insufficient_precedent | INC-002, INC-004, INC-006, INC-011, INC-010 | — | false | dense_candidate_returned_without_abstention_policy |

## Known limits

- Calibration-only report; held-out cases are not loaded or scored.
- Dense retrieval does not assign a final decision state or authorize a procedure.
- Cosine retrieval has not yet been reranked with SIE score.
- A candidate returned for an insufficient-precedent case is a retrieval limitation, not acceptable evidence.
- The provider latency is an observed batch encoding time for synthetic calibration inputs, not a warm-operation or production latency claim.
- This report is not a promotion decision; safety policy and provider-degraded behavior are evaluated in later slices.
