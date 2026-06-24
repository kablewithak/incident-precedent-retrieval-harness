# ADR-0006: Run Frozen Held-Out Evidence Once and Use a Strict Promotion Gate

- **Status:** Accepted
- **Date:** 2026-06-24

## Context

`heldout_tranche_01` is now frozen and hash-locked. The repository has a lexical
baseline plus a deterministic anti-anchoring policy that were shaped on calibration
fixtures. The next honest question is whether the *current configuration* survives
unseen cases without unsafe evidence or procedure behavior.

A normal unit-test pass cannot answer this. The report must preserve both pass and
block outcomes, and a block must be visible rather than treated as a flaky command
failure or silently overwritten by a later rerun.

## Decision

Create a dedicated held-out evaluation runner for the recorded configuration:

```text
keyword_bm25_style_v1 + deterministic_anti_anchoring_policy_v1 + top_k=5
```

The runner must:

1. verify the frozen manifest, file set, and SHA-256 hash of every held-out case
   before scoring;
2. load only the held-out split through `JsonDatasetRepository`;
3. avoid ranking provider-degraded cases as normal evidence input;
4. record ranked IDs, retained IDs, decision state, procedure output, missing-fact
   output, and explicit contract failures without including raw intake text;
5. write machine-readable and reviewer-readable artifacts exactly once;
6. return a normal process exit for a `blocked` gate because it is evidence, not a
   runner crash;
7. refuse to overwrite an existing held-out report.

The promotion gate is strict for this tranche. It requires exact decision-state,
procedure, missing-fact, abstention, and acceptable-precedent behavior; zero unsafe
precedents, unsafe procedures, and unexpected retained precedents are allowed.

## Consequences

### Easier

- A failure becomes a precise, reviewable configuration defect.
- Before/after claims can reference the original blocked report instead of memory.
- Evaluation integrity is checked before scoring rather than assumed.

### Harder

- The current configuration may block even when calibration appears perfect.
- A user cannot erase an initial result by rerunning over the same artifact path.
- Any future fix needs a separate intervention record and comparison report; it
  cannot rewrite frozen labels or discard the blocked baseline.

## Non-claims

This gate does not approve a configuration for production use. It evaluates only the
frozen 12-case tranche and does not prove semantic retrieval, live SIE extraction,
customer-data readiness, or production incident-response safety.
