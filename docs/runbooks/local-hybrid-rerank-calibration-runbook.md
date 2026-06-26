# Local Hybrid + SIE Score Rerank Calibration Runbook

## Purpose

Evaluate a bounded candidate union:

```text
keyword top-5
+ local-SIE dense top-5
-> deterministic deduplicated union (maximum 10)
-> local SIE score rerank
-> calibration-only four-way report
```

This is an experiment. It does not activate policy or procedures.

## Preconditions

- Python environment is active.
- Local Docker SIE is running and has previously passed the typed encode/score validation.
- The approved synthetic RelayOps corpus is unchanged.
- No held-out fixtures are loaded.
- The local dense index has been rebuilt for the current corpus fingerprint.

## Build the local dense index

```powershell
python .\scripts\build_local_dense_index.py `
  --repository-root .
```

The local index is rebuildable and must not be committed.

## Run the hybrid calibration

```powershell
python .\scripts\run_hybrid_rerank_calibration.py `
  --repository-root . `
  --keyword-top-k 5 `
  --dense-top-k 5
```

Expected evidence paths:

```text
evidence_vault/reports/local-sie-hybrid-rerank-calibration.json
docs/reports/local-sie-hybrid-rerank-calibration.md
```

## Review gate

Check:

- candidate count never exceeds ten;
- ranking metrics use the common top-5 evaluation cut;
- SIE score candidate identities equal the bounded union;
- exact-precedent MRR across all four paths;
- false-operational-match rate across all four paths;
- insufficient-precedent cases remain labelled as lacking an abstention policy;
- no report language promotes a path.

## Cleanup

After report review and before commit:

```powershell
Remove-Item `
  ".\evidence_vault\indexes\local-sie-dense-index-v1.json" `
  -ErrorAction SilentlyContinue
```

Commit only reviewer-facing reports and source changes. Do not commit the generated local index.
