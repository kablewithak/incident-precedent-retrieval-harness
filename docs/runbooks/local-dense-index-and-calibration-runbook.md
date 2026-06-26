# Local Dense Index and Calibration Runbook

## Purpose

Build a rebuildable local dense index from approved synthetic RelayOps incident cards, then compare local-SIE cosine retrieval with the deterministic keyword baseline on calibration only.

This is an evaluation step. It does not load held-out cases, modify policy behavior, surface procedures, or make a promotion decision.

## Preconditions

- Worktree is clean before beginning the live run.
- Local Docker SIE is running.
- `python .\scripts\validate_local_sie_submission_operations.py` has previously passed for the active local environment.
- `data\incidents\` contains only approved repository incident cards.
- Do not place private incident records, production logs, credentials, raw Slack exports, or customer data in the repository.

## 1. Build the local dense index

```powershell
python .\scripts\build_local_dense_index.py --repository-root .
```

Expected output is metadata only:

```text
status: passed
corpus_incident_count: 12
embedding_profile_id: local-sie-encode-v1
vector_dimension: 384
```

The script writes a rebuildable local artifact at:

```text
evidence_vault\indexes\local-sie-dense-index-v1.json
```

Do not commit that index artifact. It is regenerated from approved cards and the configured local model.

If the script returns `blocked`, preserve the safe JSON output and do not manually create an index file.

## 2. Run calibration-only dense retrieval

```powershell
python .\scripts\run_dense_retrieval_calibration.py --repository-root . --top-k 5
```

The script writes repository-relative evidence paths:

```text
docs/reports/local-sie-dense-retrieval-calibration.md
evidence_vault/reports/local-sie-dense-retrieval-calibration.json
```

The report compares keyword and dense retrieval on the calibration split. It records MRR, incident-family Recall@5, false-operational-match rate, and local cosine ranking latency. Its calibration-interpretation section must preserve trade-offs rather than claim that dense retrieval won by default.

## 3. Inspect the evidence

Check:

- the report says `calibration only`;
- the corpus fingerprint and vector dimension are present;
- a keyword comparison is included;
- the calibration-interpretation section states whether exact-precedent ranking and false-operational-match rate moved in opposite directions;
- any false operational matches remain visible;
- no result claims safety promotion or procedure authorization;
- no committed report or console summary exposes an absolute local path.

A denser retrieval result is not an improvement unless the later safety policy and held-out evaluation also support it.

## 4. Local cleanup

The local dense index is rebuildable. After a successful report is saved, remove the generated index before staging Git changes:

```powershell
Remove-Item .\evidence_vault\indexes\local-sie-dense-index-v1.json -ErrorAction SilentlyContinue
```

Do not delete the committed report artifacts.

## Failure handling

| Result | Required response |
|---|---|
| `dense_index_invalid` | Rebuild the index from the current approved corpus. Do not bypass fingerprint validation. |
| `provider_unavailable`, `provider_timeout`, `retry_exhausted` | Treat dense retrieval as unavailable. Preserve only safe failure metadata. |
| Dense MRR improves but unsafe top-1 rate worsens | Record the comparison. Do not add reranking or claim improvement without a safety review. |
| Dense fails to beat keyword | Preserve the evidence. Do not tune held-out cases or labels. |
