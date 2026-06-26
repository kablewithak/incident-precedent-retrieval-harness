# ADR-0023: Bounded Dense Top-k SIE Score Reranking

- **Status:** Accepted for the Submission Completion Sprint
- **Date:** 2026-06-26
- **Decision:** Evaluate local SIE `score` only as a bounded reranker of the existing local dense top-k candidate set. Compare keyword, dense, and dense-plus-rerank on calibration only before policy integration or any promotion claim.

## Context

ADR-0022 established a local dense retrieval baseline from approved synthetic RelayOps incident cards. Its calibration evidence found a trade-off: dense retrieval did not improve exact-precedent MRR relative to the keyword baseline, while it lowered the false-operational-match proxy.

The project has separately validated the typed local SIE `score` adapter. The next question is therefore narrow and testable: can score reranking improve the ordering of dense candidates without expanding the candidate pool or bypassing anti-anchoring controls?

## Decision

The reranking path must:

1. receive only the dense retriever's already-ranked top-k candidates, with `1 <= k <= 10` and default `k=5`;
2. score only the controlled card representation that excludes direct IDs, procedures, source identifiers, incident-family labels, failure-mechanism labels, and evaluation labels;
3. preserve exactly the dense candidate identity set; a score response may reorder it but cannot add or remove candidates;
4. validate score-response profile identity, candidate identities, count, and contiguous one-based ranks before returning a result;
5. retain finite provider-native raw relevance values solely as ranking evidence, never as calibrated confidence;
6. preserve dense rank and cosine similarity beside rerank rank for traceability;
7. produce a calibration-only three-way report: keyword versus dense versus dense-plus-SIE-score;
8. fail closed when the dense index is stale or the score contract cannot be validated.

## Consequences

### Positive

- Superlinked SIE `score` enters the actual retrieval evaluation path under a narrow, inspectable contract.
- Reranking cannot turn into unbounded retrieval or a hidden selection policy.
- Regression evidence can identify whether reranking improves exact ranking, worsens safety proxies, or both.
- The existing anti-anchoring and representative-selection boundaries stay intact.

### Constraints

- The reranker cannot abstain, assign an operational decision state, select the authoritative precedent, or make procedures available.
- A candidate returned for an insufficient-precedent case remains a retrieval limitation until a separate abstention policy is evaluated.
- Calibration results remain unsuitable for held-out tuning or promotion.

## Non-claims

This ADR does not prove reranking quality, safe operational comparability, policy correctness, procedure eligibility, production latency, hosted-provider access, customer-data readiness, or production readiness.
