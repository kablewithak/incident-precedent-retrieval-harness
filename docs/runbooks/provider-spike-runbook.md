# Provider Capability Spike Runbook

## Objective

Prove or explicitly block the three local SIE capabilities required by the project:

1. `encode` for dense incident representations;
2. `score` for query/candidate reranking;
3. `extract` for bounded candidate operational signals.

## Precondition

`python .\scripts\check_sie_health.py` must show liveness and readiness as reachable.

## Scope

Use only synthetic, sanitized text. The spike must not use customer incidents, private logs, API keys, raw public postmortem content, or live operational data.

## Operation evidence to capture

For each operation, record:

- profile/model ID used;
- one bounded synthetic request;
- returned application-level shape, not raw payload;
- elapsed latency in milliseconds;
- a safe failure or invalid-input observation where feasible;
- whether the result can be normalized into the typed project contract.

## Fixed synthetic inputs

### Encode

```text
Queue backlog started after a webhook-worker deployment. Consumer errors increased.
```

### Score

Query:

```text
Queue backlog after worker deployment with consumer errors.
```

Candidates:

```text
A. Worker schema incompatibility caused consumer failures and queue growth after deployment.
B. Redis cache invalidation caused a cache stampede and elevated API latency.
```

### Extract labels

```text
service
component
symptom
change_context
```

## Pass conditions

The spike passes only when:

- an official SIE SDK client can connect to the healthy local server;
- `encode` returns a usable dense vector for controlled text;
- `score` returns candidate scores/ranks for controlled text;
- `extract` returns bounded labeled signals for controlled text;
- each result can be converted to a Pydantic project response model;
- observed latency is recorded;
- one error path becomes a typed project failure with no raw payload leakage.

## Block conditions

The spike is blocked when any required operation cannot be validated in the allotted Phase 0 budget, model choice remains unconfirmed, or raw provider shapes cannot be safely normalized.

If blocked, keep the protocol and fake provider, document the evidence, and do not build against assumed SIE behavior.

## Non-claims

A successful spike does not prove retrieval quality, anti-anchoring safety, production readiness, hosted-provider access, real incident recall, customer-data readiness, or safe remediation.
