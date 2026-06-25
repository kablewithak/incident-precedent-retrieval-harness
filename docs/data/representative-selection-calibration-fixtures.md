# Representative-Selection Calibration Fixtures

## Status

Calibration-only fixture set for the schema-derived representative-selection
contract in ADR-0012. These assets define expected outcomes for a future
selection module; they do not activate selection in the current runtime.

## Boundary

The fixtures are stored separately from:

- `data/evals/calibration/`, which drives the active anti-anchoring policy;
- `data/evals/heldout/`, which remains outside this slice;
- retrieval rank and score artifacts;
- procedure-eligibility and final decision-state labels.

Each fixture contains two deliberately separate parts:

1. `selection_intake`: typed, selector-permitted evidence only.
2. `expected_outcome`: calibration label used only to evaluate a future selector.

The selection intake cannot carry incident IDs, expected decision states,
procedures, retriever rank, or retriever score.

## Fixture inventory

| Fixture | Boundary tested | Expected result |
|---|---|---|
| `SEL-CAL-001` | Exact payments component, no-change context, pool and active-connection signals | `INC-009` |
| `SEL-CAL-002` | Auth-service and configuration alignment without component input | `INC-010` |
| `SEL-CAL-003` | Exact feature-flag component, deployment context, distinct signals | `INC-011` |
| `SEL-CAL-004` | Correlated pool phrases contribute one signal family | Explicit tie: `INC-009`, `INC-012` |
| `SEL-CAL-005` | Service/component/context trade-off has no hidden weight preference | Explicit tie: `INC-009`, `INC-010` |
| `SEL-CAL-006` | No distinguishing evidence | Explicit tie across all four cards |
| `SEL-CAL-007` | Canonical candidate order | `INC-009` |
| `SEL-CAL-008` | Reversed candidate order for `ORDER-INVARIANCE-001` | `INC-009` |
| `SEL-CAL-009` | Webhook delivery identity plus queue and retry signals | `INC-012` |
| `SEL-CAL-010` | Explicit active-connection contradiction | `INC-012` |

## Integrity rules

- Every candidate ID must resolve to a current connection-pool card.
- Every candidate card must have a validated schema-derived selection signature.
- Order-invariance pairs must have identical input and label contracts, with an
  exact reversal of candidate serialization order.
- Expected representatives must be within the fixture candidate set.
- No fixture can silently use held-out data or mutate the active policy.

## Non-claims

This fixture set does not prove that a representative selector is implemented,
correct, active, promoted, or safe on held-out data. It is calibration evidence
only.
