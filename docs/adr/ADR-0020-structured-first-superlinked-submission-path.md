# ADR-0020: Use a Structured-First Superlinked Submission Path

- **Status:** Accepted
- **Date:** 2026-06-26
- **Decision owner:** Project maintainer

## Context

The project goal is an evaluated incident-precedent retrieval harness, not a
standalone representative-selection experiment. A Superlinked Inference Engine
submission must demonstrate a credible team workflow:

```text
reviewed historical incident export
→ controlled ingestion
→ SIE encode
→ local dense retrieval
→ SIE score reranking
→ deterministic anti-anchoring policy
→ typed evidence packet for human triage
```

Phase 0 evidence established that local Docker SIE successfully completed
`encode` and `score` operations using synthetic RelayOps text. The tested
`extract` model failed to become ready within the local server's provisioning
budget. The server remained healthy; this is a model-readiness limitation, not
proof that extraction is available.

The repository also contains valuable representative-selection, shadow-policy,
and procedure-asymmetry safety evidence. Those artifacts protect the broader
anti-anchoring claim, but they are not the product's primary submission path.

## Decision

The submission path is **structured-first**.

### Required submission operations

The submission path requires:

- controlled historical-incident ingestion from JSONL;
- explicit provenance and review state;
- SIE `encode` for corpus and query representations;
- local dense candidate retrieval;
- SIE `score` for reranking a bounded candidate set;
- deterministic safety, procedure-eligibility, conflict, missing-fact, and
  provider-degraded policy;
- reproducible pipeline comparison and a promotion decision.

### Optional operation

SIE `extract` is optional enrichment only. It may not be described as part of
the submitted runtime path unless a later capability experiment validates an
approved extraction model and records fresh evidence.

### Controlled ingestion boundary

The first ingestion slice accepts a reviewed-input candidate export and produces
only a trace-safe inspection report. It must not:

- write directly to `data/incidents/`;
- modify procedures, calibration cases, held-out assets, or frozen evidence;
- infer incident-family labels, procedure safety, or final provenance;
- call SIE;
- log raw incident summaries, source documents, or sensitive matches.

A later canonicalization-and-indexing slice may consume only a clean,
review-approved import inspection result.

### Safety evidence posture

The existing representative-selection and procedure-asymmetry artifacts remain
preserved as safety-regression evidence. They do not authorize selector
activation or alter public decision semantics.

## Consequences

### Gains

- The project can demonstrate real SIE inference without claiming an unverified
  extraction capability.
- The product path matches how an engineering team would maintain an approved
  historical incident corpus after incidents are resolved.
- Ingestion remains separate from current triage, evaluation, and policy paths.
- The remaining work becomes a bounded submission-completion sprint rather than
  more selector-fixture expansion.

### Costs

- Structured team exports require a defined schema and human review step.
- The initial submission cannot claim free-text extraction from arbitrary
  postmortems or raw incident channels.
- The first ingestion slice is review-only; it is not a production connector or
  automated corpus sync.

## Verification and next gate

This ADR is implemented incrementally.

The first gate passes only when a JSONL demo export can be inspected with:

```text
- strict typed validation;
- duplicate detection;
- fail-closed sensitive-content detection;
- stable batch hash;
- trace-safe report output;
- zero writes to corpus, eval, procedure, or evidence paths.
```

The next gate is a typed Superlinked `encode` and `score` adapter with a fresh
local capability confirmation. No claim of end-to-end semantic retrieval is
permitted before that adapter, dense index, reranking path, and fixed evaluation
comparison exist.

## Non-claims

This decision does not establish:

- production ingestion;
- customer-data readiness;
- Slack, PagerDuty, ticketing, or observability integrations;
- real-SIE extraction;
- selector activation;
- promotion for production use;
- automated remediation.
