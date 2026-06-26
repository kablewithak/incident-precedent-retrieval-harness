# Local Dense + SIE Score Rerank Calibration Runbook

## Purpose

Build the rebuildable local dense index, then compare three retrieval paths on calibration fixtures only:

1. deterministic keyword retrieval;
2. local-SIE dense cosine retrieval;
3. local-SIE `score` reranking of the fixed dense top-k candidate set.

This runbook does not load held-out cases, alter anti-anchoring policy, select a final representative, surface procedures, or make a promotion decision.

## Preconditions

- Worktree is clean before the live run.
- Docker SIE is running locally.
- `python .\scripts\validate_local_sie_submission_operations.py` previously passed in the active local environment.
- `data\incidents\` contains only approved synthetic RelayOps incident cards.
- Do not place private incident records, credentials, raw logs, customer data, or raw provider payloads in the repository.

## 1. Rebuild the local dense index

```powershell
python .\scripts\build_local_dense_index.py --repository-root .
```

Expected metadata-only result includes `status: passed`, `corpus_incident_count: 12`, `embedding_profile_id: local-sie-encode-v1`, and `vector_dimension: 384`.

The generated index is rebuildable:

```text
evidence_vault\indexes\local-sie-dense-index-v1.json
```

Do not commit it.

## 2. Run bounded dense-top-k score reranking

```powershell
python .\scripts\run_dense_rerank_calibration.py `
  --repository-root . `
  --top-k 5
```

The command scores only the five candidates returned by dense retrieval for each calibration query. It must not fetch a new corpus candidate, use held-out fixtures, or display raw provider payloads.

It writes portable evidence paths:

```text
evidence_vault/reports/local-sie-dense-rerank-calibration.json
docs/reports/local-sie-dense-rerank-calibration.md
```

## 3. Inspect the report

Verify that the report:

- names all three paths: keyword, dense, and dense-plus-SIE-score;
- shows the dense top-k limit and the fixed-candidate-set boundary;
- retains the corpus fingerprint, encode profile, score profile, and vector dimension;
- compares correct-precedent MRR, incident-family Recall@5, and false-operational-match rate;
- states whether reranking improved or worsened each relevant calibration metric;
- says that no path is promoted;
- makes no claim about procedures, decision states, customer data, hosted APIs, or production readiness;
- uses only repository-relative evidence paths.

## 4. Cleanup before commit

Keep the generated JSON and Markdown report artifacts. Remove the rebuildable dense index:

```powershell
Remove-Item .\evidence_vault\indexes\local-sie-dense-index-v1.json -ErrorAction SilentlyContinue
```

## Failure handling

| Result | Required response |
|---|---|
| `dense_index_invalid` | Rebuild from the current approved corpus. Do not bypass fingerprint validation. |
| Provider failure | Preserve only the safe JSON failure envelope. Do not expose raw SDK exceptions or payloads. |
| `rerank_contract_invalid` | Treat score response mapping as untrusted. Do not manually reorder candidates. |
| Rerank improves MRR but worsens false-operational-match rate | Record the trade-off. Do not promote or integrate into policy. |
| Rerank worsens both measures | Preserve the evidence and do not tune held-out labels. |
