# ADR-0031: Future-Held-Out Tranche 02 Governed Freeze Boundary

## Status

Accepted implementation boundary. This ADR authorizes a validator/importer only
for the V2 proposal accepted by the Tranche 02 future-held-out V2 acceptance audit.
It does not authorize a selector comparison, selector activation, active-policy
integration, procedure execution, or a production claim.

## Decision

Create a fail-closed, write-once import/freeze boundary that accepts only an
externally supplied V2 archive when all of the following pass before any repository
copy:

1. The committed V2 acceptance audit declares
   `accepted_for_governed_future_tranche_freeze`.
2. The supplied archive filename and SHA-256 exactly match that audit.
3. Archive root, exact 28-file topology, manifest inventory, asset hashes, byte
   counts, and four aggregate hashes match the accepted proposal contract.
4. The twelve runtime inputs and twelve evaluator-only outcomes remain structurally
   separate.
5. Valid cases validate against `RepresentativeSelectionIntake` and reference one
   profiled `connection_pool_exhaustion` candidate family.
6. `SEL-T02-FH-011` rejects duplicate signal families before selector execution.
7. `SEL-T02-FH-012` remains a genuinely mixed-family candidate pool and rejects
   before selector execution.
8. `SEL-T02-FH-001` and `SEL-T02-FH-002` remain exact candidate-order reversals
   with the same evaluator oracle.

Only validated runtime inputs and evaluator-only outcomes are copied to:

```text
data/evals/heldout/tranche_02_future_heldout/
```

The importer generates `TRANCHE_02_FUTURE_HELDOUT_FREEZE_MANIFEST.json` inside
that location and one JSON/Markdown receipt pair. Existing target or receipt paths
cause refusal rather than overwrite.

## Deliberate non-imports

The freeze module must not import or load:

- `StrictDominanceRepresentativeSelector`;
- `AntiAnchoringDecisionPolicy`;
- retrieval implementations or indexes;
- procedures;
- existing held-out Tranche 01 assets;
- procedure-asymmetry fixture assets;
- source incident-card corpus files.

The source-corpus grounding check at this boundary is the acceptance-audit-bound
archive declaration. Fresh source-card and selector behavior validation belongs to
the later, predeclared comparison gate, after this freeze is immutable.

## Freeze result

A passing result means only:

```text
frozen_test_only
```

It does not mean the selector passed future-held-out comparison. The next slice may
load this immutable frozen location, verify its generated freeze manifest, and run
one predeclared comparison. No selector or policy change is authorized before that
later evidence exists.

## Commercial and submission proof

This shows an evaluator can distinguish calibration from unseen evaluation, control
an external test asset with hashes, and make later model-adjacent behavior contingent
on a reviewable freeze boundary rather than on informal test success.
