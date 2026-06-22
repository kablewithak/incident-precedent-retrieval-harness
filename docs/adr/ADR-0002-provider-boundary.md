# ADR-0002: Use a Provider-Neutral Semantic Inference Boundary with Local SIE First

- **Status:** Accepted
- **Date:** 2026-06-23
- **Decision owner:** Project maintainer

## Context

The initial provider posture is a local Docker Superlinked Inference Engine (SIE) server at `http://localhost:8080`. The active session has verified that the local container is healthy. The project also needs deterministic tests that do not require Docker, downloaded models, a network connection, or an API key.

Server health does not prove a model can successfully perform extraction, embedding, or reranking. The exact SIE SDK response shapes and suitable model IDs must therefore be validated in a separate capability spike before a real adapter is implemented.

## Decision

The application core will depend on `SemanticInferenceClient`, a provider-neutral protocol with three capabilities:

- extract constrained candidate signals;
- encode sanitized incident text;
- score query/candidate pairs.

Normal tests use `FakeSemanticInferenceClient`, a deterministic test double. It is deliberately not a machine-learning model and must not be used to claim retrieval quality.

A future `SuperlinkedSIEClient` will be implemented only after the local provider spike verifies all three operations through the official SDK. The adapter alone may import Superlinked SDK types or normalize raw provider exceptions/responses.

The following packages must remain free of provider SDK imports:

- domain and intake policy;
- retrieval and procedure policy;
- decision policy;
- evaluation harness and reports;
- CLI/local review surface;
- tests outside adapter integration tests.

## Error contract

The provider boundary exposes only typed, safe failure envelopes:

- `provider_unavailable`
- `provider_timeout`
- `model_not_ready`
- `unsupported_capability`
- `invalid_provider_response`
- `input_limit_exceeded`
- `rate_limited`
- `retry_exhausted`

No raw provider payload, exception type, authorization header, API key, or unredacted incident narrative may cross the boundary into ordinary logs or user-visible output.

## Consequences

### Gains

- Provider changes stay behind one adapter.
- Evaluation and policy behavior can be tested deterministically.
- Local Docker availability does not become a hidden dependency of normal tests.
- Provider degradation can be represented honestly as a typed application state.

### Costs

- A real adapter is deliberately delayed until operation contracts are evidenced.
- The fake client has no semantic-quality value; it exists only to prove boundaries, policies, and safe failures.

## Verification

The local provider spike must separately record:

1. health and readiness;
2. official SDK installation and client construction;
3. successful `encode` call and returned vector shape;
4. successful `score` call and returned rank/score shape;
5. successful `extract` call with bounded labels;
6. timeout or invalid-input behavior;
7. latency capture;
8. a typed adapter failure without raw payload leakage.
