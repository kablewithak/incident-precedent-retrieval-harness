# Controlled Incident Ingestion Runbook

## Purpose

Inspect a bounded JSONL export of historical incident summaries before any
record is eligible for human canonicalization or semantic indexing.

This is an offline, review-only process. It is not a live connector, document
crawler, or direct corpus writer.

## Intended team workflow

```text
Resolved incident or approved postmortem
→ curator creates a sanitized structured export
→ inspection validates shape, uniqueness, and sensitive-content controls
→ human reviewer canonicalizes approved records
→ separate indexing step embeds only approved canonical cards
```

The on-call engineer does not run this during a live incident.

## Allowed input

Each JSONL line represents one candidate historical incident record. The export
must contain only approved, sanitized content. Required fields include:

- a stable import record ID;
- source system and source record ID;
- data classification;
- title and sanitized summary;
- occurrence date;
- service, component, and change context;
- short symptom labels;
- a source reference suitable for reviewer lookup.

The export must not contain secrets, API keys, passwords, bearer tokens, email
addresses, IP addresses, raw logs, copied postmortems, or customer identifiers.

## Demo command

From the repository root with `(.venv)` active:

```powershell
python .\scripts\inspect_incident_import_batch.py `
  --input .\data\imports\relayops-demo-incident-export.jsonl `
  --batch-id relayops-demo-v1
```

A clean batch returns exit code `0`. A rejected batch returns exit code `2`.

The command prints only a JSON-safe inspection report. It never prints the raw
summary or a matched sensitive value.

## What this step verifies

- JSONL syntax and strict typed record shape;
- unique import IDs and source-record identities within the batch;
- bounded textual fields;
- no duplicate symptom labels;
- detection of common secret, credential, email, and IPv4 patterns;
- a SHA-256 digest of the input bytes;
- a review-only result with no repository data writes.

## What this step does not do

- It does not call Superlinked SIE.
- It does not create a `HistoricalIncidentCard`.
- It does not infer final incident family, safe procedure IDs, or unsafe procedure IDs.
- It does not modify `data/incidents/`, `data/procedures/`, calibration, held-out,
  reports, or evidence-vault artifacts.
- It does not approve customer data for use.

## Failure handling

A batch is not ready for review when any line has invalid JSON, fails schema
validation, repeats an identity, or contains a sensitive-content finding.

Correct the source export, create a new batch file, and rerun inspection. Do
not patch an inspection result or suppress a finding.
