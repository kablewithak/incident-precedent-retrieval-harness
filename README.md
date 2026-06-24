# Related Incident Evidence

**Technical subtitle:** An evaluated retrieval reliability harness for historical
incident precedent.

## What this repository isolates

This repository tests one narrow safety question:

> When is a historical incident comparable enough to surface as evidence to an
> on-call engineer, and when must the system abstain because the similarity could
> cause unsafe operational anchoring?

It is not an incident-management platform, root-cause engine, remediation agent,
alerting product, or generic RAG chatbot.

## Current maturity

- **Production-shaped design:** in progress
- **Local Docker SIE server health/readiness:** verified
- **Typed provider-neutral protocol and deterministic fake provider:** included
- **Local SIE `encode`:** verified once with a 384-dimension response
- **Local SIE `score`:** verified once with two ranked candidates
- **Local SIE `extract`:** blocked for the tested CPU/model path because the model
  did not become ready within the server's model-load budget
- **Dataset contract:** implemented
- **Batch 01 controlled variants:** four queue-backlog cards, one bounded
  investigation procedure, and four calibration cases
- **Batch 02 controlled variants:** four migration-lock cards, one bounded
  investigation procedure, and four calibration cases including reciprocal
  false-operational-match tests
- **Batch 03 controlled variants:** four connection-pool cards, one bounded
  investigation procedure, and four calibration cases including a no-preference
  conflict case
- **Source grounding:** source-linked and pending explicit human verification
  before any record may be promoted to `source_grounded`
- **Keyword retrieval baseline:** calibration-only evidence recorded
- **Deterministic anti-anchoring policy:** calibration-only prototype recorded
- **Held-out evaluation and promotion gate:** implemented; the generated report is the source of truth for the current keyword-plus-policy configuration
- **Held-out baseline:** recorded as blocked at PR #9; its failure autopsy is a separate trace-only evidence step before any intervention
- **Calibration intervention:** ADR-0008 narrows connection-pool admission so contextual active-connection evidence cannot override two contradicted direct pool signals; held-out cases remain frozen and unrerun until calibration evidence is committed

The current evidence is intentionally mixed, not silently rounded up to a pass.
See:

- `docs/reports/phase-0-provider-capability-spike.md`
- `evidence_vault/reports/phase-0-local-sie-capability-spike.json`
- `docs/handover/Incident_Precedent_Retrieval_Harness_Handover_001_Phase_0_Provider_Spike_Blocked.md`
- `docs/data/batch-01-source-review.md`
- `docs/data/batch-02-source-review.md`
- `docs/data/batch-03-source-review.md`

A healthy SIE server proves only that the local process can receive traffic. It
does not prove every configured model can perform a useful inference operation.

## Local setup

From the repository root in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest .\tests\unit
```

Copy `.env.example` to `.env` only when local configuration is required. Do not
add real API keys to the repository, fixtures, screenshots, logs, or reports.

## Local SIE server

The initial provider mode is a local CPU Docker server at
`http://localhost:8080`.

```powershell
docker start -ai incident-sie
```

In another PowerShell tab:

```powershell
python .\scripts\check_sie_health.py
```

The health script tests only `/healthz` and `/readyz`. It does not make an
inference-ready claim.

## Dataset posture

The repository uses a fictional RelayOps archive. Batches 01 through 03 are
**controlled variants** built from source-review ledgers; they deliberately do
not claim `source_grounded` status until a human reviewer confirms each source,
transformation note, and absence of copied narrative.

Batch 02 introduces a hard anti-anchoring boundary: a queue backlog after a
change can be operationally incompatible with a queue-consumer failure when
verified database migration lock waits and healthy consumers point to a
database-side throughput constraint.

Batch 03 introduces a separate conflict boundary: deployment-linked consumer
capacity loss and database client-pool acquisition pressure can both look
plausible. The expected state is conflict, not a preferred procedure, until the
decisive facts are verified.

## Architecture boundary

```text
Domain workflow
  -> provider-neutral SemanticInferenceClient protocol
      -> deterministic fake client for normal tests
      -> future Superlinked SIE adapter after the required operation contracts are verified
```

Only the future adapter may know Superlinked SDK classes, HTTP response shapes, or
provider-specific exceptions. Domain policy, retrieval, evaluation, reporting,
CLI, and normal tests must remain provider-neutral.

## Decision states planned for the product

- `evidence_found`
- `evidence_found_with_conflict`
- `missing_critical_facts`
- `insufficient_precedent`
- `provider_degraded`

The final state will be assigned by deterministic application policy, never
directly by a model response.

## Keyword baseline: calibration evidence

The first retrieval baseline is now a deterministic in-memory BM25-style lexical
ranker over the 12 authored controlled-variant cards. It is a **calibration-only
baseline**, not a promotable configuration.

The generated calibration report records an important negative result: it reaches
high retrieval rank on the current authoring cases while still returning unsafe
or irrelevant top-ranked candidates for two abstention cases. That is why MRR
cannot be used as a promotion signal by itself.

Run it from the repository root:

```powershell
python .\scripts\run_keyword_baseline.py --repository-root . --top-k 5
```

It writes only generated, reviewable evidence:

- `docs/reports/keyword-baseline-calibration.md`
- `evidence_vault/reports/keyword-baseline-calibration.json`

The report deliberately does not evaluate held-out cases, assign a final decision
state, surface procedures, or make a semantic/provider-latency claim.

## Deterministic anti-anchoring policy: calibration evidence

The keyword baseline demonstrates why ranking cannot determine safe incident
support by itself. The policy prototype consumes ranked candidates plus explicit
structured intake observations (`confirmed`, `contradicted`, or `unknown`). It
then assigns a final decision state deterministically.

The current calibration report records zero surfaced unsafe precedents and zero
unsafe procedures across the 12 authoring cases. This is **calibration evidence**,
not a held-out safety claim.

Run it from the repository root:

```powershell
python .\scripts\run_anti_anchoring_policy.py --repository-root . --top-k 5
```

It writes:

- `docs/reports/anti-anchoring-policy-calibration.md`
- `evidence_vault/reports/anti-anchoring-policy-calibration.json`

The policy supports only the three authored families. It does not extract facts
from free text, call SIE, diagnose a current incident, or authorize a procedure.

## Held-out evaluation boundary

`heldout_tranche_01` is frozen under `data/evals/heldout` and is intentionally separate from calibration. It contains 12 diagnostic cases across positive, false-operational-match, no-precedent, conflict, and provider-degraded behavior. The tranche is hash-locked by `HELDOUT_FREEZE_MANIFEST.json` and must not be used to tune retrieval, policy, procedure eligibility, or prompts.

The current tranche is not the final planned 36-case holdout. The write-once evaluator verifies the manifest before scoring and records a strict pass-or-block promotion result without modifying retrieval or policy behavior.

Run it only after the working tree is clean and unit tests pass:

```powershell
python .\scripts\run_heldout_evaluation.py --repository-root . --top-k 5
```

It writes one committed evidence pair:

- `docs/reports/heldout-tranche-01-keyword-policy.md`
- `evidence_vault/reports/heldout-tranche-01-keyword-policy.json`

The command refuses to overwrite either file. A `blocked` result is a valid evidence outcome, not a tool error; preserve it and investigate through a separate intervention slice. See `docs/runbooks/heldout-evaluation-runbook.md`.

The next diagnostic step is the write-once failure autopsy. It reads the committed baseline rather than rescoring frozen cases:

```powershell
python .\scripts\run_heldout_failure_autopsy.py --repository-root .
```

It writes `docs/reports/heldout-tranche-01-failure-autopsy.md` and `evidence_vault/reports/heldout-tranche-01-failure-autopsy.json`. The autopsy identifies a narrowly testable intervention boundary, but it does not modify policy, ranking, frozen fixtures, or held-out evidence.

## Connection-pool direct-signal calibration intervention

ADR-0008 records the first calibration-only intervention arising from the held-out
failure autopsy. The policy now distinguishes direct connection-pool signals
(pool utilization and connection-acquisition latency) from contextual active
connection counts. Confirmed active connections cannot keep a connection-pool
family admissible once both direct pool signals are contradicted.

This is intentionally not a held-out result. Run the separate calibration-only
command after committing the intervention code:

```powershell
python .\scripts\run_connection_pool_direct_signal_calibration.py --repository-root . --top-k 5
```

It writes a new evidence pair and does not overwrite the prior calibration or
held-out baseline artifacts:

- `docs/reports/connection-pool-direct-signal-calibration.md`
- `evidence_vault/reports/connection-pool-direct-signal-calibration.json`

## Held-out direct-signal comparison and Handover 002

ADR-0008’s calibration evidence passed its declared safety checks. ADR-0009 now
permits one controlled comparison against the immutable Held-Out Tranche 01
baseline. The comparison is not a new baseline and does not overwrite any prior
evidence.

After committing comparison code on a clean branch, run:

```powershell
python .\scripts\run_heldout_direct_signal_comparison.py --repository-root . --top-k 5
```

The command verifies the frozen manifest, reads the committed PR #9 baseline,
records the post-intervention result in a separate write-once report pair, and
generates the project handover at the resulting evidence boundary:

- `docs/reports/heldout-tranche-01-direct-signal-comparison.md`;
- `evidence_vault/reports/heldout-tranche-01-direct-signal-comparison.json`;
- `docs/handover/Incident_Precedent_Retrieval_Harness_Handover_002_Post_Intervention_Comparison.md`.

The comparison can improve while remaining blocked. Its role is to preserve the
before/after evidence and identify the next narrowly scoped design boundary,
not to relax the promotion gate or tune frozen case labels.
