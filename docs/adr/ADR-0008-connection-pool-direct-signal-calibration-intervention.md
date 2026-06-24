# ADR-0008: Connection-Pool Direct-Signal Calibration Intervention

## Status

Accepted for calibration-only validation.

## Context

The immutable Held-Out Tranche 01 baseline was blocked on `EVAL-102` because
`connection_pool_exhaustion` remained admissible when both direct pool signals
were contradicted:

- `database_connection_pool_utilization`;
- `database_connection_acquire_latency`.

The only remaining positive observation was `active_database_connections`.
That is contextual evidence, not a direct indicator of client-pool exhaustion.
Retaining the family manufactured a false conflict alongside the correctly
retained migration-lock precedent and suppressed the expected procedure.

The frozen held-out case, its labels, the baseline artifact, and the promotion
gate are not changed by this decision.

## Decision

For `connection_pool_exhaustion` compatibility:

1. A confirmed direct pool signal admits the family.
2. When both direct pool signals are unknown, confirmed active connections may
   preserve the family as incomplete evidence; the normal missing-facts gate
   still blocks a procedure.
3. When both direct pool signals are contradicted, active connections must not
   admit the family.

Direct pool signals are limited to:

- `database_connection_pool_utilization`;
- `database_connection_acquire_latency`.

This is an admission rule, not a ranking or within-family selection rule. It
does not address the separate `EVAL-110` representative-selection ambiguity.

## Validation plan

Run only the calibration suite and record a separate report pair:

```powershell
python -m pytest .\tests\unit
python .\scripts\run_connection_pool_direct_signal_calibration.py --repository-root . --top-k 5
```

The calibration report must preserve:

- decision-state accuracy `1.0`;
- zero false-operational matches;
- zero unexpected procedures;
- conflict behavior for `EVAL-011`;
- missing-fact behavior for `EVAL-010`.

A held-out rerun is prohibited in this ADR. It becomes eligible only after this
calibration report is reviewed and committed.

## Consequences

The policy gains a narrower distinction between direct and contextual evidence.
It should eliminate the autopsied false conflict without weakening the existing
incomplete-evidence path.

## Non-claims

A calibration pass does not prove that the frozen held-out gate will pass. This
ADR does not add semantic retrieval, reranking, extraction, a live provider
adapter, or a within-family representative-selection contract.
