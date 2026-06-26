# Tranche 02 Blind-Authoring Acceptance Audit

## Audit identity

| Field | Value |
|---|---|
| Audit status | `CONDITIONAL_REJECTION_NOT_FROZEN` |
| Reviewer role | `AI reliability acceptance auditor` |
| Review method | Source-grounded structural, manifest, contract, duplicate, and selector-compatibility audit |
| Proposal archive | `tranche-02-blind-authoring-proposal.zip` |
| Proposal archive SHA-256 | `de11fb74758f0efe7776e22ec01608a0129209aa1a66fe0bcc0afc65b48e068c` |
| Proposal manifest SHA-256 | `1c41bae6138b4cca4c26c3b258b0ebc9ca42809329987c4d34118ccb36df1edf` |
| Proposal input-manifest SHA-256 | `a5a8785778e2fef1713306bf6c85ec6f8b7558388dcdfb643bdafde58d1e0d8b` |
| Proposal expected-outcome-manifest SHA-256 | `c859834697d013fedaa24c8d63ad6e1569d53610d8027afb0806ebc56f24dae3` |
| Repository baseline reviewed | `c94a6e5` |
| Scope | Schema-derived representative-selection evaluation only |
| Activation authority | None |

## Verdict

The proposal is **not authorized for Tranche 02 freeze or repository import as a complete evaluation set**.

Its authoring separation, asset integrity, typed-intake validity, source-card grounding, and most outcome oracles are sound. However, two proposed cases duplicate existing selector calibration coverage, and the constitution's required full no-hidden-legacy-tie-break case remains unavailable from the supplied corpus.

This is a **quality-preserving rejection**, not a selector failure and not a claim about active policy behavior.

## Verified evidence

| Check | Result | Evidence |
|---|---|---|
| Package structure | Pass | Required `inputs/`, `expected_outcomes/`, manifests, ledger, rejected ideas, and apply manifest are present. |
| Manifest inventory | Pass | `31/31` listed files had matching SHA-256 and byte counts. |
| Input / expected asset separation | Pass | Runtime-input files do not contain expected representatives, labels, or evaluator commentary. |
| Typed intake validation | Pass | `13/13` `selection_intake` objects validate against `RepresentativeSelectionIntake`. |
| Source-card validation | Pass | `12/12` supplied incident cards validate against `HistoricalIncidentCard`. |
| Valid-case selector compatibility | Pass | `11/11` executable valid proposals match the current strict-dominance state and representative IDs. |
| Invalid-input intent | Conditional | `SEL-T02-011` and `SEL-T02-012` require a dedicated Tranche 02 fixture validator; the current selector alone does not consume `candidate_pool_family`. |
| Pair order-invariance | Pass | `SEL-T02-009` and `SEL-T02-010` return the same `single_representative` outcome and representative ID under reversed candidate order. |
| Blind-authoring attestation | Accepted as attested | The ledger and proposal manifest declare the excluded materials unavailable. This review cannot independently prove a negative beyond that recorded boundary. |

## Case disposition

| Case ID | Disposition | Reason |
|---|---|---|
| `SEL-T02-001` | Reject | Exact structural duplicate of existing `SEL-CAL-007` and `SEL-CAL-008`: same candidate set, typed intake, and expected outcome, differing only in candidate sequence. It is not a new diagnostic case. |
| `SEL-T02-002` | Conditionally retain | Source-grounded context-only discriminator. Retain only in a future reviewed manifest. |
| `SEL-T02-003` | Conditionally retain | Diagnostic unknown-context tie with a contract-determined oracle. |
| `SEL-T02-004` | Conditionally retain | Diagnostic distinct-signal-family strict-dominance case. |
| `SEL-T02-005` | Conditionally retain | Diagnostic correlated-source-family deduplication case. |
| `SEL-T02-006` | Conditionally retain | Diagnostic contradicted-signal penalty case. |
| `SEL-T02-007` | Conditionally retain | Diagnostic non-dominated tie case. |
| `SEL-T02-008` | Conditionally retain | Diagnostic no-evidence tie case. |
| `SEL-T02-009` | Conditionally retain | Required reference half of the order-invariance pair. |
| `SEL-T02-010` | Conditionally retain | Required reversed-order half of the order-invariance pair. |
| `SEL-T02-011` | Conditionally retain | Valid fail-closed boundary case after a deterministic Tranche 02 fixture validator defines aggregate invalid-input reason codes. |
| `SEL-T02-012` | Conditionally retain | Valid cross-family rejection intent after a deterministic Tranche 02 fixture validator validates `candidate_pool_family` before selector execution. |
| `SEL-T02-013` | Reject | Near-duplicate of existing `SEL-CAL-009`: same typed intake and expected winner with a reduced candidate pool. It also does not satisfy the constitution's required procedure-availability asymmetry. |

## Constitution disposition

| Required category | Status after audit | Basis |
|---|---|---|
| 1–11 | Provisionally covered | Accepted or conditionally retained cases provide diagnostic coverage once a Tranche 02 fixture validator exists. |
| 12: no hidden legacy tie-break | **Not covered** | The supplied profiled connection-pool cards have the same procedure posture. A grounded case where procedure availability prefers a different candidate cannot be authored from this corpus. `SEL-T02-013` is insufficient and rejected. |

## Required controls before any future freeze

1. Do not modify this blind-authoring proposal in place.
2. Do not import the proposal assets into `data/evals/tranche_02`.
3. Define a governed, test-only procedure-asymmetry fixture boundary under ADR-0019.
4. Use a fresh blinded authoring session to author that narrow adversarial fixture set.
5. Create a dedicated Tranche 02 fixture contract and validator that:
   - validates `candidate_pool_family`;
   - rejects unsupported families and card-family mismatches before selection;
   - handles intentional invalid-input cases without invoking selection;
   - compares valid cases only on outcome kind and representative/non-dominated IDs;
   - treats `expected_reason_codes` as evaluator diagnostics unless an explicit machine-readable reason-code contract is later introduced.
6. After the missing category is resolved, create a **new reviewed package and new manifests** with final stable IDs. The proposal's current `SEL-T02-*` labels remain provisional and must not be treated as final freeze IDs.

## Explicit non-claims

- No Tranche 02 selector pass rate exists.
- No selector activation is authorized.
- No active policy, retained precedent, missing-fact, procedure, or decision-state behavior is evaluated or changed.
- No customer-data, production, or deployment claim is authorized.
