# Strict-Dominance Representative-Selection Calibration Report

## Scope

This report evaluates only the standalone strict-dominance selector on dedicated selection-calibration fixtures. It does not load held-out cases, invoke retrieval, change the active policy, or authorize activation.

## Result

- Selection calibration cases: `10`
- Passed cases: `10`
- Failed cases: `0`
- Contract pass rate: `1.0`
- Active policy changed: `false`
- Held-out loaded: `false`
- Retrieval loaded: `false`
- Selector activation claim: `false`

## Case Outcomes

| Case | Result | Expected | Actual |
|---|---|---|---|
| SEL-CAL-001 | PASS | single_representative: INC-009 | single_representative: INC-009 |
| SEL-CAL-002 | PASS | single_representative: INC-010 | single_representative: INC-010 |
| SEL-CAL-003 | PASS | single_representative: INC-011 | single_representative: INC-011 |
| SEL-CAL-004 | PASS | explicit_tie: INC-009, INC-012 | explicit_tie: INC-009, INC-012 |
| SEL-CAL-005 | PASS | explicit_tie: INC-009, INC-010 | explicit_tie: INC-009, INC-010 |
| SEL-CAL-006 | PASS | explicit_tie: INC-009, INC-010, INC-011, INC-012 | explicit_tie: INC-009, INC-010, INC-011, INC-012 |
| SEL-CAL-007 | PASS | single_representative: INC-009 | single_representative: INC-009 |
| SEL-CAL-008 | PASS | single_representative: INC-009 | single_representative: INC-009 |
| SEL-CAL-009 | PASS | single_representative: INC-012 | single_representative: INC-012 |
| SEL-CAL-010 | PASS | single_representative: INC-012 | single_representative: INC-012 |

## Non-claims

- This report does not activate representative selection in AntiAnchoringDecisionPolicy.
- This report does not evaluate held-out cases or establish promotion eligibility.
- This report does not claim production incident-response safety or retrieval improvement.
