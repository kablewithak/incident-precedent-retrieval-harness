# Incident Precedent Retrieval Harness — Handover 001

## 1. Handover identity

- **Handover date:** 2026-06-24
- **Phase:** Phase 0 — local SIE capability spike and provider-boundary ADR
- **Gate:** Verify `extract`, `encode`, and `score` through local Docker SIE, or
  explicitly record the block.
- **Gate status:** blocked for full three-operation local provider validation
- **Hours spent:** not measured in terminal evidence
- **Hours remaining:** not recalculated; retain the 50-hour project cap
- **Prepared from terminal evidence dated:** 2026-06-24

## 2. Verified repository state

- **Repository:** `incident-precedent-retrieval-harness`
- **Branch:** `spike/local-sie-capability-contracts`
- **Git status at evidence capture:** `scripts/provider_capability_spike.py` was
  untracked before this documentation/normalization slice.
- **Latest known commit:** `9aab5d2 chore: establish provider-neutral foundation`
- **Remote / push state:** verify from the next live terminal output; do not infer.
- **Python / virtual environment:** Python 3.12.10; `.venv` active in supplied
  terminal evidence.
- **Passing commands:** baseline unit suite had previously passed; current slice
  must rerun it after file replacement. Local `/healthz` returned `200 OK`.
- **Known block:** `urchade/gliner_multi-v2.1` exceeded local SIE's 600-second
  model-load budget and client 900-second provisioning budget.

## 3. Current technical boundary

- **Changed/evaluated boundary:** local Docker SIE provider capability and safe
  provider-failure normalization.
- **Expected behavior:** complete `extract`, `encode`, and `score` on synthetic
  inputs through the local SIE server.
- **Observed evidence:** `encode` and `score` passed; `extract` blocked by
  `ModelLoadTimeoutError` on the server and `ProvisioningError` in the client.
- **Invariants preserved:** provider-neutral protocol; fake client remains normal
  test seam; no raw provider payloads; no hosted endpoint claim.
- **Files added/changed in this slice:** capability spike script, failure
  normalization, unit tests, ADR, runbook, report, structured evidence, this
  handover, and optional dependency configuration.

## 4. Provider evidence

- **Active mode:** local Docker SIE with fake client for deterministic tests
- **Base URL:** `http://localhost:8080`
- **Health/readiness evidence:** local SIE container showed `healthy`; health
  endpoint returned `200 OK`.
- **Encode validation:** passed with `sentence-transformers/all-MiniLM-L6-v2`;
  384-dimension vector; 80,756 ms cold/provisioning observation.
- **Score validation:** passed with `cross-encoder/ms-marco-MiniLM-L-6-v2`;
  two ranks `[0, 1]`; 70,687 ms cold/provisioning observation.
- **Extract validation:** blocked for `urchade/gliner_multi-v2.1`; server load
  timeout 600 s, client provisioning timeout 900,004 ms.
- **Typed failure behavior:** `503` provisioning maps to `model_not_ready` while
  retry budget remains; terminal provisioning exhaustion maps to `retry_exhausted`.
- **Managed-hosted claim:** prohibited. No verified managed base URL exists.

## 5. Dataset and evaluation state

- **Corpus/procedure/source counts:** not started.
- **Held-out/calibration split:** not created.
- **Baseline pipelines:** not implemented.
- **Metrics/promotion gate:** absent by design at this phase.

## 6. Safety state

- **Decision states implemented/tested:** not yet implemented.
- **Provider-degraded behavior:** contract-level failure normalization is present;
  application-level `provider_degraded` decision remains future work.
- **Known safety risk:** do not present local SIE `encode`/`score` as a validated
  end-to-end incident-evidence system when extraction remains blocked.

## 7. Privacy and data boundary

- **Data used:** synthetic RelayOps incident text only.
- **Data prohibited/confirmed absent:** customer incidents, private logs,
  credentials, API keys, raw provider payloads, and real operational identifiers.
- **Trace fields retained:** operation/model/status/shape/latency and normalized
  failure metadata only.
- **Provider boundary:** local developer machine → local Docker SIE. No hosted
  endpoint or API key was used.

## 8. Evidence artifacts

- **ADR:** `docs/adr/ADR-0002-provider-boundary.md`
- **Report:** `docs/reports/phase-0-provider-capability-spike.md`
- **Machine-readable report:**
  `evidence_vault/reports/phase-0-local-sie-capability-spike.json`
- **Runbook:** `docs/runbooks/provider-spike-runbook.md`

## 9. Commercial translation

- **Offer supported:** AI System Evaluation Audit / RAG Reliability Improvement
  Sprint
- **Buyer pain:** a provider may appear healthy while a required model capability
  is unavailable or unboundedly slow.
- **Failure mode/cost reduced:** hidden model readiness failures and unmeasured
  fallback behavior during operational use.
- **Proof asset:** a reproducible capability report that distinguishes server
  health, operation readiness, and terminal provider degradation.
- **Why a CTO pays for ongoing ownership:** model/profile changes need evidence,
  failure classification, and repeatable regression checks rather than ad hoc demos.

## 10. Explicit non-claims

This work does not prove production readiness, hosted-provider access, customer
incident-data readiness, retrieval quality, safe historical precedent selection,
useful extraction labels, warm-operation latency, or safe remediation.

## 11. Next safest slice

- **Objective:** preserve the blocked Phase 0 report, then separately inspect
  documented local registry options for a CPU-appropriate extraction experiment.
- **Strict gate:** no alternate extraction profile becomes a project dependency or
  adapter default without a fresh branch, capability report, normalized failure
  behavior, and explicit ADR update.
- **Likely files:** a separate provider-experiment script/report; do not change
  retrieval policy or dataset code yet.
- **Minimum validation:** deterministic unit tests; local health; one isolated
  extract probe; server logs/stats on failure.
- **Do not do yet:** do not implement a full SIE adapter, do not claim complete
  `extract → encode → score`, do not author corpus data, and do not add a UI.
