# ADR-0034: Local Submission Demo Surface

- **Status:** Accepted
- **Date:** 2026-06-27
- **Decision owner:** Incident Precedent Retrieval Harness
- **Scope:** Local, synthetic-data, reviewer-facing demo only

## Context

The repository now has an inspectable evidence chain:

```text
structured historical incident corpus
-> deterministic keyword candidate generation
-> AntiAnchoringDecisionPolicy
-> typed TriageEvidencePacket
-> local Superlinked SIE semantic advisory
-> optional conditional representative display refinement
```

The frozen typed-triage promotion report remains blocked because the underlying
frozen keyword-policy baseline has a recorded EVAL-110 contract divergence. The
conditional representative-selection implementation does not claim to repair
that cross-family policy evidence. It is limited to same-family,
`connection_pool_exhaustion` display refinement after policy admission.

A reviewer needs a thin way to inspect the current behavior without turning the
project into an incident-management platform or suggesting production use.

## Decision

Add a local-only browser surface served by Python's standard-library HTTP server.

The server binds only to `127.0.0.1`, `localhost`, or `::1`. It has no upload
endpoint, authentication, persistence, connector, account, tenant, procedure
execution, or administrative feature.

The UI may submit only the typed runtime fields accepted by `TriageRequest`:

- sanitized incident summary;
- structured observed verification facts;
- declared provider availability; and
- optional validated `RepresentativeSelectionIntake`.

The server generates request and trace identifiers itself. It delegates all
retrieval, policy, provider, and selection behavior to the existing
`TriageService`; the browser may never calculate a policy decision or selection
outcome itself.

## Required rendering boundaries

The UI must render separate sections for:

1. policy-owned decision state, retained precedent IDs, missing facts, and
   candidate procedures;
2. optional display-only representative-selection refinement;
3. Superlinked SIE advisory status and candidate evidence;
4. `procedure_execution_authorized=false`; and
5. explicit local, synthetic-data, human-review, and non-claim language.

The UI must not present semantic rank or the display refinement as a diagnosis,
a remediation instruction, a decision override, or an execution authorization.

## Privacy and safety controls

- Server request logging is suppressed so browser summaries do not enter console
  logs.
- Request bodies are capped at 50 KB.
- Input is validated before entering the triage service.
- Sensitive-content rejection returns only a safe refusal message.
- The server writes no request payload, provider payload, prompt, or customer
  data to disk.
- The demo binds loopback only.

## Consequences

### Positive

- A reviewer can inspect real local `TriageEvidencePacket` behavior rather than a
  slide or mocked response.
- Superlinked SIE remains visible as an advisory provider boundary.
- The UI makes the evidence hierarchy legible: policy authority first, optional
  representative view second, semantic evidence advisory.

### Costs and limits

- The local dense index and local SIE configuration must exist for normal
  provider-available scenarios.
- The demo is not a deployment, a customer-data ingestion flow, or a multi-user
  product.
- A local provider failure should visibly produce the existing degraded packet;
  it must not be masked.

## Alternatives rejected

### Build a customer upload portal

Rejected. Historical company data intake requires separate review, provenance,
PII minimization, tenant, deletion, and publishing controls outside the 50-hour
proof scope.

### Add FastAPI or a hosted frontend stack

Rejected. The demonstration needs a single loopback-only transport, not a
new service platform or cloud deployment.

### Render static screenshots only

Rejected. The portfolio value comes from inspecting the governed runtime packet
and fail-closed behavior, not a cosmetic mockup.

## Non-claims

This local demo does not establish production readiness, customer-data safety,
provider availability, incident diagnosis, automated remediation, procedure
execution, or selector promotion beyond the existing scoped contracts.
