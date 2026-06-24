# Keyword Baseline Calibration Report

## Scope

This report measures deterministic lexical ranking on the calibration split only.
It does not assign product decision states, surface procedures, or establish safe operational applicability.

## Configuration

- Corpus incident cards: `12`
- Calibration cases: `12`
- Top K: `5`
- Tokenization: lowercase alphanumeric tokens; underscore/hyphen split; fixed stopword list
- Ranking: BM25-style lexical ranking (k1=1.2, b=0.75)

## Metrics

| Metric | Value |
|---|---:|
| Correct-precedent MRR | 1.0 |
| Incident-family Recall@5 | 1.0 |
| Safety-evaluable cases | 11 |
| Safe top-1 rate | 0.8182 |
| False-operational matches | 2/11 |
| False-operational-match rate | 0.1818 |
| p50 lexical query latency (ms) | 0.1936 |
| p95 lexical query latency (ms) | 0.2591 |

## Case outcomes

| Eval case | Expected state | Top candidates | First acceptable rank | Unsafe top-1 | Baseline failure labels |
|---|---|---|---:|---:|---|
| EVAL-001 | evidence_found | INC-003, INC-007, INC-012, INC-004, INC-011 | 1 | false | none |
| EVAL-002 | missing_critical_facts | INC-003, INC-004, INC-010, INC-011, INC-002 | 1 | false | none |
| EVAL-003 | insufficient_precedent | INC-001, INC-003, INC-009, INC-005, INC-007 | — | true | false_operational_match, lexical_candidate_returned_without_abstention_policy |
| EVAL-004 | provider_degraded | INC-003, INC-002, INC-004, INC-001, INC-007 | — | false | none |
| EVAL-005 | evidence_found | INC-005, INC-002, INC-006, INC-007, INC-003 | 1 | false | none |
| EVAL-006 | missing_critical_facts | INC-007, INC-010, INC-005, INC-012, INC-003 | 1 | false | none |
| EVAL-007 | evidence_found | INC-003, INC-012, INC-007, INC-010, INC-004 | 1 | false | none |
| EVAL-008 | insufficient_precedent | INC-009, INC-008, INC-006, INC-005, INC-012 | — | false | lexical_candidate_returned_without_abstention_policy |
| EVAL-009 | evidence_found | INC-009, INC-008, INC-010, INC-011, INC-012 | 1 | false | none |
| EVAL-010 | missing_critical_facts | INC-010, INC-009, INC-011, INC-012, INC-008 | 1 | false | none |
| EVAL-011 | evidence_found_with_conflict | INC-011, INC-009, INC-003, INC-012, INC-010 | 1 | false | none |
| EVAL-012 | insufficient_precedent | INC-009, INC-006, INC-010, INC-011, INC-012 | — | true | false_operational_match, lexical_candidate_returned_without_abstention_policy |

## Known limits

- Calibration-only report; held-out cases are not loaded or scored.
- Lexical ranking does not assign a final decision state.
- Lexical ranking does not surface or authorize a candidate investigation procedure.
- A candidate returned for an insufficient-precedent case is recorded as a baseline limitation, not treated as acceptable evidence.
- Latency reflects local in-memory lexical ranking only; it is not a live-provider latency claim.
