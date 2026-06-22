# Incident Precedent Retrieval Harness — Context Bundle

**Purpose:** Give this document, together with the current PRD and project handover template, to any LLM that will continue the Incident Precedent Retrieval Harness.

This is a project-continuity and implementation context bundle. It is not a generic summary. The next LLM must preserve the product boundary, data/evaluation integrity, Superlinked provider boundary, 50-hour timebox, and the user’s PowerShell/GitHub workflow.

---

## 1. Authority and Evidence Rules

Use sources in this order when facts conflict:

1. Latest user-provided terminal output.
2. Latest uploaded or repository files.
3. Latest explicit user correction.
4. This context bundle.
5. Older handovers or chat context.

Do not invent:

- repository state;
- current branch;
- successful clone state;
- Python version;
- virtual-environment command;
- Docker availability;
- Superlinked model IDs;
- managed Superlinked base URL;
- test output;
- evaluation scores;
- promotion-gate result;
- production readiness;
- use of real incident data.

Put unsupported facts under **Verify First**.

---

## 2. Project Identity

```text
Project name:
Incident Precedent Retrieval Harness

User-facing label:
Related Incident Evidence

Technical subtitle:
An evaluated retrieval reliability harness for historical incident precedent.

GitHub owner:
kablewithak

GitHub repository:
incident-precedent-retrieval-harness

Correct Git remote:
https://github.com/kablewithak/incident-precedent-retrieval-harness.git

Target local repository path:
C:\Users\kabom\Documents\Machine Learning\Machine Learning Workspace\incident-precedent-retrieval-harness

Shell:
Windows PowerShell

Editor:
VS Code

Primary language:
Python 3.11+ unless fresh environment evidence establishes another supported version.
```

### Critical username correction

The correct GitHub owner is:

```text
kablewithak
```

Do **not** use:

```text
kableiwthak
```

That typo was previously used in a clone attempt and caused a `Repository not found` error.

---

## 3. Current Repository State

### Confirmed

```text
- The GitHub repository URL is known.
- The intended local repository path is known.
- The project is at bootstrap stage.
- The repository was intended to be created empty, but its current contents are not yet verified.
```

### Not yet confirmed

```text
- Correct clone has completed.
- Local repository folder exists.
- Current branch name.
- Working tree state.
- First commit exists.
- Remote origin is configured locally.
- Docker Desktop is available.
- Python version and virtual environment setup.
```

### First orientation commands

Run these only after the user has cloned the repository successfully and is inside the repository root:

```powershell
git status
git remote -v
git log -1 --oneline
Get-Location
```

If the repository has no commits yet, `git log -1 --oneline` may fail. Record that as expected bootstrap evidence rather than treating it as an error.

### Correct clone command

From the parent workspace folder:

```powershell
Set-Location "C:\Users\kabom\Documents\Machine Learning\Machine Learning Workspace"

git clone https://github.com/kablewithak/incident-precedent-retrieval-harness.git

Set-Location ".\incident-precedent-retrieval-harness"

git status
git remote -v
Get-Location
```

Do not manually create the final repository folder before cloning. `git clone` creates it.

---

## 4. North Star

> **Build a production-shaped, source-grounded, evaluated incident-precedent retrieval harness that proves whether Superlinked-powered extraction, semantic retrieval, and reranking can surface useful historical evidence without causing unsafe operational anchoring.**

### Professional signal

> **Demonstrate the ability to design, evaluate, and govern an AI inference boundary for a realistic high-stakes operational workflow without overclaiming what the system knows or can safely do.**

### The central question

> **When is a historical incident comparable enough to surface as useful evidence to an on-call engineer, and when must the system abstain because doing so could anchor the responder on an unsafe investigation path?**

### The project is not

```text
- an incident-management platform;
- an alerting, paging, scheduling, or escalation system;
- a Slack or Teams bot;
- an observability dashboard;
- a live logs, metrics, traces, topology, or alert integration;
- a root-cause analysis engine;
- an automated remediation agent;
- a deployment rollback system;
- a generic RAG chatbot;
- a clone or competitor of Datadog, PagerDuty, Rootly, FireHydrant, incident.io, or Atlassian;
- validated on real company incident data;
- authorized for production incident response.
```

---

## 5. User, Workflow Position, and Product Promise

### Primary user

```text
An on-call backend, platform, or product engineer at a growth-stage
B2B SaaS company during early incident triage.
```

### Intended company profile

```text
- Roughly 20–150 engineers.
- Cloud-hosted B2B SaaS.
- Web application, public API, workers, queues, databases,
  caches, third-party integrations, and frequent deployments.
- Slack/Teams and a ticketing/wiki culture.
- Some on-call process and historical incidents.
- Operational evidence is scattered across incident records,
  postmortems, runbooks, deployment notes, tickets, and tribal knowledge.
```

### Workflow placement

```text
Alert acknowledged
→ responder checks current dashboards/logs/recent changes
→ responder needs historical operational context
→ Related Incident Evidence retrieves and evaluates historical precedent
→ responder reviews evidence alongside current telemetry
→ human responder decides what to investigate or escalate
```

### User-facing promise

> Find operationally comparable prior incidents and candidate investigation procedures, show why they may apply, identify what must be verified, and abstain when evidence is weak.

The system supports human investigation. It does not replace incident command.

---

## 6. Primary Safety Doctrine: Anti-Anchoring

### The failure to prevent

A historical incident can look semantically similar but be operationally incompatible.

Example:

```text
Current incident:
Checkout 502s plus queue backlog after deployment.

Unsafe lookalike:
Checkout latency caused by a cache stampede.

Potentially useful precedent:
Worker schema incompatibility after deployment caused consumers
to reject messages and queues to grow.
```

The system must treat this as a named failure:

```text
false_operational_match
```

### Required output posture

The system must:

```text
- show candidate precedents, not “the answer”;
- show candidate investigation procedures, not direct instructions;
- show why a precedent may be relevant;
- show why it may not apply;
- show which facts must be verified first;
- abstain where precedent is insufficient;
- surface conflicting precedent without selecting a preferred procedure;
- visibly state degraded inference conditions.
```

### Forbidden output language

```text
“The root cause is…”
“Use this runbook now.”
“Restart…”
“Rollback…”
“This will resolve the incident.”
“The incident is caused by…”
“Confidence is 96%, therefore…”
```

### Permitted output language

```text
Candidate precedent
Candidate investigation procedure
Why it may be relevant
Why it may not apply
Verify before using
Evidence is insufficient
Conflicting historical precedent
Human review required
Semantic retrieval currently degraded
```

---

## 7. Core Decision States

Use exactly these five decision states unless a documented ADR changes the contract:

```text
evidence_found
evidence_found_with_conflict
missing_critical_facts
insufficient_precedent
provider_degraded
```

| State | Meaning | Required behavior |
|---|---|---|
| `evidence_found` | Compatible historical precedent and eligible procedure have sufficient support. | Surface up to three candidates with caveats and verification facts. |
| `evidence_found_with_conflict` | Multiple plausible precedents imply materially different investigation paths. | Surface competing evidence, do not recommend a preferred procedure, require human review. |
| `missing_critical_facts` | A candidate may be relevant, but key verification facts are unknown. | Identify only the smallest set of missing facts needed to evaluate it safely. |
| `insufficient_precedent` | No credible comparable historical precedent exists. | Do not surface a procedure as applicable; state that historical evidence is insufficient. |
| `provider_degraded` | The SIE-backed semantic capability is unavailable or invalid. | Clearly state degraded mode; do not fake semantic confidence. |

---

## 8. Superlinked / SIE Provider Boundary

### Initial inference mode

The initial build uses **local self-hosted SIE via Docker**.

```text
Windows Python application
→ SuperlinkedSIEClient
→ SIE_BASE_URL=http://localhost:8080
→ local Docker SIE server
```

Docker hosts only the SIE inference server. The Python application, Pydantic schemas, local retrieval matrix/index, evaluation harness, promotion gate, and CLI/minimal interface run from the Windows repository.

### Local settings contract

```dotenv
SIE_BASE_URL=http://localhost:8080
SIE_API_KEY=
SIE_TIMEOUT_SECONDS=30
```

### Managed SIE rule

Only a Superlinked API key is currently known. No managed endpoint/base URL has been confirmed.

Therefore:

```text
- Do not guess a hosted Superlinked URL.
- Do not claim hosted SIE access or hosted-credit consumption.
- Do not pass the API key to local Docker merely because it exists.
- Do not put the key in source control, `.env.example`, logs, traces,
  screenshots, reports, PR text, or handovers.
```

Managed mode is a later configuration option only if a real endpoint becomes available. It must remain behind the same provider-neutral adapter.

### Required application boundary

```text
CLI / minimal local interface
→ IncidentEvidenceService
→ SemanticInferenceClient protocol
→ SuperlinkedSIEClient
→ SIE extract / encode / score at local Docker endpoint

Tests
→ IncidentEvidenceService
→ FakeSemanticInferenceClient
```

### Strict dependency rule

The following packages must not import Superlinked SDK objects directly:

```text
domain
intake
retrieval policy
procedure policy
decision policy
eval harness
reporting
CLI/UI
tests outside adapter integration tests
```

Only the Superlinked adapter package may know SDK/client response shapes and provider-specific exceptions.

### What SIE does

```text
extract:
derive candidate operational signals from safe incident text.

encode:
create vectors for historical incident retrieval.

score:
rerank broad candidate incidents using query-candidate pair scoring.
```

### What SIE does not decide

```text
- root cause;
- severity;
- whether to execute a procedure;
- whether an action is safe;
- whether a historical precedent is sufficiently comparable;
- whether to abstain;
- whether to promote a pipeline;
- whether provider degradation can be ignored.
```

Deterministic domain policy makes those decisions.

---

## 9. Local Docker SIE Capability Spike

This is Phase 0 and must be completed or explicitly blocked before real-SIE claims.

### Initial Docker command

```powershell
docker run --rm -p 8080:8080 ghcr.io/superlinked/sie-server:latest-cpu-default
```

Use CPU first. Do not add CUDA/GPU complexity unless the user explicitly wants it and local Docker GPU support is already proven.

### Phase 0 must separately verify

```text
1. Docker is available.
2. The SIE server responds locally.
3. An extract operation works with incident labels.
4. An encode operation returns usable vectors.
5. A score operation reranks candidate incident text.
6. Adapter failures become typed application failures.
7. Latency is recorded.
8. No secrets are logged.
```

### Non-claim

A Docker process, a health response, or an open localhost port does **not** prove:

```text
- model-specific inference readiness;
- extraction correctness;
- embedding usefulness;
- reranking usefulness;
- profile availability;
- production readiness.
```

If local SIE validation is blocked, build the provider-neutral protocol and fake client anyway, document the block, and do not claim real SIE validation.

---

## 10. Architecture

### Offline corpus preparation

```text
Public source material
→ human-authored source-grounded incident cards
→ provenance manifest
→ candidate signal extraction
→ deterministic canonicalization
→ Pydantic validation
→ local embedding index
```

### Online triage flow

```text
Structured fields + optional short free text
→ validate and redact
→ candidate signal extraction
→ deterministic canonicalization
→ validated IncidentFingerprint
→ broad candidate retrieval
→ rerank top candidates
→ deterministic anti-anchoring policy
→ procedure eligibility filter
→ typed EvidencePacket
```

### Evaluation flow

```text
Keyword baseline
Dense retrieval baseline
Dense retrieval + reranking
Extraction + dense retrieval + reranking + safety policy
→ held-out evaluation suite
→ quality + safety + latency + provider-failure scoring
→ promotion gate
→ PROMOTE or BLOCK for local evaluated demonstration
```

---

## 11. Dataset Strategy and Integrity Rules

### Data posture

Use a **source-grounded synthetic incident archive**.

```text
Public incident evidence
→ manually extract real operational mechanisms and response patterns
→ adapt into one coherent fictional SaaS environment
→ human-author labels and variants
→ run reproducible retrieval and safety evaluation
```

The fictional environment is named:

```text
RelayOps
```

It represents a growth-stage B2B SaaS company with a web app, public API, authentication, workers, queues, PostgreSQL, Redis/cache, webhooks, object storage, feature flags, and selected third-party dependencies.

### Sources

Use public sources to ground mechanisms, terminology, timelines, and mitigation patterns. Do not copy articles into the corpus unless licensing explicitly permits it.

Source categories already agreed:

```text
Primary licensed source:
- PostHog public postmortem repository, with attribution and required MIT notice where applicable.

Official public reference sources:
- Cloudflare postmortems
- GitHub post-incident analyses
- OpenAI incident/status write-ups

Optional supporting source:
- carefully reviewed small Rootly AI Labs public log snippets,
  used only as noisy evidence examples, not as the incident corpus.

Methodology reference:
- Rootly SRE Skills Bench, for separated evaluation thinking only.
```

### Dataset target

```text
32 historical incident cards
8 incident families
8–10 candidate investigation procedures
12 calibration/evaluation-development cases
36 held-out final evaluation cases
12 false-operational-match cases within the holdout
8 no-precedent cases within the holdout
4 conflicting-precedent cases within the holdout
6–8 deterministic provider-failure simulations
```

### Incident families

```text
1. Deployment-related worker crash loop
2. Queue backlog caused by consumer failure
3. Database migration lock contention
4. Connection-pool exhaustion
5. Cache stampede / cache invalidation failure
6. Third-party webhook or provider degradation
7. Feature-flag rollout regression
8. Rate-limit or authentication configuration regression
```

### Record-origin rule

Every incident card must declare:

```yaml
record_origin: source_grounded | controlled_variant | synthetic_no_precedent
```

Every source-grounded card must declare provenance:

```yaml
provenance:
  source_record_id: string
  source_name: string
  source_url: string
  source_date: YYYY-MM-DD | null
  usage_mode: licensed_source | cited_reference | manually_authored_variant
  transformation_note: string
  human_verified: true
```

### Held-out evaluation constitution

```text
12 standard positive cases
12 false-operational-match cases
 8 no-precedent cases
 4 conflicting-precedent cases
-----------------------------
36 held-out cases
```

### Non-negotiable integrity rules

```text
- Do not use real company incident records.
- Do not use private Slack/Teams exports, private tickets, production logs,
  customer data, secrets, internal hostnames, IP addresses, or credentials.
- Do not tune thresholds, prompt labels, retrieval behavior, reranking behavior,
  or canonicalization rules on held-out cases.
- Do not change holdout labels after freezing unless a documented data defect exists.
- Do not use an exact rewrite of a corpus incident as a held-out query.
- Do not include ground-truth fields such as incident ID, failure mechanism,
  safe procedure IDs, or unsafe procedure IDs in model prompts.
- Do not claim the corpus represents actual production history.
```

---

## 12. Candidate Investigation Procedure Rules

Procedures must be named:

```text
Candidate Investigation Procedures
```

Not “recommended runbooks.”

Every procedure needs:

```text
- procedure ID;
- title;
- version;
- status: current | stale | retired;
- applicable incident families;
- explicit non-applicability conditions;
- required verification prerequisites;
- safe investigation steps;
- unsafe/out-of-scope actions;
- last-reviewed date;
- owner role.
```

A procedure can be surfaced only when deterministic policy finds it eligible.

Do not allow the model or embedding similarity alone to make a procedure eligible.

---

## 13. Evaluation and Promotion Gate

### Pipeline variants

```text
A. Keyword retrieval baseline
B. Dense retrieval baseline
C. Dense retrieval + reranking
D. Extraction + dense retrieval + reranking + anti-anchoring safety policy
```

The more complex pipeline must earn its complexity.

### Required metrics

```text
correct_precedent_mrr
incident_family_recall_at_5
safe_precedent_top_1_rate
false_operational_match_rate
candidate_procedure_relevance
unsafe_procedure_surfacing_rate
no_precedent_abstention_accuracy
missing_fact_precision
p50_pipeline_latency_ms
p95_pipeline_latency_ms
provider_failure_safe_resolution_rate
```

### Promotion gate principle

A pipeline is **not** promoted merely because MRR improves.

It must also avoid unsafe operational matches, abstain correctly when precedent is absent, avoid unsafe procedure surfacing, remain within stated latency budget, and resolve provider failures safely.

### Gate status labels

```text
not_run
blocked
eligible_for_local_demonstration
promoted_for_local_evaluated_demonstration
```

Never use:

```text
production_promoted
production_ready
incident-response safe
```

### CI tiers

```text
Tier 1 — deterministic repository checks
- fake provider
- fixtures
- contract tests
- policy tests
- promotion-gate policy tests
- no live provider dependency

Tier 2 — manual real-SIE profile run
- local Docker SIE
- held-out evaluation
- quality/latency report
- required before changing profile/model configuration
```

---

## 14. 50-Hour Delivery Contract

This is a 50-hour evidence project. Do not expand scope without replacing something.

| Hours | Phase | Evidence / Gate |
|---:|---|---|
| 0–4 | Phase 0: Local SIE capability spike and provider-boundary ADR | Docker/adapter reality proven or explicitly blocked. |
| 4–12 | Phase 1: Dataset constitution, source manifest, corpus, procedures, split | Provenance and holdout gates pass. |
| 12–20 | Phase 2: Keyword and dense retrieval baselines | Reproducible baseline report exists. |
| 20–30 | Phase 3: Superlinked `extract` / `encode` / `score` adapter | Typed adapter and real/fake boundary tests exist. |
| 30–37 | Phase 4: Anti-anchoring policy, abstention, conflict, provider-degraded behavior | Decision state and safety tests pass. |
| 37–44 | Phase 5: Eval harness, failure gallery, promotion gate | Held-out evaluation and pass/block decision exist. |
| 44–48 | Phase 6: CLI or minimal local interface and trace view | Demo shows a correct case, false match, no-precedent, provider-degraded case. |
| 48–50 | Phase 7: README, architecture diagram, demo script, cleanup | Buyer/engineer-readable evidence pack exists. |

### Allowed features

Only build features that improve at least one of:

```text
- precedent-retrieval quality;
- anti-anchoring safety;
- provider-boundary reliability;
- reproducibility/regression safety;
- buyer/hiring-manager inspection quality.
```

### Explicit deferrals

```text
- PagerDuty, Datadog, Jira, GitHub, Slack, Teams, or observability integration;
- live logs, metrics, traces, alerts, service catalog, or ownership data;
- real incident ingestion;
- incident declaration, paging, schedules, escalation policies;
- automated remediation;
- deployment rollback;
- root-cause diagnosis;
- cloud deployment;
- enterprise auth;
- multi-tenancy;
- hosted vector database;
- multi-agent workflows;
- a large frontend/dashboard.
```

---

## 15. Expected Repository Structure

This is the planned layout. Confirm files exist before claiming they do.

```text
incident-precedent-retrieval-harness/
  README.md
  pyproject.toml
  .env.example
  LICENSE
  NOTICE.md
  docs/
    adr/
      ADR-0001-product-boundary.md
      ADR-0002-provider-boundary.md
      ADR-0003-dataset-and-provenance.md
      ADR-0004-promotion-gate.md
    data/
      dataset-constitution.md
      source-manifest.md
      labeling-guide.md
    runbooks/
      operator-runbook.md
      data-curation-runbook.md
      provider-spike-runbook.md
      local-sie-docker-runbook.md
    demo/
      demo-script.md
    reports/
      final-evaluation-report.md
      final-promotion-report.md
    planning/
      Incident_Precedent_Retrieval_Harness_PRD.md
    handover/
      Incident_Precedent_Retrieval_Harness_Handover_Template.md
    context/
      Incident_Precedent_Retrieval_Harness_CONTEXT_BUNDLE.md
  src/
    incident_precedent_harness/
      config/
      domain/
        models.py
        enums.py
        policies.py
      inference/
        protocol.py
        models.py
        superlinked_client.py
        fake_client.py
        errors.py
      intake/
        validation.py
        redaction.py
        extraction.py
        canonicalization.py
      retrieval/
        keyword.py
        dense.py
        rerank.py
        repository.py
      procedures/
        eligibility.py
      decisions/
        evidence_policy.py
      evals/
        cases.py
        metrics.py
        runner.py
        reports.py
        promotion_gate.py
      tracing/
        events.py
        recorder.py
      cli/
        main.py
  data/
    incidents/
    procedures/
    evals/
      calibration/
      heldout/
  evidence_vault/
    traces/
    reports/
    screenshots/
    promotion_reports/
  scripts/
    provider_spike.py
    build_index.py
    run_eval.py
    run_promotion_gate.py
  tests/
    unit/
    integration/
    contract/
```

### Session artifacts currently available

These are ChatGPT/session artifacts, not confirmed local repository files:

```text
/mnt/data/Incident_Precedent_Retrieval_Harness_PRD.md
/mnt/data/Incident_Precedent_Retrieval_Harness_Handover_Template.md
/mnt/data/Incident_Precedent_Retrieval_Harness_CONTEXT_BUNDLE.md
```

When the documentation structure is created in the repository, the intended target paths are:

```text
docs\planning\Incident_Precedent_Retrieval_Harness_PRD.md
docs\handover\Incident_Precedent_Retrieval_Harness_Handover_Template.md
docs\context\Incident_Precedent_Retrieval_Harness_CONTEXT_BUNDLE.md
```

Choose **Replace** if Windows prompts when copying a later revised version into the same target path.

---

## 16. Privacy, Security, and Logging Rules

### Allowed data

```text
- fictional source-grounded incident cards;
- public postmortem mechanisms;
- public, licensing-appropriate source references;
- limited, carefully reviewed public log fragments only where permitted;
- metadata-safe trace records.
```

### Prohibited data

```text
- real customer incidents;
- private incident tickets;
- private Slack/Teams exports;
- production logs;
- real infrastructure identifiers;
- internal hostnames;
- IP addresses;
- tenant/customer/account IDs;
- email addresses;
- credentials;
- API keys;
- tokens;
- signed URLs;
- raw provider payloads.
```

### Safe trace fields

```text
trace_id
operation_name
profile_id
latency_ms
candidate_incident_ids
decision_state
failure_code
fallback_status
```

### Do not log

```text
raw incident narrative
full procedure text
full provider response
secrets
private system context
raw prompt
raw source postmortem text
```

This project describes engineering controls aligned with privacy principles. It does not make legal-compliance claims.

---

## 17. User Workflow Preferences

The user works in Windows PowerShell and VS Code.

### File delivery

```text
- Prefer full-file replacements, not partial patches.
- Provide downloadable files for generated/replacement files.
- State the exact destination path beside each download.
- Generated filename must match final destination filename exactly.
- Tell the user to choose Replace if Windows asks.
- Avoid Downloads-folder staging.
- For more than three generated/replacement files, prefer a ZIP.
- For more than two files needed from the user as context, ask for one descriptive ZIP created on the Desktop.
```

### Validation

```text
- Run tests only when behavior, code, contracts, runtime, schemas, or safety rules change.
- Put each pytest command on its own line.
- Do not add Test-Path, marker checks, pytest, or formal validation ceremony to
  docs-only, planning-only, prompt-only, or handover-only slices unless needed.
- Do not claim repository-wide tests if only focused tests ran.
```

### Git workflow

```text
- One branch per slice.
- Begin new implementation slices from confirmed clean main.
- Confirm state from the latest terminal output.
- Run git status before staging.
- Run git status again after git add.
- Use a semantic commit message.
- Push the feature branch.
- Provide a clean GitHub-safe PR description.
- Include one complete after-merge sync/delete PowerShell block in the same response.
- Do not place `git --no-pager log -1 --oneline` directly after feature-branch push.
  Use it in the after-merge cleanup/orientation block only.
- Do not assume main is clean, a branch is merged, or a remote branch exists without evidence.
```

### Confirmation signals

```text
“excellent work”
“what’s next?”
“take it away”
```

These usually mean the user followed the prior instructions, accepts the prior slice, and is ready for the next concrete step. They do not permit skipping verification, privacy, eval, or Git discipline.

---

## 18. Handover Rules

Use the project-specific handover template for formal handovers.

Create a formal handover only at a safe boundary, such as:

```text
- phase gate passed or failed with recorded evidence;
- branch merged and main confirmed clean;
- dataset constitution or held-out split frozen;
- Superlinked local-provider spike concluded;
- baseline or intervention report exists;
- promotion gate ran;
- material safety/architecture decision recorded;
- intentional pause at a safe boundary.
```

Do not create formal handovers in the middle of a small implementation slice.

Every handover must preserve:

```text
- current 50-hour budget and phase;
- repo state backed by terminal evidence;
- dataset count, provenance and split status;
- held-out freeze status;
- Superlinked extract/encode/score validation status;
- anti-anchoring and decision-state status;
- evaluation and promotion-gate metrics;
- privacy/data boundary;
- strict non-claims;
- next safest slice;
- exact user workflow preferences.
```

---

## 19. Commercial and Hiring Translation

This is not positioned as a product that replaces Datadog, PagerDuty, Rootly, FireHydrant, incident.io, or Atlassian.

The portfolio claim is:

> A production-shaped, source-grounded evaluation harness for testing whether historical incident retrieval can surface operationally comparable evidence safely. It measures retrieval quality, unsafe lookalike incidents, abstention behavior, provider failures, and latency.

The strongest professional signal is:

> The operator understands that retrieval quality alone is not sufficient. An inference pipeline can improve MRR while becoming operationally less safe; the promotion gate blocks that regression.

The project supports future consultancy positioning around:

```text
AI System Evaluation Audit
AI Reliability Pilot
Agent / workflow reliability evaluation
Provider-boundary hardening
Retrieval quality and regression governance
```

It does not yet prove commercial delivery, production operational impact, customer-data readiness, or production incident-response readiness.

---

## 20. Immediate Next Safe Slice

### Current intended phase

```text
Bootstrap / pre-Phase 0
```

### First objective

Establish the repository foundation and create the local-Docker SIE capability spike boundary.

### Before code, verify first

```text
- Correct repository clone exists.
- Current Git status.
- Remote origin.
- Whether the repo has an initial commit.
- Docker Desktop/CLI availability.
- Python version.
- Virtual environment approach.
```

### Do not do yet

```text
- Do not add real corpus data before dataset constitution and provenance structure exist.
- Do not guess Superlinked model IDs.
- Do not add a UI.
- Do not add cloud services.
- Do not attempt managed SIE calls with only an API key.
- Do not add integrations.
- Do not make real-SIE readiness or performance claims.
```

---

## 21. Quick Resume Checklist for the Next LLM

```text
- Read this context bundle first.
- Read the PRD.
- Read the project-specific handover template.
- Confirm the local repository exists.
- Run git status.
- Run git remote -v.
- Run git log -1 --oneline if a commit exists.
- Confirm current branch and working tree state.
- Confirm Python and Docker availability before provider implementation.
- Treat local Docker SIE as the only approved inference mode initially.
- Keep the API key out of the repo and do not infer a hosted endpoint.
- Preserve source-grounded synthetic dataset rules.
- Preserve holdout isolation.
- Preserve anti-anchoring controls.
- Keep the system’s five decision states.
- Do not add out-of-scope incident-platform features.
- For code changes, give branch → files → tests → Git → PR → full after-merge cleanup.
- For docs-only work, keep validation lean.
- Never overclaim maturity or real-world incident impact.
```

---

## 22. Final Instruction to the Next LLM

Be strict.

The project is only impressive if it remains narrow, evaluated, and honest.

```text
Production-shaped does not mean production-ready.
Source-grounded synthetic data does not mean real incident-data validated.
A local Docker health response does not mean model-specific inference is ready.
Higher MRR does not mean safer incident support.
A plausible historical match does not establish root cause.
A candidate investigation procedure is not an instruction.
An API key does not identify a managed endpoint.
```

Build the smallest system that can be inspected, evaluated, explained, maintained, and defended.
