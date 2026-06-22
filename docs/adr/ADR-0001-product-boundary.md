# ADR-0001: Keep the Product Boundary at Historical Incident Evidence

- **Status:** Accepted
- **Date:** 2026-06-23
- **Decision owner:** Project maintainer

## Context

On-call engineers often need historical operational context during early incident triage. A broad product response would be to build alert ingestion, incident command, telemetry integrations, ticketing, scheduling, dashboards, remediation, or an autonomous SRE agent.

That would dilute the actual reliability question: whether a prior incident is comparable enough to surface without anchoring a responder on a harmful lookalike.

## Decision

The product will support a human responder by returning:

- candidate historical precedents;
- candidate investigation procedures;
- reasons a precedent may be relevant;
- reasons it may not apply;
- required verification facts;
- explicit conflict, missing-fact, insufficient-precedent, or provider-degraded states.

The product will not declare root cause, direct a remediation, execute a procedure, create/manage an incident, page anyone, ingest live telemetry, or act as an incident-management platform.

The final decision state must be deterministic application policy. A model/provider response can contribute validated signals or ranking data but may not directly determine the final state.

## Consequences

### Gains

- A narrow, inspectable reliability claim.
- A testable anti-anchoring failure mode: `false_operational_match`.
- A scope suitable for a 50-hour evidence project.
- A clear commercial story around retrieval reliability, regression prevention, and safe human review.

### Costs

- No claims about incident resolution time, production safety, remediation value, or live operational impact.
- The system will intentionally abstain rather than offer an attractive but weak match.

## Guardrails

The user-facing language must use `candidate precedent` and `candidate investigation procedure`, never `root cause`, `recommended fix`, `run this now`, `restart`, or `rollback`.

## Verification

Future acceptance tests must cover all five project decision states and must include false-operational-match, no-precedent, conflicting-precedent, and provider-degraded cases.
