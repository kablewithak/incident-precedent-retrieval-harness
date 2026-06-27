# ADR-0026: Frozen End-to-End Typed-Triage Promotion Gate

- **Status:** Accepted
- **Date:** 2026-06-27
- **Decision owners:** Incident Precedent Retrieval Harness
- **Scope:** `heldout_tranche_01` only

## Context

PR #33 introduced a typed, non-executing `TriageEvidencePacket` boundary.

The packet combines:

```text
deterministic keyword top-5
-> AntiAnchoringDecisionPolicy
-> policy decision authority

local-SIE dense top-5
-> SemanticAdvisory
-> human-review context only
```

The semantic advisory must not alter:

- decision state;
- retained precedent IDs;
- missing critical facts;
- candidate procedure eligibility;
- procedure execution authorization.

Calibration established packet-control behavior. It did not establish the current typed-triage path against the frozen holdout. The held-out tranche contains 12 cases and is guarded by per-file SHA-256 hashes in:

```text
data/evals/heldout/HELDOUT_FREEZE_MANIFEST.json
```

The existing historical keyword-plus-policy held-out report is immutable baseline evidence. It must not be overwritten or rewritten to flatter the typed triage path.

## Decision

Add a new write-once frozen end-to-end gate that:

1. Verifies the held-out manifest and every case hash before scoring.
2. Computes the current deterministic keyword-plus-policy baseline in memory.
3. Runs the same frozen cases through the typed triage boundary.
4. Compares typed-triage policy output directly with baseline policy output.
5. Verifies the final packet invariants:
   - semantic advisory is advisory-only;
   - all packets keep `procedure_execution_authorized=false`;
   - the declared provider-degraded case fails closed;
   - provider-available cases do not silently degrade;
   - no semantic result changes policy authority.
6. Records p50 and p95 end-to-end typed-triage latency.
7. Writes one JSON and one Markdown evidence artifact, refusing to overwrite either.
8. Emits one decision:

```text
promote_advisory_only
block
insufficient_evidence
```

## Gate rules

### Blocking conditions

The gate returns `block` when any of the following is true:

- the underlying frozen keyword-plus-policy baseline is blocked;
- typed-triage state behavior differs from frozen expectations;
- policy output differs from the baseline;
- policy case contracts remain violated;
- a provider-available case degrades unexpectedly;
- the provider-degraded case does not fail closed;
- any packet authorizes procedure execution;
- observed p95 end-to-end latency exceeds the provisional 1,500 ms budget.

### Insufficient-evidence conditions

The gate returns `insufficient_evidence` when a necessary evidence category cannot be measured, including:

- no provider-degraded case exists;
- no provider-available semantic latency sample exists.

### Promotion meaning

`promote_advisory_only` means only:

> The typed wrapper preserved deterministic policy authority, met the frozen safety controls, and stayed within the stated local latency gate.

It does not mean:

- dense retrieval became policy authority;
- semantic retrieval is superior to keyword retrieval;
- any model diagnosed a root cause;
- any procedure is executable;
- production readiness, customer-data readiness, or incident-response safety was established.

## Consequences

### Positive

- The system has a single reproducible proof boundary for the current typed triage path.
- A semantic advisory cannot acquire authority through presentation or accidental orchestration coupling.
- A blocked result becomes a clear engineering artifact rather than a hidden failure.
- Historical reports remain immutable and comparable.

### Negative

- The local CPU SIE environment may block the gate on latency.
- The existing deterministic baseline may continue to block the typed path.
- This is a 12-case tranche, not the planned final 36-case evaluation.

These are acceptable outcomes. They are more honest and more useful than changing frozen cases or silently loosening the gate.

## Alternatives rejected

### Promote the typed path after calibration only

Rejected. Calibration confirms local control behavior, not frozen-split safety.

### Let semantic rank feed the policy to improve apparent relevance

Rejected. The project has evidence of rank/order sensitivity. Changing policy authority requires a separate ADR, fixed evaluation design, and new held-out gate.

### Reuse or overwrite the historical held-out report

Rejected. Historical evidence must remain write-once. The typed path needs a separately named artifact.

### Add a UI before the gate

Rejected. Presentation does not close the remaining safety and promotion-evidence gap.

## Verification

The implementation must include deterministic unit tests for:

- manifest verification before scoring;
- policy authority parity;
- explicit provider-degraded fail-closed behavior;
- unexpected semantic degradation;
- zero procedure execution authorization;
- write-once report behavior.

The real local-SIE run is intentional and separate from normal CI:

```powershell
python .\scripts\run_frozen_typed_triage_promotion_gate.py --repository-root .
```

## Non-claims

This ADR defines a local, synthetic-data evaluation control. It does not create a production promotion mechanism, a customer-data approval, a deployment readiness assessment, or an operational remediation authority.
