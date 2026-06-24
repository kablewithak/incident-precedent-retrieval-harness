# Incident Precedent Retrieval Harness — Handover 002

## Boundary

Post-intervention comparison boundary after ADR-0008. This handover is generated with the write-once comparison evidence; it is not a plan-only checkpoint.

## Repository checkpoint

- Comparison configuration revision: `1eaea7493b427ff873ddf71e5f00166f7ea74405`
- Frozen scope: `heldout_tranche_01`
- Held-out manifest SHA-256: `5fbb4372582db66a96e9718394776a3dcbde8f6c7447cefc0c1e5beaf2f63535`
- Baseline evidence SHA-256: `4518cc80b4e6864bbf1d19fc6e76047787fffa09d9bc58c3f080d23f5aa65a96`
- Comparison gate: **BLOCKED**
- Comparison conclusion: **IMPROVED BUT BLOCKED**

## What changed

ADR-0008 changed only connection-pool family admission: active database connections are contextual and cannot override two contradicted direct pool signals.
- Improved held-out cases: EVAL-102
- Regressed held-out cases: none
- Remaining blocked cases: EVAL-110

## Current evidence status

- Decision-state accuracy: `1.0`
- Case-contract pass rate: `0.9167`
- Acceptable-precedent coverage: `0.8571`
- Unsafe precedents retained: `0`
- Unexpected procedures surfaced: `0`
- Unexpected retained precedents: `1`

## Architecture status

```text
structured synthetic intake facts
  -> BM25-style local keyword retrieval
  -> deterministic anti-anchoring policy
  -> frozen held-out comparison gate
```

Local SIE encode and score capability were demonstrated earlier, but live extraction remains blocked. No SIE call, embedding, dense retrieval, or reranking is in the active evaluation path.

## Remaining blocker

The remaining held-out issue is within-family representative selection for connection-pool evidence. The current policy retains the first compatible candidate per family, coupling the selected evidence card to lexical rank. Do not patch this using incident-ID order, held-out labels, or raw lexical rank.

## Next safe slice

Define a reviewed within-family evidence-selection contract, create calibration-only diagnostics for that contract, and preserve the frozen held-out baseline and comparison artifacts unchanged until the calibration design is accepted.

## Non-claims

- This checkpoint does not prove semantic retrieval, reranking, extraction quality, customer-data readiness, or production safety.
- A blocked comparison remains diagnostic evidence, not a reason to relax the gate or modify frozen labels.
