# ADR-0005: Freeze a Held-Out Evaluation Tranche Before Further Retrieval Tuning

- **Status:** Accepted
- **Date:** 2026-06-24

## Context

The project has a deterministic keyword baseline and a calibration-only anti-anchoring policy. Calibration results are useful for implementation feedback, but continued use of the same cases to tune ranking or policy would make apparent improvement untrustworthy.

The current corpus contains three authored families and twelve calibration cases. The project needs an untouched, reproducible boundary before introducing dense retrieval, reranking, candidate thresholds, or policy changes.

## Decision

Freeze `heldout_tranche_01` with twelve cases under `data/evals/heldout`.

- Use IDs `EVAL-101` through `EVAL-112` to keep the held-out range visibly separate from calibration IDs.
- Include standard positive, false-operational-match, no-precedent, conflict, and provider-degraded cases.
- Record per-file SHA-256 hashes in `HELDOUT_FREEZE_MANIFEST.json`.
- Add a repository loader that validates held-out files separately and rejects calibration/held-out split mixing.
- Do not run this tranche as an optimization loop. It becomes an evaluation boundary for future reports.

## Consequences

### Easier

- Detect regression when retrieval or policy changes.
- Demonstrate that safety claims are not based only on tuned calibration cases.
- Preserve a defensible before/after evaluation boundary.

### Harder

- Implementation changes cannot be justified by changing expected labels after seeing a failure.
- A legitimate data defect requires documented manifest revision and full reruns.

## Non-claims

This decision does not freeze the final 36-case holdout, prove production safety, or establish a promotion gate. It creates the first protected tranche needed to make the next experiments meaningful.
