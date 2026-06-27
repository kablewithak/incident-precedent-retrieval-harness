# Representative-Selection Calibration Readiness

## Scope

This write-once report evaluates the standalone strict-dominance selector only on dedicated selection-calibration fixtures.
It does not load held-out evaluation fixtures, invoke retrieval or semantic inference, or activate selector output in the active anti-anchoring policy.

## Decision

**Decision: CALIBRATION_PASSED_ACTIVATION_BLOCKED**

### Decision reasons

- All fixed selection-calibration contracts passed.
- Fixed order-invariance groups produced identical results.
- Activation remains blocked because calibration is not independent held-out evidence and the selector is not wired into the active policy.

## Calibration metrics

| Metric | Value |
|---|---:|
| Fixed selection-calibration cases | 10 |
| Contract pass rate | 1.0 |
| Single-representative outcomes | 7 |
| Explicit-tie outcomes | 3 |
| Order-invariance groups | 1 |
| Order-invariance pass rate | 1.0 |
| All candidates in approved family scope | true |
| Held-out loaded | false |
| Retrieval loaded | false |
| Active policy changed | false |
| Selector activation claimed | false |

## Case outcomes

| Case | Expected | Actual | Contract | Order group |
|---|---|---|---|---|
| SEL-CAL-001 | single_representative: INC-009 | single_representative: INC-009 | pass | none |
| SEL-CAL-002 | single_representative: INC-010 | single_representative: INC-010 | pass | none |
| SEL-CAL-003 | single_representative: INC-011 | single_representative: INC-011 | pass | none |
| SEL-CAL-004 | explicit_tie: INC-009, INC-012 | explicit_tie: INC-009, INC-012 | pass | none |
| SEL-CAL-005 | explicit_tie: INC-009, INC-010 | explicit_tie: INC-009, INC-010 | pass | none |
| SEL-CAL-006 | explicit_tie: INC-009, INC-010, INC-011, INC-012 | explicit_tie: INC-009, INC-010, INC-011, INC-012 | pass | none |
| SEL-CAL-007 | single_representative: INC-009 | single_representative: INC-009 | pass | ORDER-INVARIANCE-001 |
| SEL-CAL-008 | single_representative: INC-009 | single_representative: INC-009 | pass | ORDER-INVARIANCE-001 |
| SEL-CAL-009 | single_representative: INC-012 | single_representative: INC-012 | pass | none |
| SEL-CAL-010 | single_representative: INC-012 | single_representative: INC-012 | pass | none |

## Activation blockers

- The strict-dominance selector is not wired into AntiAnchoringDecisionPolicy and remains shadow-only.
- Calibration fixtures are not independent held-out evidence for an activation change.
- The selector currently supports connection_pool_exhaustion cards only; active policy covers additional incident families.
- Any activation proposal requires a separate ADR, an independently authored future held-out tranche, and a new promotion gate.

## Non-claims

- This report does not load the frozen held-out tranche or reuse EVAL-110 as a calibration fixture.
- This report does not invoke lexical retrieval, dense retrieval, semantic inference, or provider infrastructure.
- This report does not modify or activate AntiAnchoringDecisionPolicy.
- A calibration pass does not prove that activation will preserve held-out behavior, improve retrieval, authorize a procedure, or establish production readiness.
