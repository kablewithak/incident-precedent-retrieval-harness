# ADR-0018: Shadow-Evidence Freeze and Tranche 02 Constitution

- **Status:** Accepted
- **Date:** 2026-06-26
- **Decision scope:** Post-E1 evidence handling and fresh representative-selection evaluation design
- **Related decisions:** ADR-0012, ADR-0013, ADR-0014, ADR-0015, ADR-0016, ADR-0017

## Context

PR #23 introduced E1 admission-preserving shadow integration. The active `AntiAnchoringDecisionPolicy` remains authoritative for decision state, retained precedent IDs, missing-fact handling, conflict behavior, and procedure eligibility. The new shadow path retains compatibility-admitted cards by family and emits non-authoritative strict-dominance traces.

E1 established a safe observation seam. It did **not** activate representative selection and did **not** resolve the legacy first-compatible-card rank sensitivity documented in ADR-0016.

The project now needs two controls before any future integration or activation discussion:

1. freeze the E1 calibration evidence as historical baseline evidence; and
2. define a fresh Tranche 02 selection-evaluation process that is not reused from selector calibration, policy calibration, Tranche 01, or E1 bridge fixtures.

## Decision

### 1. Freeze the E1 evidence boundary

The following E1 outputs are historical calibration evidence after PR #23 and must not be edited in place:

- `docs/reports/policy-shadow-integration-calibration.md`
- `evidence_vault/reports/policy-shadow-integration-calibration.json`

Any future rerun produces a new report with a new run identifier, timestamp, commit reference, and report path. It must not overwrite or silently replace the historical PR #23 evidence artifact.

The PR #23 merged commit (`96fb53e`) is the reference implementation boundary for E1 evidence review. This commit is not an activation baseline and does not imply a production or customer-data claim.

### 2. Separate Tranche 02 from all prior evaluation assets

Tranche 02 is a fresh, frozen, representative-selection evaluation set. It must not reuse:

- selector calibration fixtures in `data/evals/selection_calibration`;
- policy calibration fixtures;
- E1 shadow-integration fixtures;
- Tranche 01 cases, labels, manifests, failure autopsies, direct-signal comparisons, or reports;
- candidate order, exact phrasing, expected labels, or scenario templates that were already exposed during calibration;
- hidden runtime fallbacks such as incident ID, lexical rank, lexical score, candidate order, procedure availability, or free-text cue matching.

Tranche 02 is scoped to the schema-derived representative-selection boundary. It must not become a general incident-policy benchmark.

### 3. Require authoring independence

The Tranche 02 case author or authoring session must not receive:

- selector calibration expected outcomes;
- E1 expected outcomes or trace outputs;
- Tranche 01 expected outcomes;
- the desired representative for any new Tranche 02 case;
- internal selector implementation details beyond the public contract in ADR-0012 and ADR-0013.

The author may use the published typed schema, admissible enum values, incident-card signatures, and the constitution in `docs/data/tranche-02-selection-evaluation-constitution.md`.

A reviewer records the authoring boundary, fixture source, and case acceptance or rejection rationale before the set is frozen.

### 4. Freeze before evaluation

Before the selector is run against Tranche 02:

1. assign stable case IDs;
2. create an input manifest with case IDs and input-file SHA-256 values;
3. create a separate expected-outcome manifest with case IDs, expected outcomes, and SHA-256 values;
4. record the selector commit under evaluation;
5. record the repository commit containing the frozen manifests;
6. prohibit mutation of either manifest during the evaluation run.

Expected outcomes must be kept out of runtime selector inputs and out of ordinary implementation context. The comparison harness may read them only at evaluation time.

### 5. Promotion gate is not yet open

Passing Tranche 02 alone does not activate representative selection.

Any future activation proposal requires, at minimum:

- E1 historical evidence review complete;
- Tranche 02 frozen before the evaluated selector change;
- zero unexplained Tranche 02 failures;
- same-input public `PolicyDecisionResult` invariance still passing;
- procedure and missing-fact behavior unchanged unless a separately approved policy redesign explicitly changes them;
- legacy rank sensitivity reported, not hidden;
- a separate ADR defining whether and how selector output may influence public policy output.

## Consequences

### Positive

- Preserves a clear boundary between calibration evidence, shadow evidence, and unseen evaluation evidence.
- Prevents the project from treating shadow-trace success as policy activation evidence.
- Makes future selection claims auditable through manifests, commit references, and frozen expected outcomes.
- Prevents Tranche 02 from becoming another visible tuning target.

### Costs

- Requires separate authoring and review steps.
- Delays any activation discussion until evidence is genuinely independent.
- Leaves the documented legacy rank-sensitivity behavior unchanged.

## Explicit non-claims

This ADR does not claim that representative selection is activated, production-ready, customer-data tested, or safe to influence procedure availability or decision states.
