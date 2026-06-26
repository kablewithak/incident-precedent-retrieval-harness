# ADR-0019: Governed Procedure-Asymmetry Fixture Boundary for Tranche 02

- **Status:** Accepted for design; implementation blocked pending a fresh blinded authoring package
- **Date:** 2026-06-26
- **Decision owners:** Repository maintainer and evaluation reviewer
- **Related:** ADR-0012, ADR-0018, Tranche 02 blind-authoring acceptance audit

## Context

The Tranche 02 constitution requires a no-hidden-legacy-tie-break case in which lexical rank, incident identifier order, and procedure availability would favor a different candidate from the strict-dominance result.

The current profiled `connection_pool_exhaustion` cards cannot provide that test: each carries the same linked/safe/unsafe procedure posture. The blind-authoring proposal correctly recorded the gap. No existing or proposed case may be relabeled as satisfying it.

The strict-dominance selector must not use procedure metadata. A dedicated adversarial fixture is needed to preserve that regression boundary without changing the source incident corpus, the active policy, or historical evaluation assets.

## Decision

Create a **test-only, separately governed procedure-asymmetry fixture set** after a fresh blinded authoring session.

The fixture set must:

1. Live outside `data/incidents`, active policy fixtures, selector calibration fixtures, E1 fixtures, and prior Tranche assets.
2. Be loaded only by the Tranche 02 comparison harness.
3. Contain at least one same-family candidate pool where:
   - typed selection evidence strictly favors one candidate;
   - procedure metadata is intentionally more favorable for a different candidate;
   - candidate order and incident identifier order also favor the non-winning candidate;
   - the expected selector result remains determined only by the typed selection contract.
4. Include an order-reversed partner case.
5. Preserve valid `HistoricalIncidentCard` and `RepresentativeSelectionSignature` contracts.
6. Record the controlled-fixture provenance, perturbation purpose, and non-production status.
7. Be authored in a new blinded session that receives the governing boundary and schema, but not selector calibration labels, E1 fixtures, Tranche 01 outcomes, prior Tranche 02 proposal labels, or selector implementation behavior.

## Prohibited approaches

- Do not mutate an existing source incident card in place.
- Do not change procedure metadata on cards loaded by the active policy.
- Do not add procedure availability, rank, score, identifiers, or free-text fields to `RepresentativeSelectionIntake`.
- Do not normalize or patch selector outcomes after observing a result.
- Do not claim that this fixture makes active policy order-invariant or authorizes selector activation.

## Required future evaluation checks

The future Tranche 02 harness must prove:

- same typed intake and signatures yield the same selection outcome when only procedure metadata changes;
- the procedure-favored, earlier, or lower-ID candidate does not replace the strict-dominance winner;
- order reversal leaves the selection outcome unchanged;
- invalid fixtures fail closed before selector execution;
- the fixture is not loaded by active-policy, retrieval, or held-out evaluation paths.

## Consequences

Tranche 02 remains unfrozen until this fixture gap is resolved and the reviewed set is reissued with new manifests and final stable IDs.

This ADR raises evaluation rigor. It does not alter the active policy or selector authority.
