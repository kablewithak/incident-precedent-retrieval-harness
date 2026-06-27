# Typed triage evidence packet runbook

## Purpose

Run the calibration-only typed triage boundary with local-SIE dense advisory retrieval. This is a local synthetic-data check. It is not a production incident workflow.

## Preconditions

- Run from the repository root with the project virtual environment active.
- Local Docker SIE is running at the configured `SIE_BASE_URL`.
- The approved incident-card corpus is unchanged.
- A fresh local dense index exists and matches the approved corpus fingerprint.

## Commands

```powershell
python .\scripts\build_local_dense_index.py `
  --repository-root .

python .\scripts\run_typed_triage_calibration.py `
  --repository-root .
```

## Expected passed shape

```text
triage_kind: typed_triage_calibration
status: passed
decision_state_match_rate: 1.0
procedure_execution_authorized_count: 0
evidence_json: evidence_vault/reports/typed-triage-calibration.json
evidence_markdown: docs/reports/typed-triage-calibration.md
```

## Failure handling

- `dense_index_invalid`: rebuild the local dense index from the approved corpus. Do not hand-edit the index.
- `triage_input_rejected`: remove secret, credential, email, or IP content upstream; do not bypass the guard or log the rejected text.
- `triage_contract_invalid`: stop and inspect the typed contract mismatch before changing policy behavior.
- `status: blocked`: do not treat the packet boundary as a product-path milestone.

## Scope controls

- The report reads calibration cases only and does not load held-out assets.
- The local dense index is rebuildable and must not be committed.
- Candidate procedure IDs are human-review material only. The packet does not authorize execution.
- Dense semantic evidence is advisory. It cannot alter the deterministic policy result in this slice.
