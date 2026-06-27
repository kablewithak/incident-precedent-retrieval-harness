# Typed Triage Calibration Report

## Scope

This report runs calibration fixtures through the typed triage packet boundary only.
It does not load held-out cases, promote a retriever, select an authoritative representative, authorize a procedure, or execute a remediation.

## Control boundary

- Policy candidate source: `deterministic_keyword_top_5`
- Semantic advisory source: `local_sie_dense_top_5`
- Semantic evidence is advisory-only and cannot alter the active anti-anchoring policy result.
- Procedure execution authorized: `false` for every valid packet.

## Results

| Metric | Value |
|---|---:|
| Calibration cases | 12 |
| Matching decision states | 12/12 |
| Decision-state match rate | 1.0000 |
| Semantic advisory available | 11/12 |
| Provider-degraded packets | 1 |
| Procedure execution authorized | 0 |

## Decision

- Result: packet control gate passed.
- This does not promote a retrieval path; semantic evidence remains advisory while retrieval and policy evaluation continue separately.

## Case outcomes

| Eval case | Expected state | Observed state | Match | Semantic advisory | Policy precedents | Semantic candidates | Failure labels |
|---|---|---|---:|---|---|---|---|
| EVAL-001 | evidence_found | evidence_found | true | available | INC-003 | INC-012, INC-003, INC-007, INC-004, INC-002 | none |
| EVAL-002 | missing_critical_facts | missing_critical_facts | true | available | INC-003 | INC-004, INC-003, INC-002, INC-001, INC-007 | none |
| EVAL-003 | insufficient_precedent | insufficient_precedent | true | available | N/A | INC-012, INC-001, INC-004, INC-007, INC-003 | none |
| EVAL-004 | provider_degraded | provider_degraded | true | provider_degraded | N/A | N/A | none |
| EVAL-005 | evidence_found | evidence_found | true | available | INC-005 | INC-005, INC-006, INC-002, INC-007, INC-008 | none |
| EVAL-006 | missing_critical_facts | missing_critical_facts | true | available | INC-007 | INC-007, INC-012, INC-003, INC-005, INC-006 | none |
| EVAL-007 | evidence_found | evidence_found | true | available | INC-003 | INC-003, INC-007, INC-012, INC-004, INC-006 | none |
| EVAL-008 | insufficient_precedent | insufficient_precedent | true | available | N/A | INC-008, INC-006, INC-009, INC-005, INC-007 | none |
| EVAL-009 | evidence_found | evidence_found | true | available | INC-009 | INC-009, INC-008, INC-006, INC-007, INC-005 | none |
| EVAL-010 | missing_critical_facts | missing_critical_facts | true | available | INC-010 | INC-010, INC-009, INC-008, INC-011, INC-007 | none |
| EVAL-011 | evidence_found_with_conflict | evidence_found_with_conflict | true | available | INC-011, INC-003 | INC-003, INC-007, INC-012, INC-004, INC-010 | none |
| EVAL-012 | insufficient_precedent | insufficient_precedent | true | available | N/A | INC-002, INC-004, INC-006, INC-011, INC-010 | none |

## Known limits

- Calibration-only report; held-out cases are not loaded or scored.
- The anti-anchoring policy consumes deterministic keyword candidates only in this slice.
- Local-SIE dense candidates are advisory evidence and cannot alter policy decision state, retained precedents, missing facts, or procedure eligibility.
- No packet authorizes procedure execution, automated remediation, or root-cause determination.
- This report evaluates packet control behavior, not retrieval-quality superiority or production readiness.
