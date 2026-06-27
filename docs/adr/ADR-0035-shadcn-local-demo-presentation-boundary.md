# ADR-0035: shadcn Local Demo Presentation Boundary

- **Status:** Accepted for implementation
- **Date:** 2026-06-27
- **Scope:** Local synthetic demo presentation only

## Context

PR #44 created a working loopback-only browser demo served by the Python standard-library transport. The demo proves the governed typed packet boundary but its static HTML presentation is intentionally minimal.

The repository now needs a clearer, more polished reviewer experience without moving reliability decisions into a frontend.

## Decision

Add a separate Vite + React + Tailwind + shadcn/ui frontend under:

```text
apps/local-demo-ui/
```

During development, it runs only on `127.0.0.1:5173` and proxies `/api/*` to the existing Python demo server on `127.0.0.1:8765`.

The UI may:

- collect a sanitized typed browser payload;
- render fixed safe demo scenarios;
- render the typed `TriageEvidencePacket` returned by the Python boundary;
- make conclusion, uncertainty, human review, and no-execution posture easier to understand;
- expose technical JSON only on demand.

The UI must not:

- implement retrieval, policy, selection, procedure eligibility, or provider-degradation logic;
- derive a decision from raw form values;
- persist browser payloads;
- add authentication, uploads, connectors, tenants, or administrative features;
- alter `procedure_execution_authorized=false`.

## Architecture

```text
React/shadcn presentation
    -> POST /api/triage
    -> LocalDemoApplication
    -> existing TriageService
    -> typed TriageEvidencePacket
    -> React renderer
```

`/api/triage` remains the only runtime action endpoint.

## Acceptance criteria

- UI starts only on loopback.
- Vite proxy targets only `127.0.0.1:8765`.
- Every client request is structurally limited to the existing `LocalDemoPayload` contract.
- UI decision copy is a pure rendering map of the packet's policy state.
- Superlinked SIE stays visually and structurally advisory.
- Human review and no-execution posture remain prominent.
- `npm run test` and `npm run build` pass.
- Existing Python demo tests pass unchanged.

## Non-claims

This is not a production frontend, a customer portal, an operations console, or an execution system. It does not create customer-data validation, production readiness, retrieval correctness, or remediation authority.
