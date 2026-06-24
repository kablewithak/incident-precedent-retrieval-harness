# ADR-0002: Use a Provider-Neutral Semantic Inference Boundary with Local SIE First

- **Status:** Accepted
- **Date:** 2026-06-24
- **Decision owner:** Project maintainer

## Context

The initial provider posture is a local Docker Superlinked Inference Engine (SIE)
server at `http://localhost:8080`. Deterministic tests must not depend on Docker,
downloaded models, a network connection, or an API key.

The local server is healthy. A Phase 0 capability spike then tested the three
required primitives through `sie-sdk 0.6.12` using synthetic text:

- `encode` returned a valid 384-dimension vector;
- `score` returned two rankable candidates;
- `extract` using `urchade/gliner_multi-v2.1` did not become ready within the
  local server's 600-second model-load budget. The client exhausted its
  900-second provisioning budget.

The container remained healthy and was not OOM-killed. See
`docs/reports/phase-0-provider-capability-spike.md` for the evidence record.

## Decision

The application core will depend on `SemanticInferenceClient`, a provider-neutral
protocol with three capabilities:

- extract constrained candidate signals;
- encode sanitized incident text;
- score query/candidate pairs.

Normal tests use `FakeSemanticInferenceClient`, a deterministic test double. It
is deliberately not a machine-learning model and must not be used to claim
retrieval quality.

A full `SuperlinkedSIEClient` is **not approved as the default application
provider** until all three operations have been validated through the local
provider or a new ADR approves an explicitly documented extraction alternative.

Until then:

- `encode` and `score` are verified local capability observations only;
- `extract` is blocked for the tested local CPU/model configuration;
- no full `extract → encode → score` claim is permitted;
- core policy, evaluation, and future retrieval work must retain the fake provider
  as their deterministic test seam.

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

The adapter's retry controller must distinguish:

1. temporary `503` responses during model provisioning → `model_not_ready`,
   retryable while the bounded budget remains;
2. exhausted provisioning budget or terminal model-load timeout →
   `retry_exhausted`, non-retryable for that request.

No raw provider payload, exception text, authorization header, API key, or
unredacted incident narrative may cross into ordinary logs or user-visible output.

## Consequences

### Gains

- Provider changes stay behind one adapter.
- Evaluation and policy behavior remain deterministic under the fake client.
- The exact local CPU blocker is visible rather than hidden by retries.
- Future fallback/model experiments must earn their own evidence.

### Costs

- Real adapter implementation is delayed until the extraction path is evidenced.
- Local `encode` and `score` observations do not yet deliver an end-to-end live
  inference pipeline.
- The fake client has no semantic-quality value; it exists only to prove
  boundaries, policies, and safe failures.

## Verification

The first provider spike established:

1. health and readiness;
2. official SDK installation and client construction;
3. successful `encode` response shape;
4. successful `score` rank/score shape;
5. terminal extraction provisioning failure with server-side timeout evidence;
6. no OOM termination;
7. latency capture;
8. provider-failure normalization tests.

The next live provider experiment must use a separate branch, state the candidate
extraction model/profile, record cold/warm results, and update the capability
report rather than replacing this blocked evidence.
