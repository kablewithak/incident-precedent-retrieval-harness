# Evidence Map

## How to read this map

Each artifact below answers a bounded question. A passing outcome in one row must not be expanded into a claim that belongs to another row.

```text
fixture / evidence boundary
-> exact behavior under test
-> recorded result
-> remaining gate or non-claim
```

## 1. Typed triage policy boundary

| Item | Evidence |
|---|---|
| Question | Does the typed `TriageEvidencePacket` preserve the frozen keyword-plus-policy baseline without granting authority to semantic advisory evidence? |
| Evidence | [Frozen typed-triage promotion gate](../reports/frozen-typed-triage-promotion-gate.md) |
| Frozen corpus | Tranche 01, 12 cases |
| Recorded result | `BLOCK` |
| Positive evidence | Expected-state accuracy `1.0`; policy parity `1.0`; provider-degraded safe resolution `1.0`; procedure authorization `0` |
| Blocking evidence | `EVAL-110`: expected acceptable precedent `INC-009` was not retained; `INC-012` was retained unexpectedly |
| Correct conclusion | The typed wrapper preserved the existing policy result; it did not promote a blocked baseline |
| Non-claim | This does not validate production readiness, customer-data safety, or semantic retrieval authority |

## 2. EVAL-110 diagnostic autopsy

| Item | Evidence |
|---|---|
| Question | What caused the frozen Tranche 01 representative divergence? |
| Evidence | [EVAL-110 representative-selection autopsy](../reports/eval-110-representative-selection-autopsy.md) |
| Recorded verdict | `UNDOCUMENTED_CONFLICT_RULE` |
| Finding | The policy maintained the correct conflict state but retained the first compatible connection-pool candidate according to retrieval order, omitting the expected same-family representative |
| Correct consequence | Do not alter frozen inputs, labels, ranks, IDs, or policy just to make the fixture pass |
| Non-claim | The diagnosis itself does not prove that any selector remediation is safe or promotable |

## 3. Procedure-asymmetry adversarial control

| Item | Evidence |
|---|---|
| Question | Can a candidate’s procedure availability or metadata improperly change strict-dominance representative selection? |
| Evidence | [Procedure-asymmetry fixture comparison](../reports/procedure-asymmetry-fixture-comparison.md) |
| Scope | Isolated test-only selector fixture; no active corpus, retrieval, held-out set, procedures, or policy loaded |
| Recorded result | `COMPARISON_PASSED_ACTIVATION_BLOCKED` |
| Positive evidence | 3/3 exact outcomes; candidate-order invariant; output stable under procedure asymmetry |
| Correct conclusion | The isolated selector control resisted procedure-driven selection drift |
| Non-claim | This does not prove active-policy, end-to-end, or production safety |

## 4. Future-held-out selector comparison

| Item | Evidence |
|---|---|
| Question | Does strict-dominance selection satisfy independently authored frozen future-held-out contracts? |
| Evidence | [Tranche 02 future-held-out comparison](../reports/tranche-02-future-heldout-comparison.md) |
| Scope | 10 valid selector cases and 2 pre-selector rejection controls |
| Recorded result | `comparison_passed_activation_blocked` |
| Positive evidence | Contract pass rate `1.00`; order invariance `true`; source-card hashes verified |
| Correct conclusion | The standalone selector passed its frozen future-held-out contract |
| Non-claim | This does not establish policy integration, procedure withholding, retrieval safety, degraded behavior, or production readiness |

## 5. Conditional display-only integration

| Item | Evidence |
|---|---|
| Question | Can the evaluated selector be attached to the typed triage boundary without altering policy authority? |
| Evidence | [Conditional representative-selection activation readiness](../reports/conditional-representative-selection-activation-readiness.md) |
| Scope | Fixed local synthetic integration controls |
| Recorded result | `implementation_validated_activation_blocked` |
| Positive evidence | Policy unchanged in all three controls; validates single winner, explicit tie, and selection not requested |
| Correct conclusion | Conditional refinement can be returned separately from policy decision when callers supply valid selection intake |
| Non-claim | This does not improve retrieval, diagnose incidents, make procedures executable, or resolve the frozen Tranche 01 block |

## 6. Local demo boundary

| Item | Evidence |
|---|---|
| Question | Can a reviewer inspect governed behavior through a local browser surface without exposing a public application or moving authority into UI code? |
| Evidence | [Local submission demo runbook](../runbooks/local-submission-demo-runbook.md), [shadcn presentation runbook](../runbooks/shadcn-local-demo-development-runbook.md), ADR-0034, ADR-0035 |
| Scope | Loopback-only Python transport plus React/Vite local UI |
| Demonstrated behavior | Safe evidence, conflict, insufficient-precedent abstention, and provider-degraded fail-closed scenarios |
| Correct conclusion | The UI is a local renderer of the typed packet |
| Non-claim | A demo is not a deployment, customer pilot, or production system |

## Evidence-to-claim matrix

| Claim | Supported? | Evidence boundary |
|---|---:|---|
| Typed packet preserves frozen policy state | Yes | Frozen typed-triage gate |
| Baseline path is promotable | No | Frozen typed-triage gate is blocked |
| Selector is stable against procedure asymmetry in isolated control | Yes | Procedure-asymmetry comparison |
| Selector satisfies frozen future-held-out standalone contract | Yes | Tranche 02 comparison |
| Selector is actively allowed to replace policy authority | No | Conditional integration report remains activation-blocked |
| Selection can refine display in the local typed boundary under narrow conditions | Yes | Conditional integration controls |
| UI creates no policy authority | Yes, by architecture and local test boundary | ADR-0034/0035 and demo runbooks |
| Procedures are executable | No | Contract is always false |
| Production readiness | No | Out of scope and unproven |
| Customer-data safety / real incident performance | No | Synthetic local corpus only |

## Machine-readable evidence

The corresponding immutable machine-readable reports live under:

```text
evidence_vault/reports/
```

They are paired with the markdown reports in `docs/reports/`. Treat the readable report as the reviewer narrative and the JSON receipt as the exact recorded artifact.
