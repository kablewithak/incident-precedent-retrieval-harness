# ADR-0032: Frozen Tranche 02 Representative-Selection Comparison

## Status

Accepted implementation boundary.

## Context

Tranche 02 was independently authored, acceptance-audited, and imported through
a fail-closed write-once freeze boundary. The frozen asset tree contains twelve
runtime inputs and twelve structurally separate evaluator-only outcomes.

Ten cases permit isolated strict-dominance selector execution. Two are negative
controls that must reject before selector execution:

- `SEL-T02-FH-011`: duplicate typed operational-signal family;
- `SEL-T02-FH-012`: genuinely mixed-family candidate pool.

The system now needs one predeclared comparison against this frozen material.
It must be reproducible without allowing the selector, active policy, or
retrieval code to consume evaluator-only outcomes during normal runtime.

## Decision

Add a write-once frozen comparison gate that:

1. verifies the freeze manifest and freeze receipt before loading any case;
2. re-verifies the exact frozen file set, asset hashes, byte counts, and
   frozen aggregate hashes;
3. loads evaluator outcomes only inside the comparison harness;
4. re-verifies every source-card SHA-256 and typed card contract used by each
   frozen case;
5. invokes `StrictDominanceRepresentativeSelector` only for the ten
   selector-permitted, same-family `connection_pool_exhaustion` cases;
6. proves both invalid controls reject before selector invocation;
7. proves the exact FH-001/FH-002 reversal pair has the same result;
8. writes JSON and Markdown evidence once;
9. returns either:
   - `comparison_passed_activation_blocked`,
   - `comparison_blocked`, or
   - `insufficient_evidence`.

## Decision semantics

A passing comparison means the isolated selector agrees with the frozen
evaluator-controlled oracle on this tranche. It does **not** activate the
selector.

Selector activation remains blocked because this gate does not:

- integrate selection into `AntiAnchoringDecisionPolicy`;
- prove active-policy admission invariance;
- prove decision-state, procedure-withholding, retrieval, or provider-degraded
  safety in the integrated path;
- constitute an activation ADR or production authorization.

## Scope controls

This boundary must not import or invoke:

- `AntiAnchoringDecisionPolicy`;
- retrieval, dense indexes, reranking, or provider adapters;
- procedures;
- Tranche 01 fixtures or reports;
- procedure-asymmetry fixture assets.

Source incident cards are read only to verify the exact hashes declared in the
frozen evaluator outcomes and to supply the already schema-derived candidate
signatures required by the isolated selector.

## Non-claims

This comparison does not authorize production use, customer-data validation,
procedure execution, automated remediation, or incident-response decisions.
