# Tranche 02 Future-Held-Out Comparison

## Decision

`comparison_passed_activation_blocked`

## Frozen evidence

- Frozen fixture: `data/evals/heldout/tranche_02_future_heldout`
- Freeze manifest: `data/evals/heldout/tranche_02_future_heldout/TRANCHE_02_FUTURE_HELDOUT_FREEZE_MANIFEST.json`
- Freeze receipt: `evidence_vault/reports/tranche-02-future-heldout-freeze.json`

## Metrics

- Valid selector cases: `10`
- Pre-selector rejection controls: `2`
- Valid-case contract pass rate: `1.00`
- Order invariance: `true`
- Source-card hashes verified: `true`
- Failed cases: `none`

## Case outcomes

| Case | Selector executed | Expected | Actual | Contract match |
|---|---:|---|---|---:|
| SEL-T02-FH-001 | true | single_representative | single_representative | true |
| SEL-T02-FH-002 | true | single_representative | single_representative | true |
| SEL-T02-FH-003 | true | single_representative | single_representative | true |
| SEL-T02-FH-004 | true | single_representative | single_representative | true |
| SEL-T02-FH-005 | true | explicit_tie | explicit_tie | true |
| SEL-T02-FH-006 | true | explicit_tie | explicit_tie | true |
| SEL-T02-FH-007 | true | explicit_tie | explicit_tie | true |
| SEL-T02-FH-008 | true | explicit_tie | explicit_tie | true |
| SEL-T02-FH-009 | true | explicit_tie | explicit_tie | true |
| SEL-T02-FH-010 | true | single_representative | single_representative | true |
| SEL-T02-FH-011 | false | invalid_input | pre-selector rejection | true |
| SEL-T02-FH-012 | false | invalid_input | pre-selector rejection | true |

## Activation blockers

- The strict-dominance selector remains disconnected from AntiAnchoringDecisionPolicy.
- No activation ADR or active-policy integration review has authorized selector activation.
- This frozen comparison does not establish decision-state, procedure-withholding, provider-degraded, retrieval, or production safety for an integrated runtime path.

## Non-claims

- Expected outcomes are evaluator-only oracles and are never supplied to selector invocation.
- This comparison does not alter retrieval, active policy, procedures, Tranche 01, provider behavior, or any production-facing decision path.
- A passing comparison does not authorize procedure execution, production use, customer-data validation, or automated incident response.
