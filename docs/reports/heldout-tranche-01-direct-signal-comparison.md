# Held-Out Tranche 01 — Direct-Signal Intervention Comparison

## Scope

This report compares one predeclared calibration-validated policy intervention against the immutable keyword-plus-policy held-out baseline.
The frozen inputs, labels, manifest, retriever, top-k setting, and gate thresholds are unchanged.

## Evidence linkage

- Baseline report: `evidence_vault/reports/heldout-tranche-01-keyword-policy.json`
- Baseline SHA-256: `4518cc80b4e6864bbf1d19fc6e76047787fffa09d9bc58c3f080d23f5aa65a96`
- Baseline repository revision: `edcf8c8e7f2a79559858e07607fd8c5104a30d31`
- Baseline gate: **BLOCKED**
- Frozen manifest SHA-256: `5fbb4372582db66a96e9718394776a3dcbde8f6c7447cefc0c1e5beaf2f63535`
- Comparison repository revision: `1eaea7493b427ff873ddf71e5f00166f7ea74405`
- Comparison gate: **BLOCKED**

## Metric comparison

| Metric | Baseline | Comparison |
|---|---:|---:|
| Decision-state accuracy | 0.9167 | 1.0 |
| Case-contract pass rate | 0.8333 | 0.9167 |
| Acceptable-precedent coverage | 0.8571 | 0.8571 |
| Procedure-contract accuracy | 0.9167 | 1.0 |
| False-operational matches | 0 | 0 |
| Unexpected retained precedents | 2 | 1 |
| Blocked cases | EVAL-102, EVAL-110 | EVAL-110 |

## Case-level change

| Eval case | Change | Baseline state | Comparison state | Baseline retained | Comparison retained |
|---|---|---|---|---|---|
| EVAL-102 | improved | evidence_found_with_conflict | evidence_found | INC-005, INC-011 | INC-005 |

## Conclusion

**IMPROVED BUT BLOCKED**

- Improved cases: EVAL-102
- Regressed cases: none
- Changed but not promoted: none
- Remaining blocked cases: EVAL-110

## Non-claims

- This comparison evaluates one predeclared deterministic policy intervention against the same frozen 12-case tranche.
- The frozen case inputs, labels, hashes, baseline evidence, lexical retriever, top-k setting, and promotion thresholds are not changed by this comparison.
- A comparison improvement does not prove semantic retrieval quality, live SIE extraction readiness, customer-data readiness, or production incident-response safety.
- A remaining blocked gate is not a license to tune on held-out labels; the next intervention must be justified through a separate calibration-only design step.
