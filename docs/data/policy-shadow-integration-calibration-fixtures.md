# Policy Shadow Integration Calibration Fixtures

## Purpose

`data/evals/shadow_integration/` contains E1 bridge fixtures. Each fixture binds
one existing policy calibration case to separately supplied typed selection
input, then declares only the expected shadow trace.

The fixture never changes the policy case, its expected decision state, its
retrieval query, or its procedure expectation.

## Boundary

```text
policy_case_id
+ optional family-specific RepresentativeSelectionIntake
-> same active PolicyDecisionResult
+ expected non-authoritative family selection trace
```

The selection intake is not inferred from `EvalCase.input_summary`. It must be
explicitly authored and validated independently.

## Fixture Contract

Each file contains:

```text
shadow_case_id
split = shadow_integration_calibration
policy_case_id
selection_intake_bindings
expected_traces
failure_label_intent
acceptance_reason
```

An expected trace records only safe structured fields:

```text
incident_family
admitted_candidate_ids
selection_intake_present
selector_invoked
selection_state
representative_incident_ids
unavailable_reason
```

No raw narrative, retriever score, matched term, provider payload, procedure
body, evaluation label, or held-out content belongs in a trace.

## Current Cases

| Fixture | Policy case | Purpose |
|---|---|---|
| SHADOW-CAL-001 | EVAL-004 | Provider-degraded bypass |
| SHADOW-CAL-002 | EVAL-003 | Insufficient-precedent bypass |
| SHADOW-CAL-003 | EVAL-001 | Multiple admitted cards without typed selection input |
| SHADOW-CAL-004 | EVAL-009 | Connection-pool pool unavailable without typed input |
| SHADOW-CAL-005 | EVAL-009 | Typed single representative trace |
| SHADOW-CAL-006 | EVAL-010 | Typed explicit within-family tie |
| SHADOW-CAL-007 | EVAL-011 | Cross-family conflict and procedure withholding preserved |
| SHADOW-CAL-008 | EVAL-005 | Unsupported-family unavailability |

## Acceptance Rules

- Public policy output must match the active policy exactly for the same ranked
  input.
- Only compatibility-admitted cards may enter a trace.
- A trace may not create a sixth evidence decision state.
- A trace may not make a procedure eligible.
- Explicit ties remain ties.
- Missing typed input, unsupported family, and missing schema signature remain
  unavailable. They do not fall back to lexical rank or incident ID.
- The runner must not load held-out cases, freeze manifests, baseline comparison
  artifacts, or promotion reports.
