# Provider Capability Spike Runbook

## Objective

Prove or explicitly block the three local SIE capabilities required by the
project:

1. `encode` for dense incident representations;
2. `score` for query/candidate reranking;
3. `extract` for bounded candidate operational signals.

## Precondition

The local server must be running, and:

```powershell
python .\scripts\check_sie_health.py
```

must show liveness and readiness as reachable.

## Install the spike dependency

The SDK is isolated to an explicit optional dependency so normal fake-provider
unit tests do not require Docker or the SIE SDK.

```powershell
python -m pip install -e ".[dev,provider-spike]"
```

## Scope

Use only synthetic, sanitized text. The spike must not use customer incidents,
private logs, API keys, raw public postmortem content, or live operational data.

## Run the probe

Run each operation independently for easier failure diagnosis:

```powershell
python .\scripts\provider_capability_spike.py --operation encode
python .\scripts\provider_capability_spike.py --operation score
python .\scripts\provider_capability_spike.py --operation extract
```

For a deliberate metadata-safe evidence artifact:

```powershell
python .\scripts\provider_capability_spike.py `
  --operation all `
  --output .\evidence_vault\reports\local-sie-capability-spike-latest.json
```

Do not commit an unreviewed raw provider payload. The script records only operation
status, model ID, response shape, latency, and a normalized safe failure class.

## Expected cold-start behavior

A healthy server can return temporary `503 Service Unavailable` responses while a
model downloads, loads, and warms. Treat that as `model_not_ready` only while the
bounded retry/provisioning budget remains. It is not a successful operation.

If the client exhausts its bounded provisioning budget, record a terminal
`retry_exhausted` result. Inspect the server state:

```powershell
docker logs --tail 250 incident-sie
docker stats --no-stream incident-sie
docker inspect incident-sie --format "{{json .State}}"
```

Do not hide a terminal provisioning timeout behind endless retries.

## Operation evidence to capture

For each operation, record:

- profile/model ID used;
- one bounded synthetic request;
- returned application-level shape, not raw payload;
- whether the observation is cold-start/provisioning or warm-operation latency;
- a safe normalized failure or invalid-input observation where feasible;
- whether the result can be converted to the typed project contract.

## Pass conditions

The full three-operation spike passes only when:

- an official SIE SDK client connects to the healthy local server;
- `encode` returns a usable dense vector for controlled text;
- `score` returns candidate scores/ranks for controlled text;
- `extract` returns bounded labeled signals for controlled text;
- each result can be converted to a Pydantic project response model;
- cold/warm observation categories are recorded separately;
- one provider failure can be normalized without raw payload leakage.

## Block conditions

The spike is blocked when any required operation cannot be validated in the
allotted Phase 0 budget, model choice remains unconfirmed, or raw provider shapes
cannot be safely normalized.

If blocked:

- keep the provider-neutral protocol and fake client;
- record the exact server and client evidence;
- mark the operation blocked rather than unsupported unless evidence supports
  unsupported capability;
- do not build against imagined model behavior;
- do not claim a fully validated real-SIE pipeline.

## Current project evidence

See:

```text
docs/reports/phase-0-provider-capability-spike.md
evidence_vault/reports/phase-0-local-sie-capability-spike.json
```

## Non-claims

A successful spike does not prove retrieval quality, anti-anchoring safety,
production readiness, hosted-provider access, real incident recall,
customer-data readiness, or safe remediation.
