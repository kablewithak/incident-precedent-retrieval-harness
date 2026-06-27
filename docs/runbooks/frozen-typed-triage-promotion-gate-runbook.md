# Frozen Typed-Triage Promotion Gate Runbook

## Purpose

Run the current typed `TriageEvidencePacket` boundary against the frozen
`heldout_tranche_01` fixtures without changing retrieval, policy authority, fixture
labels, or the historical baseline evidence.

The gate compares:

```text
Baseline:
deterministic keyword top-5 -> AntiAnchoringDecisionPolicy

Candidate:
the same deterministic policy path
+ local-SIE dense advisory evidence
-> typed non-executing TriageEvidencePacket
```

The dense advisory is not allowed to change the policy result.

## Preconditions

- You are on the dedicated evaluation branch.
- `main` was clean before the branch was created.
- The unit suite passed before the change.
- `data/evals/heldout/HELDOUT_FREEZE_MANIFEST.json` has not been edited.
- The local dense index exists:

```text
evidence_vault/indexes/local-sie-dense-index-v1.json
```

- Local Docker SIE is running in a separate PowerShell window when real semantic
  advisory evidence is being measured.

Do not put API keys in commands, screenshots, reports, or committed files.

## Start local SIE in a separate PowerShell window

```powershell
docker start incident-sie
```

If the local container does not exist, stop. Do not substitute a managed endpoint or
invent provider behavior in this gate.

## Run deterministic verification first

```powershell
python -m pytest .\tests\unit\test_frozen_typed_triage_promotion_gate.py

python -m pytest .\tests\unit
```

## Run the frozen gate once

```powershell
python .\scripts\run_frozen_typed_triage_promotion_gate.py --repository-root .
```

Expected evidence paths:

```text
evidence_vault/reports/frozen-typed-triage-promotion-gate.json
docs/reports/frozen-typed-triage-promotion-gate.md
```

The command exits successfully after writing a report even when the decision is
`block`. A block is valid evaluation evidence.

## Read the decision correctly

### `promote_advisory_only`

The typed wrapper preserved policy authority, passed packet safety controls, and met
the recorded local latency gate.

It does not promote semantic retrieval into policy authority and does not authorize
procedures, remediation, production use, or customer data.

### `block`

One or more safety, policy, provider-degradation, baseline, or latency conditions
failed. Preserve the report. Do not modify held-out cases, labels, hashes, policy
rules, or retrieval parameters in response.

### `insufficient_evidence`

A required evidence category could not be measured. Preserve the report and resolve
the missing measurement through a separately documented implementation decision.

## Refusal conditions

The runner must refuse before scoring when:

- the held-out manifest is missing, invalid, or hash-mismatched;
- a held-out case is missing or an unexpected case is present;
- the local dense index is missing or incompatible;
- a report already exists at either output path;
- a typed triage contract cannot be satisfied.

## Privacy and safety controls

- The report stores IDs, states, metrics, latency, and failure labels only.
- It does not write raw incident summaries, raw provider payloads, secrets, or full
  procedure text.
- Every packet remains human-review material.
- Every packet must have `procedure_execution_authorized=false`.

## Do not do

- Do not rerun into the same output paths.
- Do not manually edit the report to improve the decision.
- Do not tune top-k, weights, policy behavior, semantic profiles, or procedure
  eligibility after seeing held-out results.
- Do not build the UI before this evidence is reviewed.
