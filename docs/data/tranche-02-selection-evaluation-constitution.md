# Tranche 02 Representative-Selection Evaluation Constitution

## Purpose

Tranche 02 is a fresh, frozen evaluation set for the **schema-derived representative-selection boundary**. Its purpose is to test whether the strict-dominance selector behaves correctly on new typed selection inputs and candidate pools that were not used to create, tune, or inspect the existing calibration fixtures.

It is not a general RAG benchmark, incident-resolution benchmark, policy-state benchmark, or procedure-recommendation benchmark.

## Boundary under evaluation

The evaluated component receives only:

- a typed `RepresentativeSelectionIntake`;
- a candidate pool of already compatibility-admitted incident cards from one family;
- schema-derived `selection_signature` values attached to those cards.

The component must not use:

- retrieval rank or score;
- candidate input order;
- incident ID as a tie-breaker;
- procedure metadata or procedure availability;
- evaluation labels;
- free-text symptom matching;
- Tranche 01 or prior calibration assets.

## Required case fields

Each Tranche 02 case must contain these fields:

```json
{
  "case_id": "SEL-T02-001",
  "contract_version": "tranche-02-selection-v1",
  "selection_intake": {},
  "candidate_incident_ids": ["INC-..."],
  "candidate_pool_family": "connection_pool_exhaustion",
  "case_design_tags": ["..."],
  "input_provenance": {
    "authoring_batch": "...",
    "authored_by_role": "independent_case_author",
    "source_type": "synthetic_schema_derived",
    "created_at_utc": "..."
  }
}
```

The input fixture must not contain `expected_outcome`, `expected_incident_id`, evaluator commentary, calibration labels, or a free-text explanation that names the desired winner.

Expected outcomes belong in a separate reviewer-controlled manifest.

## Expected-outcome manifest contract

The reviewer-controlled manifest must contain:

```json
{
  "case_id": "SEL-T02-001",
  "expected_outcome_kind": "single_representative",
  "expected_representative_ids": ["INC-..."],
  "expected_non_dominated_ids": ["INC-..."],
  "expected_reason_codes": ["..."],
  "review_rationale": "..."
}
```

Allowed `expected_outcome_kind` values are:

- `single_representative`
- `explicit_tie`
- `invalid_input`

The expected manifest is unavailable to runtime selector code and is not included in implementation bundles before the run is complete.

## Required evaluation coverage

The frozen set must include at least one accepted, non-duplicate case for each category below:

1. **Exact service and exact component dominance**: one candidate strictly dominates using service and component alignment.
2. **Context-only discriminator**: candidates are otherwise equivalent, but exact change-context alignment creates a winner.
3. **Unknown context safety**: missing or unknown context does not invent alignment.
4. **Distinct signal-family dominance**: one candidate has strictly stronger supported signal-family alignment.
5. **Correlated-source deduplication**: multiple source references for one signal family count as one family, not multiple votes.
6. **Contradicted-signal penalty**: a candidate with contradicted signal evidence cannot win merely through another weak match.
7. **Explicit non-dominated tie**: more than one candidate remains non-dominated.
8. **No-evidence tie**: no candidate receives supported positive dominance evidence.
9. **Input-order reversal**: reversing the candidate list leaves selector output unchanged.
10. **Invalid signature boundary**: a candidate missing a required selection signature fails closed.
11. **Cross-family rejection**: candidate pool from a non-target family is rejected rather than coerced.
12. **No hidden legacy tie-break**: a case where lexical rank, incident ID order, and procedure availability would prefer a different card than the strict-dominance result.

The case author must reject trivial duplicates, cases with ambiguous expected outcomes, and cases whose outcome requires undocumented selector behavior.

## Case quality requirements

A Tranche 02 case is acceptable only when all of the following are true:

- the scenario is expressible through the typed contract;
- expected behavior is determined by the published contract, not a preferred incident ID;
- it does not duplicate a prior calibration case by structure or wording;
- its candidate pool is valid for the target family;
- it includes an explicit acceptance rationale;
- it does not depend on procedures, retrieval order, or free-text inference;
- its expected outcome can be checked mechanically.

## Freeze protocol

1. Author inputs in a separate authoring workspace.
2. Review and accept or reject each proposed case with a written reason.
3. Assign final stable IDs only after acceptance.
4. Produce `tranche_02_input_manifest.json` containing input hashes.
5. Produce `tranche_02_expected_manifest.json` containing expected-outcome hashes.
6. Record authoring boundary, repository commit, and reviewer identity or role.
7. Freeze both manifests before the evaluated selector run.
8. Run the comparison harness without modifying cases or labels.
9. Record a failure taxonomy for every mismatch.

## Failure taxonomy

Every Tranche 02 mismatch must receive one primary label:

- `contract_interpretation_error`
- `schema_signature_error`
- `intake_validation_error`
- `dominance_relation_error`
- `tie_handling_error`
- `order_dependence_error`
- `forbidden_signal_leakage`
- `fixture_ambiguity`
- `harness_or_manifest_error`

No mismatch may be silently relabeled as an expected tie or removed after seeing selector output.

## Reporting requirements

The Tranche 02 report must include:

- selector commit under evaluation;
- frozen input-manifest hash;
- frozen expected-manifest hash;
- total accepted cases;
- pass/fail counts;
- outcome-kind confusion summary;
- order-invariance results;
- failure taxonomy counts;
- representative traces with sensitive content excluded;
- explicit statement that Tranche 02 is evaluation evidence, not activation evidence.

## Non-claims

A passing Tranche 02 result does not by itself authorize changes to `AntiAnchoringDecisionPolicy`, retained precedent IDs, missing facts, procedures, decision states, or any production workflow.
