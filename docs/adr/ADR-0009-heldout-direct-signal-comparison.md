# ADR-0009: Held-Out Comparison After Direct-Signal Calibration Intervention

## Status

Accepted for one write-once comparison run.

## Context

ADR-0008 introduced a calibration-only change to connection-pool family admission.
The calibration report passed its declared safety checks:

- decision-state accuracy `1.0`;
- zero surfaced false-operational matches;
- zero surfaced unsafe procedures;
- preserved `EVAL-010` missing-fact behavior;
- preserved `EVAL-011` conflict behavior.

The immutable Held-Out Tranche 01 baseline remains preserved at:

```text
evidence_vault/reports/heldout-tranche-01-keyword-policy.json
```

That baseline was blocked on `EVAL-102` and `EVAL-110`. The purpose of the
comparison is not to tune the frozen tranche. It is to determine whether the
single predeclared ADR-0008 change removes the EVAL-102 false conflict without
regressing any other frozen-case contract.

## Decision

Run one comparison configuration using the existing:

```text
keyword_bm25_style_v1
+ deterministic_anti_anchoring_policy_v1 with ADR-0008 direct-signal admission
+ top_k=5
```

The comparison must:

1. read the committed baseline artifact rather than recreate it;
2. verify the frozen held-out manifest before scoring;
3. use the same 12 frozen case IDs, lexical retriever, top-k setting, and gate
   thresholds as the baseline;
4. write a new, separate evidence pair without overwriting baseline or autopsy
   artifacts;
5. generate Handover 002 from the actual comparison result;
6. refuse a second write to the same comparison paths.

The comparison is eligible only because the ADR-0008 calibration evidence was
reviewed and committed. It is not a general authorization to iterate on held-out
cases.

## Expected decision boundary

The comparison can reach one of four conclusions:

- `promoted`: all strict gate contracts pass with no regression;
- `improved_but_blocked`: one or more baseline failures improve, but at least one
  strict gate block remains;
- `blocked_without_clear_improvement`: the strict gate remains blocked with no
  recorded case-contract improvement;
- `regressed`: any previously passing held-out case loses its contract.

For the current known failure shape, `EVAL-102` is expected to improve if the
calibration rule transfers correctly. `EVAL-110` is intentionally out of scope;
it requires a separately designed within-family evidence-selection contract.

## Validation plan

```powershell
python -m pytest .\tests\unit
```

Commit comparison code with a clean working tree. Then run once:

```powershell
python .\scripts\run_heldout_direct_signal_comparison.py --repository-root . --top-k 5
```

Review:

- current gate status;
- per-case deltas;
- regression count;
- remaining blocked cases;
- generated Handover 002.

## Consequences

A successful EVAL-102 improvement is evidence that the direct-versus-contextual
signal distinction transfers beyond calibration. It does not resolve EVAL-110,
prove semantic retrieval, or allow a relaxed promotion gate.

A remaining blocked result must preserve the evidence and lead to a new
calibration-only design step. Frozen cases and their labels remain unchanged.

## Non-claims

This ADR does not add dense retrieval, reranking, free-text extraction, a live
SIE adapter, customer-data evaluation, or production incident-response safety.
