# ADR-0024: Bounded Hybrid Retrieval Experiment

- Status: Accepted for calibration-only evaluation
- Date: 2026-06-27
- Decision owner: Incident Precedent Retrieval Harness

## Context

The calibration baseline shows a measured trade-off:

- keyword retrieval has stronger exact-precedent ranking on the current small calibration corpus;
- local-SIE dense retrieval has a lower false-operational-match proxy;
- SIE score reranking of dense top-k executed successfully but did not change either metric.

A hybrid candidate generator is therefore evaluated as an experiment, not assumed to be superior.

## Decision

Build a deterministic, bounded candidate union:

1. take keyword top-5 in lexical rank order;
2. append dense top-5 candidates absent from the keyword set in cosine-rank order;
3. deduplicate by incident ID;
4. cap the score pool at ten candidates;
5. use SIE score to reorder only that exact union;
6. evaluate ranking metrics at the common top-5 cut, even when the score pool contains more candidates.

The hybrid seed order is provenance only. It is not a final ranking and does not express a policy preference.

## Hard boundaries

This slice must not:

- load held-out fixtures;
- change active decision policy, anti-anchoring policy, representative selection, or procedure visibility;
- allow SIE score to inject candidates outside the hybrid union;
- interpret raw cross-encoder relevance as probability or confidence;
- claim promotion, production readiness, customer-data validation, or retrieval-quality superiority.

## Acceptance criteria

- Candidate provenance records keyword and/or dense origin and original rank.
- The union is deterministic, deduplicated, and contains at most ten candidates.
- SIE score response identities exactly match the union.
- Score ranks are complete and contiguous.
- A four-way calibration report compares keyword, dense, dense-plus-rerank, and hybrid-plus-rerank.
- The report explicitly records non-improvement or regressions.
- Generated local index artifacts remain rebuildable and are not committed.

## Consequences

The experiment may improve exact-match retrieval, safety proxy, both, neither, or regress either. No retrieval path is promoted from this report alone. Later anti-anchoring and held-out evaluation remain required before triage integration.
