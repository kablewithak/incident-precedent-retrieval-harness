# ADR-0003: Use a Source-Grounded Synthetic Dataset with a Frozen Holdout

- **Status:** Accepted
- **Date:** 2026-06-24
- **Decision owner:** Project maintainer

## Context

The project needs incident-like data to evaluate retrieval, false operational
matches, abstention, conflicts, and procedure safety. Real customer incidents,
private tickets, internal chat exports, production logs, and sensitive
infrastructure details are prohibited.

Generic AI-authored fiction would make retrieval results too easy to flatter.
Copying public postmortems would create attribution, licensing, and reuse risk.

## Decision

Build a coherent fictional **RelayOps** archive using public incident material
only as controlled source grounding. The data contract separates:

- source-grounded incident cards;
- controlled variants;
- synthetic no-precedent cases;
- calibration cases;
- frozen held-out cases.

Every source-grounded card needs a human-verified provenance record. Every
evaluation case must declare expected decision state, acceptable and unsafe
precedents, expected missing facts where relevant, failure-label intent, and an
acceptance reason.

The first data slice creates schemas and authoring rules only. It does not claim
the 32-card corpus or frozen 36-case holdout exists.

## Consequences

### Gains

- Source use remains inspectable and attributable.
- Safety cases become explicit assets, not prompt folklore.
- The holdout can later support a credible promotion gate.
- No private operational data enters the repository.

### Costs

- Dataset authoring is deliberate work rather than copy/paste.
- The project cannot claim real-world incident recall.
- Public-source review and transformation notes add friction by design.

## Verification

- Pydantic schemas reject missing source-grounded provenance.
- Pydantic schemas reject overlap between safe and unsafe procedure/precedent
  labels.
- No-precedent and conflict eval contracts reject unsafe label combinations.
- The source manifest and authoring guide are versioned with the code.
