# Policy Shadow Integration Calibration

- Shadow integration fixtures: 8
- Existing policy calibration cases checked for same-input public invariance: 12
- Public-result invariance failures: 0
- Bridge-fixture failures: 0
- Shadow trace order invariant: `true`
- Same-input policy invariant: `true`
- Legacy rank-sensitivity observation: `true`
- Changed public fields under EVAL-009 rank reversal: assessments, candidate_procedure_ids, decision_state, missing_critical_facts, retained_precedent_ids, safety_notes
- Active policy changed: `false`
- Held-out loaded: `false`
- Selector activation claim: `false`
- Status: **PASS**

The shadow trace is non-authoritative. It does not replace retained precedent IDs, decision state, missing-fact aggregation, or procedure eligibility.
