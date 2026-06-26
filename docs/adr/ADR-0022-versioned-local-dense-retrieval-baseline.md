# ADR-0022: Versioned Local Dense Retrieval Baseline

- **Status:** Accepted for the Submission Completion Sprint
- **Date:** 2026-06-26
- **Decision:** Build a local, versioned dense index from approved RelayOps incident cards using the validated local SIE `encode` adapter. Evaluate cosine retrieval against the existing keyword baseline on calibration only before adding SIE `score` reranking or changing policy behavior.

## Context

The project now has validated local Docker SIE application-adapter evidence for:

- `encode` with `sentence-transformers/all-MiniLM-L6-v2`;
- `score` with `cross-encoder/ms-marco-MiniLM-L-6-v2`.

The existing active retrieval baseline is deterministic keyword ranking. It is not sufficient to establish whether semantic retrieval improves retrieval quality or increases unsafe lookalikes. A dense-retrieval baseline is therefore required before reranking, triage orchestration, or any promotion claim.

## Decision

The dense baseline must:

1. create a stable, explicit text representation for each approved historical incident card;
2. exclude incident IDs, procedures, source identifiers, explicit incident-family labels, failure-mechanism labels, and evaluation labels from that representation;
3. call the existing provider-neutral `SemanticInferenceClient.encode_incident_texts` boundary;
4. serialize vectors with a local index manifest that binds the artifact to a corpus fingerprint, representation version, profile, model, and vector dimension;
5. fail closed if the current corpus, representation hashes, entry identities, or vector dimensions do not match the index manifest;
6. use deterministic cosine similarity and incident-ID ordering only as a numerical tie-breaker;
7. run calibration only, while explicitly excluding held-out cases;
8. report dense and keyword metrics side by side without claiming safety promotion.

## Consequences

### Positive

- The project now tests a real SIE embedding path in the retrieval workflow.
- Generated local vectors are bound to the exact approved incident-card representations used to create them.
- A stale or mismatched local index cannot be silently used.
- The dense baseline can be compared with keyword retrieval before complexity is added.

### Constraints

- The index is a rebuildable local artifact, not a source-of-truth data asset and not a committed provider payload.
- Calibration results cannot tune the held-out tranche.
- Dense retrieval does not assign decision states, select a single authoritative precedent, authorize procedures, or establish safe operational applicability.
- SIE `score` remains unused until this baseline has saved comparison evidence.

## Non-claims

This ADR does not prove retrieval quality, safe comparability, reranking benefit, production latency, hosted-provider access, customer-data readiness, or production readiness.
