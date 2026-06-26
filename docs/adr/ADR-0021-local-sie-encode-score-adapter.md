# ADR-0021: Local SIE Encode and Score Adapter

- **Status:** Accepted for local submission-path validation
- **Date:** 2026-06-26

## Context

The Phase 0 local Docker SIE spike validated the response contracts for:

- `encode` with `sentence-transformers/all-MiniLM-L6-v2`;
- `score` with `cross-encoder/ms-marco-MiniLM-L-6-v2`.

The tested `extract` model did not provision within the local server load budget.
The submission architecture is therefore structured-first. Existing typed input
contracts provide canonical incident facts; local SIE provides dense encoding and
reranking only.

## Decision

Add `SuperlinkedSIEClient` as the only concrete SIE SDK boundary.

The adapter:

- supports `encode` and `score` through typed request and response contracts;
- keeps SDK imports, response mapping, and exception text inside the adapter;
- validates dense vectors, dimensions, score count, finite raw relevance values, and rank coverage;
- converts zero-based SDK ranks to the one-based application contract;
- normalizes provider failures to trace-safe `ProviderFailure` envelopes;
- fails closed for `extract` with `unsupported_capability`;
- permits only local endpoint construction for this submission path.

The first local profiles have zero retries. The Phase 0 timings were cold-start
provisioning evidence, not steady-state latency. A later evaluation slice will
measure warm-operation behavior before any latency claim.

## Consequences

- The application can now call real local SIE encode and score without leaking SDK
  types into retrieval, policy, evaluation, or CLI code.
- Ordinary tests stay deterministic through injected stubs and the existing fake
  provider. Local Docker validation remains an intentional manual command.
- This ADR does not add dense retrieval, reranking orchestration, indexing,
  selector activation, held-out changes, or production claims.

## Raw Score Semantics

Local SIE `score` returns finite, provider-native raw relevance values. They are
not calibrated probabilities: valid values may be negative or exceed one. The
application preserves those values for traceable evidence while treating the
returned rank as the ordering contract. Thresholding or score normalization is
not introduced at this adapter boundary.
