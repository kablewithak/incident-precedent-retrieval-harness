# ADR-0027: EVAL-110 Representative-Selection Autopsy

- **Status:** Accepted
- **Date:** 2026-06-27
- **Decision owners:** Incident Precedent Retrieval Harness
- **Scope:** Frozen `EVAL-110` evidence only

## Context

The frozen typed-triage promotion gate blocked without a typed-boundary safety failure.

Recorded facts:

```text
EVAL-110 expected state: evidence_found_with_conflict
baseline state:          evidence_found_with_conflict
typed-triage state:      evidence_found_with_conflict
policy parity:           true
procedure execution:     false
```

The remaining failure is representative selection:

```text
Expected acceptable precedents: INC-003, INC-009
Retained precedents:            INC-012, INC-003
Failure labels:
- required_acceptable_precedent_missing
- unexpected_retained_precedent
```

`INC-012` and `INC-009` are both connection-pool-exhaustion cards. The active policy retains the first compatible candidate per family. It does not have an active, reviewed within-family representative-selection contract.

## Decision

Add a write-once, deterministic EVAL-110 autopsy that:

1. Verifies `HELDOUT_FREEZE_MANIFEST.json` before reading evidence.
2. Reads the committed keyword-policy held-out report and typed-triage promotion report.
3. Checks that typed triage preserved policy authority and did not authorize procedure execution.
4. Records ranked, retained, expected, omitted, and unexpected incident IDs.
5. Maps those IDs to typed card evidence and selection signatures.
6. Emits one diagnostic verdict only:

```text
policy_selection_defect
expected_contract_defect
undocumented_conflict_rule
insufficient_evidence
```

7. Refuses to overwrite the resulting JSON and Markdown evidence pair.

## Active boundaries

The autopsy must not:

- rerun keyword retrieval, policy scoring, or local SIE;
- modify held-out cases, labels, hashes, candidate ordering, or freeze metadata;
- modify active policy rules, procedures, or semantic-advisory authority;
- treat a calibration-only selector as active policy authority;
- claim that an identified future remediation will pass the frozen tranche.

## Verdict meaning

`undocumented_conflict_rule` means the frozen contract and recorded policy state agree that two incident families should remain visible, but the current first-compatible behavior lacks a reviewed rule for selecting one connection-pool representative over another.

It is not permission to choose by incident ID, rank, score, or held-out expectation. A future proposal must define a typed selection contract, measure it on calibration data, and only then seek separate activation approval.

## Consequences

### Positive

- The unresolved block becomes a traceable engineering decision rather than a vague failure.
- The project separates policy-state correctness from within-family representative-selection correctness.
- Future remediation starts with a narrow, evidence-backed problem statement.

### Negative

- The active promotion result remains `block`.
- This report does not produce a remediation or a new promotion result.
- A later selector activation would require a separate ADR, calibration evidence, and a new frozen evaluation boundary.

## Verification

The implementation must prove:

- the current EVAL-110 evidence chain yields `undocumented_conflict_rule`;
- typed-triage retained IDs match the frozen baseline IDs;
- no procedure execution authorization is accepted;
- report writing is write-once.

## Non-claims

This is a local, synthetic-data, evidence-reading autopsy. It does not demonstrate semantic retrieval quality, customer-data readiness, production safety, or operational remediation authority.
