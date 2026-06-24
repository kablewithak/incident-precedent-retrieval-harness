# ADR-0007: Autopsy a blocked held-out baseline before intervention

- **Status:** Accepted
- **Date:** 2026-06-24
- **Decision owners:** Incident Precedent Retrieval Harness maintainers

## Context

The first frozen held-out evaluation of `keyword_bm25_style_v1` plus
`deterministic_anti_anchoring_policy_v1` is blocked. The gate is blocked by
`EVAL-102` and `EVAL-110` while reporting zero unsafe retained precedents and
zero unexpected candidate procedures.

A blocked held-out result is not permission to edit the frozen fixtures, relax the
gate, silently alter ranking, or apply a broad policy patch. The project needs a
traceable explanation of the failure mechanism before a calibration-only
intervention is designed.

## Decision

Introduce a write-once failure-autopsy report that:

1. reads the already committed held-out baseline rather than rescoring it;
2. verifies the held-out freeze manifest before producing the trace;
3. maps blocked outcomes to typed intake facts and typed incident-card
   verification requirements;
4. records diagnosis categories and intervention boundaries without applying a
   patch;
5. refuses to overwrite the autopsy evidence pair.

The next engineering change may be designed only after the autopsy identifies a
narrow, testable mechanism. It must first be exercised against calibration cases.
The frozen tranche must not be altered or re-run as a tuning loop.

## Consequences

### Positive

- Preserves the blocked baseline as the before-state for later comparison.
- Separates diagnostic evidence from an unmeasured implementation change.
- Makes explicit whether failure comes from family admission, within-family
  representative choice, ranking, missing facts, or procedure gating.
- Reduces the risk of satisfying held-out labels through hidden special cases.

### Costs and limits

- The autopsy does not improve the gate by itself.
- The trace uses the current compact corpus and cannot prove behavior on an
  expanded or customer-derived corpus.
- It does not validate dense retrieval, semantic reranking, or live SIE
  extraction.

## Rejected alternatives

### Immediately patch the policy from the two failed held-out cases

Rejected because it risks building hidden case-specific behavior and removes a
clean before-state.

### Rerun the held-out evaluator repeatedly during investigation

Rejected because the frozen gate is a promotion boundary, not a feedback loop.

### Treat zero unsafe procedures as sufficient for promotion

Rejected because accurate evidence selection and procedure eligibility are both
required contract dimensions.
