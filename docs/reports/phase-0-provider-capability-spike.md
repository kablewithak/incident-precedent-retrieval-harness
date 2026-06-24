# Phase 0 Provider Capability Spike — Local Docker SIE

- **Evidence date:** 2026-06-24
- **Repository branch at capture:** `spike/local-sie-capability-contracts`
- **Inference mode:** local Docker SIE on `http://localhost:8080`
- **SDK observed:** `sie-sdk 0.6.12`
- **Input posture:** synthetic RelayOps incident text only
- **Gate status:** **blocked for full three-operation adapter implementation**

## Question

Can the local CPU SIE environment complete the three operations required by the
project's intended semantic boundary: `encode`, `score`, and `extract`?

## Preconditions verified

| Check | Result |
|---|---|
| Docker Engine available | Passed |
| `incident-sie` container running | Passed |
| Container health | `healthy` |
| `/healthz` | `200 OK` |
| `/readyz` | `200 OK` |
| API key required locally | No |
| Container out-of-memory termination | Not observed (`OOMKilled=false`) |

## Operation evidence

| Operation | Model | Result | Evidence | Interpretation |
|---|---|---:|---|---|
| `encode` | `sentence-transformers/all-MiniLM-L6-v2` | Passed | 384-dimension vector; 80,756 ms observed | Contract validated. Timing is cold-start/provisioning evidence, not a steady-state latency result. |
| `score` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Passed | Two entries with ranks `[0, 1]`; 70,687 ms observed | Contract validated. CPU fallback was used; timing is cold-start/provisioning evidence, not a triage-latency result. |
| `extract` | `urchade/gliner_multi-v2.1` | Blocked | SDK `ProvisioningError` after 900,004 ms; server `ModelLoadTimeoutError` after 600 s | The configured extraction model did not become ready within the local server's load budget. |

The structured machine-readable evidence is stored at:

```text
evidence_vault/reports/phase-0-local-sie-capability-spike.json
```

## Root-cause evidence

The server remained healthy while extraction was unavailable. It returned repeated
`503 Service Unavailable` responses while attempting background provisioning.
The server then reported a terminal `ModelLoadTimeoutError` for
`urchade/gliner_multi-v2.1` after its 600-second model-load budget elapsed.

This is not an out-of-memory failure. At inspection time, the container reported
`OOMKilled=false`, remained healthy, and used about 1.33 GiB of its 7.64 GiB
memory limit.

## Engineering decision

The project must not claim a fully validated local SIE `extract → encode → score`
pipeline.

The next provider boundary must support two distinct states:

1. **Transient model provisioning:** a bounded `model_not_ready` failure for a
   retriable `503` before the retry budget is consumed.
2. **Terminal provisioning exhaustion:** a non-retryable `retry_exhausted`
   failure once the configured provisioning budget is consumed.

`failure_normalization.py` captures these safe, provider-neutral failure envelopes.
No raw provider payloads, internal paths, or source text are stored in the evidence
artifact.

## Scope decision

Do not retry this same model indefinitely and do not add a full SIE adapter yet.
The fake client remains the deterministic CI/test seam.

A later provider experiment may inspect the local model registry for a documented,
CPU-appropriate extraction option. That is a separate experiment; it is not a
silent substitution and it must produce a fresh capability report.

## Non-claims

This evidence does not prove:

- retrieval quality or safe operational comparability;
- model/profile suitability for this project;
- extraction-label usefulness;
- warm-operation p50/p95 latency;
- hosted-provider access;
- customer-data readiness;
- production readiness or safe remediation.

## Next safest slice

Freeze this Phase 0 evidence and introduce the real adapter only after a separate
ADR-approved extraction path is proven. Continue core contract, policy, and
future retrieval work with the deterministic fake provider rather than inventing
unverified live extraction behavior.
