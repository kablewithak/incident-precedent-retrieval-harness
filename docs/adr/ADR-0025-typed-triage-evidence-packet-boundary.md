# ADR-0025: Typed triage evidence packet boundary

## Status

Accepted for a calibration-only, local-SIE implementation slice.

## Decision

Introduce a typed non-executing triage packet that joins:

1. the existing deterministic `AntiAnchoringDecisionPolicy`, fed only by its current keyword top-5 candidate source; and
2. local-SIE dense top-5 candidate evidence, held in a separate advisory field.

The policy remains the only authority for decision state, retained precedent IDs, missing facts, conflict behavior, and candidate procedure eligibility. Semantic candidate rank, similarity, presence, absence, and order cannot enter the active policy call.

## Invariants

- Every valid packet requires human review.
- Every valid packet sets `procedure_execution_authorized` to `false`.
- A local-SIE encode failure or explicit provider-unavailable intake produces `provider_degraded`, no semantic candidates, no retained precedents, and no candidate procedures.
- Semantic evidence is capped at five dense candidates and is not reranked in this product boundary. Dense-plus-score has no measured calibration gain and hybrid retrieval was rejected.
- Runtime summaries with high-risk secret or PII indicators are rejected before provider invocation. Findings contain only safe codes, never matched text.
- Calibration reporting loads calibration fixtures only. It records policy-state parity and control behavior, not retrieval superiority.

## Consequences

This creates the first product-shaped path without claiming that a retrieval variant is promoted. Future work may change the policy candidate source only after a dedicated integration ADR, fixed evaluation cases, trace review, and held-out gate. The legacy rank-sensitive policy remains unchanged by this ADR.
