# ADR-0029: Case-Scoped Procedure-Asymmetry Fixture Validator and Import

- **Status:** Accepted
- **Date:** 2026-06-27
- **Decision owners:** Incident Precedent Retrieval Harness
- **Related:** ADR-0019; Procedure-Asymmetry Adversarial Fixture V2 Acceptance Audit
- **Scope:** Accepted V2 proposal archive only; isolated test-only fixture import

## Context

The accepted V2 procedure-asymmetry proposal closes the missing adversarial category
identified during the Tranche 02 review:

```text
typed selection evidence strictly favors INC-014
procedure metadata, lower incident ID, and initial candidate order favor INC-013
```

The V2 acceptance audit verified archive integrity, controlled-card provenance, typed
schemas, and isolated strict-dominance oracle replay. It did not import the fixture
into the repository or authorize active-policy use.

The next boundary is deliberately narrow: validate the accepted archive before any
selector comparison, then copy its raw assets into an isolated evaluation directory.
The importer must not add controlled cards to the active incident corpus or allow
fixture governance or expected outcomes to reach selector inputs.

## Decision

Add a write-once, case-scoped fixture importer that:

1. reads one proposal ZIP under the exact
   `proposed_procedure_asymmetry_fixture/` root;
2. requires exactly 16 proposal files: 15 non-manifest assets plus `manifest.json`;
3. verifies the raw SHA-256 and byte count of every manifest-listed asset;
4. verifies the five declared aggregate hashes using one documented deterministic
   canonical formula;
5. validates exactly three runtime inputs, three expected outcomes, four controlled
   cards, and four derivation assertions;
6. requires the V2 PAV-001 / INC-013 assertion to declare
   `unsafe_procedure_ids` as a governed perturbation;
7. keeps runtime inputs and reviewer-controlled expected outcomes structurally
   separate;
8. validates controlled cards with `HistoricalIncidentCard` and runtime intakes with
   `RepresentativeSelectionIntake`;
9. preserves `controlled_card_set_id` at runtime: `PAV-001` and `PAV-002` may
   reuse incident IDs, but only the exact set named by a case may reach the selector;
10. accepts the V2 expected-outcome keys `expected_outcome_kind` and
   `expected_representative_ids` only in reviewer-controlled outcome assets;
11. runs the isolated strict-dominance selector only after all checks pass;
12. requires all three accepted V2 cases to select `INC-014`, with an exact
    PAF-T02-001 / PAF-T02-002 reverse-order pair;
13. copies raw proposal assets only to:

```text
data/evals/procedure_asymmetry_fixture/
```

12. writes one JSON and Markdown import receipt and refuses any overwrite.

## Isolation rules

The importer must not import or call:

```text
data/incidents/
data/procedures/
data/evals/heldout/
AntiAnchoringDecisionPolicy
keyword retrieval
dense retrieval
local SIE
provider configuration
```

The imported fixture remains a controlled evaluation asset. It is not active policy
input and is not a Tranche 02 freeze.

## Case-scoped card-set invariant

`PAV-001-procedure-asymmetric` and `PAV-002-procedure-neutral-control` deliberately
reuse `INC-013` and `INC-014` as identifiers. They are separate controlled variants,
not a global card corpus. The importer must therefore select cards by each runtime
case's `controlled_card_set_id`; flattening both sets into one incident-ID map would
erase the primary procedure-asymmetry evidence.

## Consequences

### Positive

- The accepted V2 proposal becomes reproducibly importable without leaking into the
  active corpus.
- Procedure metadata, candidate order, and incident identifier order are explicitly
  adversarially tested at the selector boundary.
- A malformed or incomplete archive fails before selector execution.
- The repository retains a machine-readable proof of exactly what was imported.

### Negative

- The importer may refuse an archive whose manifest uses an unsupported aggregate
  encoding. This is intentional: integrity semantics may not be guessed.
- The fixture does not solve EVAL-110 or activate the selector.
- The fixture does not freeze Tranche 02.

## Alternatives rejected

### Copy controlled cards into `data/incidents/`

Rejected. That would contaminate the active corpus and procedure path with test-only
metadata.

### Hand-copy the archive after an acceptance audit

Rejected. Manual copying bypasses raw-byte, aggregate, derivation, and separation
checks.

### Let expected outcomes drive selection

Rejected. Expected outcomes are reviewer-controlled oracles and must be withheld from
runtime selector inputs.

### Activate selection after the three isolated cases pass

Rejected. Three fixture cases are a regression boundary, not independent activation
evidence.

## Non-claims

This ADR does not activate representative selection, change retrieval or procedure
behavior, freeze Tranche 02, authorize any procedure, validate customer data, or
establish production readiness.
