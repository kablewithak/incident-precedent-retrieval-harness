# Dataset Constitution — Related Incident Evidence

## Purpose

This repository uses a **source-grounded synthetic** incident archive for
repeatable retrieval and anti-anchoring evaluation. It is not a collection of
real customer incidents, production logs, or operational instructions.

The fictional environment is **RelayOps**, a growth-stage B2B SaaS topology with
a public API, background workers, queues, PostgreSQL, Redis/cache, feature flags,
webhooks, and third-party provider dependencies.

## Fixed scope

| Asset | Target | Current status |
|---|---:|---|
| Historical incident cards | 32 | 12 controlled variants authored; source review pending |
| Incident families | 8 | frozen |
| Candidate investigation procedures | 8–10 | 3 bounded procedures authored |
| Calibration cases | 12 | 12 cases authored; calibration only |
| Held-out cases | 36 | not started; must remain separate from calibration |

The eight incident families are frozen in
`src/incident_precedent_harness/domain/incident_enums.py`.

## Source posture

A public source may inform mechanisms, timelines, terminology, and uncertainty.
It must not be copied wholesale into the corpus unless licensing explicitly
permits the use and the required notice is retained.

Every source-grounded record requires:

- a `source_record_id`;
- source name and URL;
- known publication date where available;
- usage mode;
- transformation note;
- explicit `human_verified: true`.

Controlled variants and synthetic no-precedent records must not pretend to be
records of a public source.

## Directory contract

```text
data/
  incidents/          # fictional historical incident cards
  procedures/         # candidate investigation procedures
  evals/
    calibration/      # tuning only
    heldout/          # frozen final evaluation only
```

No record may move from `heldout/` to `calibration/` to make a pipeline look
better. Any holdout correction requires a documented data defect and a full
evaluation rerun.

## Hard integrity gates

1. Every incident maps to exactly one incident family.
2. Every source-grounded incident validates provenance.
3. Every procedure names applicability, non-applicability, verification
   prerequisites, safe investigation steps, and out-of-scope actions.
4. Every eval case names an expected decision state, acceptable precedent IDs,
   unsafe precedent IDs, expected missing facts where relevant, and an
   acceptance reason.
5. Calibration policy fixtures may carry `observed_facts` with explicit
   `confirmed`, `contradicted`, or `unknown` state. They simulate structured
   intake fields and must not be inferred from expected labels at runtime.
6. No corpus/eval asset may contain private incident records, raw production
   logs, internal hostnames, customer identifiers, credentials, tokens, signed
   URLs, or copied public articles.

## Non-claims

The corpus is a controlled evaluation asset. It does not represent actual
RelayOps history, production incident recall, safe remediation, or customer-data
validation.

## Held-out tranche 01

The repository now contains `heldout_tranche_01`: 12 frozen cases with IDs `EVAL-101` through `EVAL-112`. The tranche is hash-locked by `data/evals/heldout/HELDOUT_FREEZE_MANIFEST.json`. It is distinct from the 12 calibration cases and cannot be used for tuning. See `docs/data/heldout-evaluation-constitution.md` for its case groups, change policy, and non-claims.
