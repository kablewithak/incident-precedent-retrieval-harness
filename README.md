# Related Incident Evidence

**Technical subtitle:** An evaluated retrieval reliability harness for historical
incident precedent.

## What this repository isolates

This repository tests one narrow safety question:

> When is a historical incident comparable enough to surface as evidence to an
> on-call engineer, and when must the system abstain because the similarity could
> cause unsafe operational anchoring?

It is not an incident-management platform, root-cause engine, remediation agent,
alerting product, or generic RAG chatbot.

## Current maturity

- **Production-shaped design:** in progress
- **Local Docker SIE server health/readiness:** verified
- **Typed provider-neutral protocol and deterministic fake provider:** included
- **Local SIE `encode`:** verified once with a 384-dimension response
- **Local SIE `score`:** verified once with two ranked candidates
- **Local SIE `extract`:** blocked for the tested CPU/model path because the model
  did not become ready within the server's model-load budget
- **Dataset contract:** implemented
- **Batch 01 controlled variants:** four validated queue-backlog incident cards,
  one bounded candidate investigation procedure, and four calibration cases
- **Batch 01 source grounding:** source-linked and pending explicit human
  verification before any record may be promoted to `source_grounded`
- **Retrieval baseline, held-out evaluation, and promotion gate:** not yet
  implemented

The current evidence is intentionally mixed, not silently rounded up to a pass.
See:

- `docs/reports/phase-0-provider-capability-spike.md`
- `evidence_vault/reports/phase-0-local-sie-capability-spike.json`
- `docs/handover/Incident_Precedent_Retrieval_Harness_Handover_001_Phase_0_Provider_Spike_Blocked.md`
- `docs/data/batch-01-source-review.md`

A healthy SIE server proves only that the local process can receive traffic. It
does not prove every configured model can perform a useful inference operation.

## Local setup

From the repository root in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest .\tests\unit
```

Copy `.env.example` to `.env` only when local configuration is required. Do not
add real API keys to the repository, fixtures, screenshots, logs, or reports.

## Local SIE server

The initial provider mode is a local CPU Docker server at
`http://localhost:8080`.

```powershell
docker start -ai incident-sie
```

In another PowerShell tab:

```powershell
python .\scripts\check_sie_health.py
```

The health script tests only `/healthz` and `/readyz`. It does not make an
inference-ready claim.

## Dataset posture

The repository uses a fictional RelayOps archive. Batch 01 records are
**controlled variants** built from a source-review ledger; they deliberately do
not claim `source_grounded` status until a human reviewer confirms the source,
transformation note, and absence of copied narrative. This keeps the provenance
contract honest while still giving the retrieval baseline a validated starter
corpus.

## Architecture boundary

```text
Domain workflow
  -> provider-neutral SemanticInferenceClient protocol
      -> deterministic fake client for normal tests
      -> future Superlinked SIE adapter after the required operation contracts are verified
```

Only the future adapter may know Superlinked SDK classes, HTTP response shapes, or
provider-specific exceptions. Domain policy, retrieval, evaluation, reporting,
CLI, and normal tests must remain provider-neutral.

## Decision states planned for the product

- `evidence_found`
- `evidence_found_with_conflict`
- `missing_critical_facts`
- `insufficient_precedent`
- `provider_degraded`

The final state will be assigned by deterministic application policy, never
directly by a model response.
