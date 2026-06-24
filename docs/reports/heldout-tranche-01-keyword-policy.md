# Held-Out Tranche 01 — Keyword + Policy Evaluation

## Scope

This report evaluates the frozen `heldout_tranche_01` against the recorded deterministic keyword retriever and anti-anchoring policy.
The held-out cases were manifest-verified before scoring. This is a promotion gate result, not a tuning input.

## Freeze verification

- Scope: `heldout_tranche_01`
- Manifest: `data/evals/heldout/HELDOUT_FREEZE_MANIFEST.json`
- Manifest SHA-256: `5fbb4372582db66a96e9718394776a3dcbde8f6c7447cefc0c1e5beaf2f63535`
- Verified cases: `12`

## Evaluated configuration

- Retriever: `keyword_bm25_style_v1`
- Policy: `deterministic_anti_anchoring_policy_v1`
- Top K: `5`
- Corpus incident cards: `12`
- Candidate procedures: `3`
- Repository revision: `edcf8c8e7f2a79559858e07607fd8c5104a30d31`

## Promotion gate

**Status: BLOCKED**

| Gate criterion | Observed | Required |
|---|---:|---:|
| Decision-state accuracy | 0.9167 | 1.0 |
| Case-contract pass rate | 0.8333 | 1.0 |
| Acceptable-precedent coverage | 0.8571 | 1.0 |
| Procedure-contract accuracy | 0.9167 | 1.0 |
| Missing-fact contract accuracy | 1.0 | 1.0 |
| Abstention/degraded contract accuracy | 1.0 | 1.0 |
| Unsafe precedents retained | 0 | 0 |
| Unexpected procedures surfaced | 0 | 0 |
| Unexpected retained precedents | 2 | 0 |

### Gate rationale

- Decision-state accuracy is below the required 1.0 on the frozen tranche.
- One or more held-out cases violate the full evidence/procedure contract.
- Not every required acceptable precedent was retained by the configuration.
- Candidate procedure output differs from the held-out contract.
- Unexpected retained precedents require trace review before promotion.

## Case outcomes

| Eval case | Expected state | Actual state | Ranked IDs | Retained IDs | Procedures | Contract result | Failure labels |
|---|---|---|---|---|---|---|---|
| EVAL-101 | evidence_found | evidence_found | INC-003, INC-007, INC-012, INC-011, INC-010 | INC-003 | RB-001 | pass | none |
| EVAL-102 | evidence_found | evidence_found_with_conflict | INC-005, INC-002, INC-011, INC-009, INC-012 | INC-005, INC-011 | none | block | decision_state_mismatch, unexpected_retained_precedent, candidate_procedure_contract_mismatch |
| EVAL-103 | evidence_found | evidence_found | INC-009, INC-008, INC-010, INC-012, INC-005 | INC-009 | RB-003 | pass | none |
| EVAL-104 | insufficient_precedent | insufficient_precedent | INC-009, INC-006, INC-005, INC-012, INC-003 | none | none | pass | none |
| EVAL-105 | insufficient_precedent | insufficient_precedent | INC-012, INC-007, INC-005, INC-003, INC-009 | none | none | pass | none |
| EVAL-106 | insufficient_precedent | insufficient_precedent | INC-009, INC-004, INC-006, INC-005, INC-012 | none | none | pass | none |
| EVAL-107 | insufficient_precedent | insufficient_precedent | INC-005, INC-011, INC-001, INC-002, INC-008 | none | none | pass | none |
| EVAL-108 | insufficient_precedent | insufficient_precedent | INC-010, INC-001, INC-006, INC-009, INC-005 | none | none | pass | none |
| EVAL-109 | insufficient_precedent | insufficient_precedent | INC-005, INC-006, INC-003, INC-009, INC-008 | none | none | pass | none |
| EVAL-110 | evidence_found_with_conflict | evidence_found_with_conflict | INC-012, INC-011, INC-009, INC-003, INC-010 | INC-012, INC-003 | none | block | required_acceptable_precedent_missing, unexpected_retained_precedent |
| EVAL-111 | evidence_found_with_conflict | evidence_found_with_conflict | INC-005, INC-009, INC-010, INC-008, INC-007 | INC-005, INC-009 | none | pass | none |
| EVAL-112 | provider_degraded | provider_degraded | none | none | none | pass | none |

## Non-claims

- This is a 12-case held-out tranche, not the final planned 36-case evaluation set.
- A passed or blocked result applies only to the recorded keyword-plus-policy configuration.
- This report does not prove semantic retrieval quality, live SIE extraction readiness, customer-data readiness, or production incident-response safety.
- A blocked result is diagnostic evidence and must not be converted into a tuning loop by modifying frozen cases or their labels.
