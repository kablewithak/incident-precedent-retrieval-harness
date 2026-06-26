# Local SIE Submission Profile Validation Runbook

## Purpose

Confirm the exact local Docker SIE `encode` and `score` profiles used by the
structured-first submission path after adapter changes or local environment changes.

## Preconditions

- Work from the repository root with the Python virtual environment active.
- Start local Docker SIE in a separate terminal:

```powershell
 docker run --rm -p 8080:8080 ghcr.io/superlinked/sie-server:latest-cpu-default
```

- Use only synthetic RelayOps text. Do not include real incident records, secrets,
  API keys, customer identifiers, or internal URLs.

## Command

```powershell
python .\scripts\validate_local_sie_submission_operations.py `
  --output .\evidence_vault\reports\local-sie-submission-operations.json
```

## Pass condition

The command reports `status: passed`, with:

- three validated vectors of one consistent dimension;
- two reranked candidates;
- `INC-SIE-001` ranked ahead of `INC-SIE-002` for the synthetic discriminative pair.

## Block condition

If the command returns a typed failure, retain only the safe JSON output. Do not
copy raw provider exceptions, provider payloads, logs, model paths, or credentials
into repository artifacts.

## Non-claims

A passing command proves only adapter/profile contract compatibility for local SIE
encode and score. It does not prove retrieval quality, anti-anchoring safety,
warm latency, hosted-provider access, customer-data readiness, or production
readiness.
