# Procedure-Asymmetry Fixture Comparison

## Scope

This write-once report re-verifies the imported test-only fixture and evaluates only the standalone strict-dominance selector.
It does not load the active incident corpus, retrieval, held-out cases, procedures, or AntiAnchoringDecisionPolicy.

## Decision

**Decision: COMPARISON_PASSED_ACTIVATION_BLOCKED**

### Decision reasons

- All three isolated fixture cases matched their reviewer-controlled expected outcomes.
- The reversed candidate order preserved the primary selected representative.
- Procedure posture changed between the adversarial and neutral card sets while the typed-selection outcome remained stable.
- Activation remains blocked because this is governed test-only evidence, not policy-integrated independent held-out evidence.

## Comparison metrics

| Metric | Value |
|---|---:|
| Manifest-verified imported assets | 15 |
| Runtime cases | 3 |
| Expected outcomes | 3 |
| Exact outcome contract pass rate | 1.0 |
| Candidate-order invariance | true |
| Procedure asymmetry present | true |
| Procedure-neutral control parity | true |
| Import receipt verified | true |
| Active policy changed | false |
| Retrieval loaded | false |
| Held-out loaded | false |
| Selector activation claimed | false |

## Case outcomes

| Case | Card set | Expected | Actual | Contract |
|---|---|---|---|---|
| PAF-T02-001 | PAV-001-procedure-asymmetric | single_representative: INC-014 | single_representative: INC-014 | pass |
| PAF-T02-002 | PAV-001-procedure-asymmetric | single_representative: INC-014 | single_representative: INC-014 | pass |
| PAF-T02-003 | PAV-002-procedure-neutral-control | single_representative: INC-014 | single_representative: INC-014 | pass |

## Activation blockers

- The strict-dominance selector remains disconnected from AntiAnchoringDecisionPolicy.
- This fixture is a governed test-only adversarial control, not independent future held-out activation evidence.
- The fixture covers only connection_pool_exhaustion candidates and does not establish cross-family policy safety.
- Selector activation still requires a separate ADR, independently authored future held-out cases, policy integration review, and a promotion gate.

## Non-claims

- This harness does not load the active incident corpus, retrieval, held-out cases, procedures, or AntiAnchoringDecisionPolicy.
- Expected reason codes are evaluator diagnostics; they are not supplied to the selector and are not a selector-output contract.
- A passing comparison does not freeze Tranche 02, activate representative selection, authorize procedures, or prove production or customer-data readiness.
