# Local Docker SIE Runbook

## Purpose

Run the initial local Superlinked Inference Engine (SIE) server for controlled capability validation. This runbook does not authorize hosted-provider use, customer-data use, or production claims.

## Current local contract

```text
SIE_BASE_URL=http://localhost:8080
SIE_API_KEY=
SIE_TIMEOUT_SECONDS=30
```

The API key remains empty for local Docker mode. Do not place a managed-provider key in source control, `.env.example`, screenshots, logs, traces, reports, or pull requests.

## Session evidence already observed

The active bootstrap session verified:

- Docker Engine availability;
- image pull for `ghcr.io/superlinked/sie-server:latest-cpu-default`;
- a local named cache volume: `incident-sie-cache`;
- an `incident-sie` container healthy on `0.0.0.0:8080`;
- `GET /healthz` returning HTTP 200 and `ok`.

This establishes server availability only. It does not establish that an `extract`, `encode`, or `score` model call succeeds.

## Start the existing container

Use a dedicated PowerShell tab:

```powershell
docker start -ai incident-sie
```

Keep that terminal open. Pressing `Ctrl+C` stops the foreground-attached container.

## Stop the server when finished

From another PowerShell tab:

```powershell
docker stop incident-sie
```

Do not remove the container or the named cache volume during normal development. The cache avoids re-downloading model artifacts.

## Verify server availability

From the repository root after activating the local Python environment:

```powershell
python .\scripts\check_sie_health.py
```

Or inspect directly:

```powershell
curl.exe -i http://localhost:8080/healthz
curl.exe -i http://localhost:8080/readyz
```

Success condition: both endpoints return HTTP 200 and `ok`.

## Recreate only when intentionally resetting local SIE

```powershell
docker rm -f incident-sie
docker run --name incident-sie `
  -p 8080:8080 `
  -e SIE_DEVICE=cpu `
  -v incident-sie-cache:/app/.cache/huggingface `
  ghcr.io/superlinked/sie-server:latest-cpu-default
```

## Failure handling

- Port `8080` allocated: identify the owning Docker container before stopping anything.
- Container exits: use `docker logs incident-sie` and preserve the sanitized error evidence.
- Health succeeds but a model call fails: record it as a model-operation failure, not server availability success.
- Never paste an API key, raw incident narrative, or raw provider payload into a ticket, trace, or project artifact.
