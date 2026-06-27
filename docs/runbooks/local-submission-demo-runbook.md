# Local Submission Demo Runbook

## Purpose

Run the loopback-only **Related Incident Evidence** demo against the existing
synthetic RelayOps corpus, local dense index, typed policy boundary, and local
Superlinked SIE adapter.

The demo does not upload company data, persist browser input, execute procedures,
or create a production endpoint.

## Preconditions

- You are on the dedicated demo branch.
- The local dense index exists:

```text
evidence_vault/indexes/local-sie-dense-index-v1.json
```

- The `provider-spike` dependency was installed previously for the local SIE path.
- Local Docker SIE is available for provider-available scenarios.
- No `.env` value, API key, raw provider response, or sensitive runtime input is
  copied into a report, commit, or screenshot.

## Validate the deterministic boundary

```powershell
python -m pytest .\tests\unit\test_local_demo_application.py

python -m pytest .\tests\unit
```

## Verify local prerequisites

```powershell
Get-Item .\evidence_vault\indexes\local-sie-dense-index-v1.json

python -c "import sie_sdk; print('sie-sdk available')"

docker start incident-sie
```

If the container does not exist or cannot start, stop here. Do not substitute a
hosted endpoint or claim a provider-available demo. The `Provider degraded`
scenario may still demonstrate the declared fail-closed policy path.

## Start the local demo

```powershell
python .\scripts\run_local_submission_demo.py `
    --repository-root . `
    --port 8765
```

The server prints a loopback URL similar to:

```text
http://127.0.0.1:8765
```

Open that URL locally. Keep the PowerShell window running while using the demo.
Use `Ctrl+C` in that same window to stop it.

## Suggested reviewer flow

1. **Connection-pool evidence** — inspect policy decision, advisory candidates,
   and optional display-only representative refinement.
2. **Cross-family conflict** — show that policy retains ambiguity and withholds a
   preferred procedure.
3. **Insufficient precedent** — show abstention rather than fabricated evidence.
4. **Provider degraded** — show that candidate precedent and procedures are not
   presented when provider availability is declared false.
5. Open the typed packet JSON — show that every visible field comes from a
   machine-readable boundary rather than browser-side heuristics.

## Do not do

- Do not bind the demo to `0.0.0.0`, a LAN address, or a public address.
- Do not put a real post-mortem, outage export, Slack thread, log, dashboard,
  secret, or customer identifier into the browser.
- Do not treat an advisory candidate, displayed representative, or candidate
  procedure as an execution instruction.
- Do not alter frozen evaluations or write-once reports while preparing a demo.
- Do not represent the demo as a hosted product, customer pilot, or production
  deployment.
