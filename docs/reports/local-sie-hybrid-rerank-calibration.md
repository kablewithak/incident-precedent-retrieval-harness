# Local SIE Hybrid + Score Rerank Calibration Report

## Scope

This report compares keyword retrieval, local-SIE dense retrieval, dense-plus-SIE-score reranking, and a bounded hybrid candidate union with SIE score reranking on calibration fixtures only.
It does not score held-out cases, assign product decision states, select an authoritative precedent, authorize procedures, or constitute a promotion decision.

## Hybrid boundary

- Keyword candidates per case: `5`
- Dense candidates per case: `5`
- Maximum score candidates per case: `10`
- Common metric evaluation cut: top `5`
- Seed union order: keyword rank order, then dense-only candidates in dense rank order.
- SIE score cannot add an incident card absent from the hybrid seed union.
- Provider raw relevance values are not confidence values; provider rank governs reranked ordering.

## Calibration comparison

| Metric | Keyword | Dense | Dense + SIE score | Hybrid + SIE score | Hybrid minus keyword | Hybrid minus dense + score |
|---|---:|---:|---:|---:|---:|---:|
| Correct-precedent MRR | 1.0000 | 0.9375 | 0.9375 | 1.0000 | 0.0000 | 0.0625 |
| False-operational-match rate | 0.1818 | 0.0909 | 0.0909 | 0.1818 | 0.0000 | 0.0909 |

## Calibration interpretation

- Hybrid-plus-rerank improved exact-precedent ranking by 0.0625 relative to dense-plus-rerank on this calibration set; this is not a promotion claim.
- Hybrid-plus-rerank increased the false-operational-match rate by 0.0909 relative to dense-plus-rerank on this calibration set; it is not eligible for promotion.
- Decision: this calibration report does not promote any retrieval path. Anti-anchoring policy and held-out evaluation remain separate gates.

## Hybrid-only diagnostics

| Metric | Value |
|---|---:|
| False-operational matches | 2/11 |
| p50 SIE score latency (ms) | 308.5 |
| p95 SIE score latency (ms) | 387.85 |
| p50 seed candidate count | 6.5 |
| p95 seed candidate count | 7.45 |

## Case outcomes

| Eval case | Keyword top-k | Dense top-k | Hybrid seed | Reranked top-k | First acceptable rank | Unsafe top-1 | Failure labels |
|---|---|---|---|---|---:|---:|---|
| EVAL-001 | INC-003, INC-007, INC-012, INC-004, INC-011 | INC-012, INC-003, INC-007, INC-004, INC-002 | INC-003, INC-007, INC-012, INC-004, INC-011, INC-002 | INC-003, INC-007, INC-012, INC-004, INC-011, INC-002 | 1 | false | none |
| EVAL-002 | INC-003, INC-004, INC-010, INC-011, INC-002 | INC-004, INC-003, INC-002, INC-001, INC-007 | INC-003, INC-004, INC-010, INC-011, INC-002, INC-001, INC-007 | INC-003, INC-004, INC-010, INC-011, INC-002, INC-001, INC-007 | 1 | false | none |
| EVAL-003 | INC-001, INC-003, INC-009, INC-005, INC-007 | INC-012, INC-001, INC-004, INC-007, INC-003 | INC-001, INC-003, INC-009, INC-005, INC-007, INC-012, INC-004 | INC-001, INC-003, INC-009, INC-005, INC-007, INC-012, INC-004 | N/A | true | false_operational_match, hybrid_candidate_returned_without_abstention_policy |
| EVAL-004 | INC-003, INC-002, INC-004, INC-001, INC-007 | INC-004, INC-002, INC-001, INC-011, INC-012 | INC-003, INC-002, INC-004, INC-001, INC-007, INC-011, INC-012 | INC-003, INC-002, INC-004, INC-001, INC-007, INC-011, INC-012 | N/A | false | none |
| EVAL-005 | INC-005, INC-002, INC-006, INC-007, INC-003 | INC-005, INC-006, INC-002, INC-007, INC-008 | INC-005, INC-002, INC-006, INC-007, INC-003, INC-008 | INC-005, INC-002, INC-006, INC-007, INC-003, INC-008 | 1 | false | none |
| EVAL-006 | INC-007, INC-010, INC-005, INC-012, INC-003 | INC-007, INC-012, INC-003, INC-005, INC-006 | INC-007, INC-010, INC-005, INC-012, INC-003, INC-006 | INC-007, INC-010, INC-005, INC-012, INC-003, INC-006 | 1 | false | none |
| EVAL-007 | INC-003, INC-012, INC-007, INC-010, INC-004 | INC-003, INC-007, INC-012, INC-004, INC-006 | INC-003, INC-012, INC-007, INC-010, INC-004, INC-006 | INC-003, INC-012, INC-007, INC-010, INC-004, INC-006 | 1 | false | none |
| EVAL-008 | INC-009, INC-008, INC-006, INC-005, INC-012 | INC-008, INC-006, INC-009, INC-005, INC-007 | INC-009, INC-008, INC-006, INC-005, INC-012, INC-007 | INC-009, INC-008, INC-006, INC-005, INC-012, INC-007 | N/A | false | hybrid_candidate_returned_without_abstention_policy |
| EVAL-009 | INC-009, INC-008, INC-010, INC-011, INC-012 | INC-009, INC-008, INC-006, INC-007, INC-005 | INC-009, INC-008, INC-010, INC-011, INC-012, INC-006, INC-007, INC-005 | INC-009, INC-008, INC-010, INC-011, INC-012, INC-006, INC-007, INC-005 | 1 | false | none |
| EVAL-010 | INC-010, INC-009, INC-011, INC-012, INC-008 | INC-010, INC-009, INC-008, INC-011, INC-007 | INC-010, INC-009, INC-011, INC-012, INC-008, INC-007 | INC-010, INC-009, INC-011, INC-012, INC-008, INC-007 | 1 | false | none |
| EVAL-011 | INC-011, INC-009, INC-003, INC-012, INC-010 | INC-003, INC-007, INC-012, INC-004, INC-010 | INC-011, INC-009, INC-003, INC-012, INC-010, INC-007, INC-004 | INC-011, INC-009, INC-003, INC-012, INC-010, INC-007, INC-004 | 1 | false | none |
| EVAL-012 | INC-009, INC-006, INC-010, INC-011, INC-012 | INC-002, INC-004, INC-006, INC-011, INC-010 | INC-009, INC-006, INC-010, INC-011, INC-012, INC-002, INC-004 | INC-009, INC-006, INC-010, INC-011, INC-012, INC-002, INC-004 | N/A | true | false_operational_match, hybrid_candidate_returned_without_abstention_policy |

## Known limits

- Calibration-only report; held-out cases are not loaded or scored.
- The hybrid seed union contains only keyword top-k and dense top-k candidates.
- SIE score can reorder only the bounded hybrid seed union; it cannot introduce a new incident card.
- The lexical-first seed order is deterministic provenance, not a final ranking or policy preference.
- Dense-plus-rerank and hybrid-plus-rerank do not assign decision states, select an authoritative precedent, or authorize a procedure.
- Raw relevance values are provider-native ranking evidence, not calibrated probabilities or confidence values.
- A candidate returned for an insufficient-precedent case remains a retrieval limitation until a separate abstention policy is applied.
- This report is not a promotion decision; anti-anchoring policy and held-out evaluation remain separate gates.
