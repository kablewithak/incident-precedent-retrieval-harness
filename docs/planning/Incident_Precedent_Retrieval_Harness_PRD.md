# Product Requirements Document
# Incident Precedent Retrieval Reliability Harness

**Repository name:** `incident-precedent-retrieval-harness`  
**User-facing label:** **Related Incident Evidence**  
**Technical subtitle:** *An evaluated retrieval reliability harness for historical incident precedent.*  
**Version:** 1.1  
**Status:** Build-ready PRD; repository identity and local-Docker inference posture locked  
**Delivery constraint:** **50 focused hours maximum**  
**Maturity target:** Production-shaped; locally validated; source-grounded synthetic-incident-data validated.  
**Explicit non-claim:** Not production incident-response tested. Not an incident-management platform. Not a root-cause system. Not authorized for automated remediation.

**GitHub repository:** [`kablewithak/incident-precedent-retrieval-harness`](https://github.com/kablewithak/incident-precedent-retrieval-harness)  
**Repository URL:** `https://github.com/kablewithak/incident-precedent-retrieval-harness.git`  
**Target local repository path:** `C:\Users\kabom\Documents\Machine Learning\Machine Learning Workspace\incident-precedent-retrieval-harness`  
**Local inference mode:** Docker-hosted SIE at `http://localhost:8080`  
**Managed SIE mode:** Not in scope for the initial build. Only an API key is available; no managed SIE endpoint URL has been provided. Do not infer or guess one.  

---


## 0.1 Confirmed repository and local execution facts

### Confirmed repository identity

```text
GitHub owner: kablewithak
GitHub repository: incident-precedent-retrieval-harness
Repository URL: https://github.com/kablewithak/incident-precedent-retrieval-harness.git
Target local repository path:
C:\Users\kabom\Documents\Machine Learning\Machine Learning Workspace\incident-precedent-retrieval-harness
Shell: Windows PowerShell
Editor: VS Code
```

### Local SIE execution contract

The initial build uses **local self-hosted SIE via Docker**. Docker hosts only the SIE inference server. The Python application, tests, local retrieval index, evaluation harness, promotion gate, and CLI/minimal interface run from the Windows repository and its Python virtual environment.

```text
Windows Python application
  -> SuperlinkedSIEClient
    -> SIE_BASE_URL=http://localhost:8080
      -> local Docker SIE server
```

Initial local settings:

```dotenv
SIE_BASE_URL=http://localhost:8080
SIE_API_KEY=
SIE_TIMEOUT_SECONDS=30
```

### Strict managed-access rule

A Superlinked API key by itself does not identify a managed inference endpoint. The initial build must therefore **not** claim hosted Superlinked inference, hosted-credit consumption, or managed-cluster validation.

Do not:

- guess a Superlinked hosted URL;
- put the API key into source control, `.env.example`, logs, traces, screenshots, or reports;
- pass the API key to the local Docker server merely because it exists;
- treat a Docker health response as proof that `extract`, `encode`, and `score` are model-ready.

Managed SIE validation may be added only if a real managed base URL becomes available through an existing account, dashboard, or supplied configuration. That would be a later configuration change behind the same provider adapter, not a rewrite of domain logic.

### Repository-state note

The repository URL and intended local path are known. Current clone state, first commit, main-branch state, Python version, virtual-environment command, and Docker availability must be verified from fresh PowerShell evidence before implementation claims are made.

---

## 0. Read this first: north star and delivery contract

### North star

> **Build a production-shaped, source-grounded, evaluated incident-precedent retrieval harness that proves whether Superlinked-powered extraction, semantic retrieval, and reranking can surface useful historical evidence without causing unsafe operational anchoring.**

### Professional signal

> **Demonstrate the ability to design, evaluate, and govern an AI inference boundary for a real high-stakes workflow without overclaiming what the system knows or can safely do.**

### The central product question

> **When is a historical incident comparable enough to surface as useful evidence to an on-call engineer, and when must the system abstain because doing so could send the responder down an unsafe path?**

### The time-crunch rule

This is a **50-hour evidence project**, not a startup MVP.

Every feature must improve at least one of:

1. precedent-retrieval quality;
2. anti-anchoring safety;
3. provider-boundary reliability;
4. reproducibility and regression safety;
5. buyer/hiring-manager inspection quality.

If it does not improve one of those, it is out of scope.

### Absolute scope rule

A polished, evaluated, narrow system is better than a broad incident copilot that is unfinished, unmeasured, or unsafe.

---

## 1. Executive summary

### 1.1 What is being built

Related Incident Evidence is a local, production-shaped decision-support prototype for early incident triage.

A responder supplies a short, sanitized incident summary with optional structured fields. The system:

1. validates and redacts the intake;
2. derives a constrained operational fingerprint;
3. retrieves historical incidents from a source-grounded synthetic archive;
4. reranks candidate precedents;
5. applies deterministic safety policy;
6. surfaces candidate investigation procedures only when applicable;
7. identifies critical unknown facts;
8. abstains when precedent is insufficient or conflicting;
9. records metadata-safe traces;
10. blocks candidate inference pipelines when held-out safety, quality, latency, or degraded-mode gates fail.

### 1.2 What it is not

The project is **not**:

- PagerDuty, Datadog, Rootly, FireHydrant, incident.io, or an alternative to them;
- an alert-ingestion platform;
- a pager, schedule, escalation-policy, or incident-command system;
- a live telemetry, logs, metrics, traces, or topology integration;
- a root-cause analysis engine;
- a remediation agent;
- a deployment rollback system;
- an autonomous SRE agent;
- a generic RAG chatbot;
- a claim that AI can safely diagnose outages;
- a claim of production incident-response impact.

### 1.3 User-facing promise

> **Find operationally comparable prior incidents and candidate investigation procedures, show why they may apply, identify what must be verified, and abstain when evidence is weak.**

### 1.4 Technical thesis

Superlinked is used as the first real inference provider behind a provider-neutral application contract:

```text
business workflow
  -> stable domain contracts
    -> semantic inference protocol
      -> Superlinked adapter
        -> SIE extract / encode / score
```

The project must prove that model profile, provider availability, latency, and response shape are controlled dependencies, not hidden application risks.

---

## 2. Problem and opportunity

### 2.1 The current operational problem

Growth-stage SaaS incident responders routinely need to answer:

- Has this happened before?
- Which prior incident is actually comparable?
- Is there an investigation procedure worth inspecting?
- What changed before the failure?
- Which facts must be verified before treating the historical case as useful?
- Is the current incident too novel or ambiguous for historical evidence to be useful?

The relevant information usually exists but is fragmented across:

- incident records;
- postmortems;
- runbooks;
- deployment history;
- service ownership records;
- chat threads;
- tickets;
- individual engineer memory.

The current manual behavior is often:

```text
alert acknowledged
  -> dashboard/log/deploy inspection
  -> search old incidents, postmortems, docs, and chat
  -> ask the engineer who remembers a prior failure
  -> inspect a runbook if one can be found
  -> human mitigation and investigation
```

### 2.2 The actual reliability risk

A plausible-looking historical match can be harmful.

Two incidents can share words such as `latency`, `checkout`, `error`, or `deployment`, while being operationally incompatible:

```text
Current incident:
Checkout 502s plus queue backlog after deployment.

Unsafe lookalike:
Checkout latency caused by a cache stampede.

Potentially useful precedent:
Worker schema incompatibility after deployment causes consumers
to reject messages and queues to grow.
```

A system that simply returns the top semantic match can anchor an on-call engineer on the wrong subsystem.

This project treats that as a named failure:

```text
false_operational_match
```

### 2.3 Product opportunity

Do not solve incident management.

Solve one inspectable decision boundary:

> **Whether historical evidence is safe enough to surface as a candidate operational precedent.**

The value is not “AI tells engineers how to fix incidents.”

The value is:

- more useful historical evidence;
- fewer shallow keyword-search failures;
- fewer unsafe lookalike matches;
- visible uncertainty;
- explicit missing facts;
- clear human-review boundaries;
- an auditable decision to promote or block model/pipeline changes.

---

## 3. Intended users and operating context

### 3.1 Target organization

The project models a growth-stage, cloud-based B2B SaaS organization with:

- approximately 20–150 engineers;
- recurring software releases and configuration changes;
- a web application, public API, background workers, queues, database, cache, feature flags, and external dependencies;
- an on-call or incident escalation process;
- a Slack- or Teams-like coordination culture;
- scattered incident knowledge but no deeply integrated internal reliability knowledge platform.

### 3.2 Primary user

**Primary on-call engineer**: backend, platform, or product engineer who has acknowledged an alert and needs early triage context.

The primary user asks:

```text
Has this happened before?
What old incident should I inspect first?
Why is it actually comparable?
What procedure could be relevant?
What facts must I verify?
When should I ignore this result and escalate?
```

### 3.3 Secondary users

| User | Need |
|---|---|
| Secondary on-call / service owner | Get an evidence packet without rereading old incident threads. |
| Incident Commander | Confirm that suggested precedent is evidence-backed and does not claim a diagnosis. |
| Platform / SRE lead | Inspect retrieval safety, failure patterns, and regression-gate evidence. |
| AI hiring manager / CTO | Inspect boundary design, model evaluation, safety policy, and non-claims. |

### 3.4 Workflow placement

The prototype enters **after alert acknowledgment** and during early investigation:

```text
alert fires
  -> on-call acknowledges
    -> responder assesses impact and current signals
      -> responder submits safe incident summary
        -> Related Incident Evidence retrieves candidate precedent
          -> human inspects dashboard/logs/deploy context
            -> human investigates, mitigates, or escalates
```

### 3.5 Out-of-workflow boundaries

The system must never:

- page responders;
- declare severity;
- open or manage an incident channel;
- create tickets;
- instruct a rollback;
- execute a runbook;
- restart a service;
- assert root cause;
- declare an incident resolved;
- communicate externally;
- replace an Incident Commander.

---

## 4. Product principles

### P1. Evidence, not diagnosis

The system can surface historical evidence and candidate investigation procedures. It must not state or imply root cause.

### P2. Anti-anchoring over apparent intelligence

A top-ranked precedent is only valuable if it is operationally compatible. A safe abstention is superior to a confident, misleading match.

### P3. Structured contracts at every probabilistic boundary

All application-facing input/output contracts use Pydantic v2 models and enums. Raw provider objects and unvalidated dictionaries do not cross the provider boundary.

### P4. Model choice is an evaluated configuration, not an opinion

A model/profile/pipeline may be promoted only after passing a held-out evaluation gate.

### P5. Provider-neutral core, Superlinked-first adapter

The application core depends on semantic capabilities, not on SIE SDK types or exceptions.

### P6. Realism through source grounding, validity through controlled labels

The corpus must reflect real operational failure patterns while remaining a coherent fictional environment with human-authored ground truth.

### P7. A smaller system that proves a hard thing beats a broad demo

No integrations or platform features that do not strengthen the evidence story.

### P8. Safety metrics may veto quality gains

A more complex pipeline is rejected if it improves MRR or Recall but increases unsafe matching, unsafe procedure surfacing, or degraded-mode risk.

---

## 5. Success definition and non-claims

### 5.1 Definition of done

The project is done only when it includes:

- a source-grounded synthetic incident archive;
- a documented dataset constitution;
- a safe/unsafe precedent labeling scheme;
- a provider-neutral semantic inference protocol;
- a real Superlinked adapter;
- a deterministic fake provider;
- keyword, dense, reranked, and structured pipelines;
- held-out evaluation cases;
- an anti-anchoring safety policy;
- typed decision states;
- metadata-safe traces;
- provider failure tests;
- an executable promotion gate;
- a readable final report;
- one local demo surface;
- clear run instructions;
- clear non-claims.

### 5.2 Maturity label

```text
Production-shaped
Locally validated
Source-grounded synthetic-incident-data validated
Not customer-data tested
Not production incident-response tested
Not authorized for automated remediation
```

### 5.3 Permitted claims

The project may claim only:

> This prototype evaluates whether structured incident extraction, semantic retrieval, and reranking improve retrieval of operationally comparable historical precedent over simpler baselines on a held-out, source-grounded synthetic dataset.

> The prototype evaluates false operational matches, abstention behavior, latency, and safe provider degradation.

> Candidate pipeline profiles are blocked when predefined quality, safety, latency, or degraded-mode gates are violated.

### 5.4 Prohibited claims

Do not claim:

- that incident resolution time improved;
- that outages are diagnosed;
- that the tool prevents incidents;
- that the system is production-ready;
- that the system has been tested with real company incident history;
- that SIE is the best provider/model universally;
- that any public postmortem source validates fictional RelayOps incidents;
- that a candidate procedure is an instruction to execute.

---

## 6. Scope

### 6.1 In scope

1. One fictional SaaS environment: **RelayOps**.
2. Source-grounded synthetic incident corpus.
3. Local repository and local execution.
4. CLI-first or very small local web surface.
5. Structured incident intake plus optional free text.
6. Entity/signal extraction through Superlinked.
7. Dense retrieval through Superlinked embeddings.
8. Candidate reranking through Superlinked scoring.
9. Deterministic safety and procedure-eligibility policy.
10. Fixed eval set, baseline comparison, trace review, promotion gate.
11. Simulated provider failures.
12. Safe traces, runbooks, ADRs, report, README, and demo script.

### 6.2 Explicitly out of scope

```text
PagerDuty / Opsgenie / Rootly / incident.io integration
Slack / Teams bot
Datadog / Grafana / New Relic integration
Live logs, metrics, traces, or alert ingestion
Cloud deployment
Hosted vector database
Background workers, queues, or event streaming
Authentication, authorization, multi-tenancy
Enterprise audit controls
Ticket creation
On-call scheduling
Status pages
Automatic remediation
Runbook execution
Root-cause declaration
Prompt optimization project
Fine-tuning
Multi-agent system
Mobile client
Heavy frontend/dashboard work
```

### 6.3 Scope-kill rule

Any feature that requires more than 90 minutes and does not directly improve the evaluation gate, data realism, provider boundary, or demo clarity must be cut.

---

## 7. The fictional environment: RelayOps

### 7.1 Purpose

RelayOps provides a coherent fictional operational environment. It prevents the corpus from becoming an incoherent mixture of unrelated public incidents.

### 7.2 System topology

```text
Customer web app
  -> Public API
      -> Authentication service
      -> Workflow service
      -> Payments integration
      -> Webhook delivery service
      -> Background workers
      -> Queue / event processing
      -> PostgreSQL
      -> Redis
      -> Object storage
      -> Feature flags
      -> Third-party provider dependencies
```

### 7.3 Service names

Use a stable, small set:

- `edge-api`
- `auth-service`
- `workflow-service`
- `payments-api`
- `webhook-worker`
- `notification-worker`
- `event-queue`
- `postgres-primary`
- `redis-cache`
- `feature-flag-service`
- `object-storage-adapter`
- `third-party-provider-adapter`

### 7.4 Incident families

Exactly eight:

1. deployment-related worker crash loop;
2. queue backlog caused by consumer failure;
3. database migration lock contention;
4. connection-pool exhaustion;
5. cache stampede or cache-invalidation failure;
6. third-party webhook/provider degradation;
7. feature-flag rollout regression;
8. rate-limit or authentication-configuration regression.

### 7.5 Strict corpus coherence gate

Before code implementation begins:

- each incident record must map to exactly one primary incident family;
- each incident must use RelayOps services and topology;
- each incident must have a plausible timeline;
- each incident must have a human-authored operational mechanism;
- no record may copy a public postmortem verbatim;
- every source-grounded record must carry provenance metadata;
- each procedure must state applicability and non-applicability conditions.

**Gate outcome:** Do not proceed to indexing until all corpus records pass schema validation and manual provenance review.

---

## 8. Data strategy and dataset constitution

### 8.1 Data posture

The corpus is **source-grounded synthetic data**, not a claim of real customer incident history.

```text
Public incident evidence
  -> manually extracted mechanisms and response patterns
    -> controlled RelayOps adaptation
      -> human-authored labels
        -> reproducible evaluation assets
```

### 8.2 Source hierarchy

#### Primary: licensed public postmortem source

Use the public PostHog postmortem repository as a source of incident structure and engineering language. Preserve attribution and the required MIT license material for any included/derived portions.

#### Secondary: official public incident analyses

Use official incident write-ups from organizations such as Cloudflare, GitHub, and OpenAI as **cited references** for manually extracted failure mechanisms, timelines, and recovery patterns.

Do not commit copied articles. Do not imply the fictional incident occurred at the source organization.

#### Supporting: optional real log fragments

Use a very small number of carefully reviewed Rootly AI Labs log-dataset snippets only as optional noisy evidence examples. They are not the incident corpus and must not drive root-cause conclusions.

#### Methodology reference

Use Rootly SRE Skills Bench only as an inspiration for separated task evaluation, not as the core dataset.

### 8.3 Dataset size

| Asset | Target | Requirement |
|---|---:|---|
| Public source documents reviewed | 20–25 | Source manifest required |
| Historical incident cards | 32 | Four per family across eight families |
| Candidate investigation procedures | 8–10 | Explicit applicability metadata |
| Calibration/evaluation-development cases | 12 | Never used as final holdout |
| Held-out final evaluation cases | 36 | Fixed before final tuning |
| False-operational-match cases | 12 | Within held-out set |
| No-precedent cases | 8 | Within held-out set |
| Conflicting-precedent cases | 4 | Within held-out set |
| Standard positive cases | 12 | Within held-out set |
| Provider-failure simulations | 6–8 | Deterministic tests |

### 8.4 Holdout constitution

The held-out final set is frozen before final threshold tuning.

```text
12 standard positive cases
12 false-operational-match cases
 8 no-precedent cases
 4 conflicting-precedent cases
-----------------------------
36 total held-out cases
```

No changes to:

- accepted precedent IDs;
- unsafe precedent IDs;
- expected procedure IDs;
- expected missing facts;
- expected decision state;
- safety thresholds;

may be made after the held-out set is frozen unless a documented dataset defect is discovered. A defect fix requires a changelog entry and rerun of all pipelines.

### 8.5 Record origins

Every record must contain:

```yaml
record_origin: source_grounded | controlled_variant | synthetic_no_precedent
```

Every source-grounded record must contain:

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

### 8.6 Incident-card schema

```yaml
incident_id: INC-001
title: string
record_origin: source_grounded | controlled_variant | synthetic_no_precedent
service: enum
component: enum
region: enum | unknown
severity: sev_1 | sev_2 | sev_3 | sev_4
started_after_change: boolean | unknown
change_context: deployment | migration | feature_flag | configuration | dependency | none | unknown
symptoms:
  - enum
observability_signals:
  - enum
failure_mechanism: enum
mitigation_summary: string
recovery_state: recovered | partially_recovered | unresolved | unknown
timeline_summary: string
linked_procedure_ids:
  - RB-001
safe_procedure_ids:
  - RB-001
unsafe_procedure_ids:
  - RB-004
required_verification_facts:
  - enum
narrative_safe: string
provenance: object
```

### 8.7 Procedure/runbook schema

Procedures must be called **Candidate Investigation Procedures**, not “recommended runbooks.”

```yaml
procedure_id: RB-001
title: string
version: string
status: current | stale | retired
applicable_incident_families:
  - queue_backlog_consumer_failure
not_applicable_when:
  - cache_stampede
verification_prerequisites:
  - consumer_error_rate
  - worker_deployment_version
safe_investigation_steps:
  - inspect...
  - compare...
unsafe_or_out_of_scope_actions:
  - do_not_execute_remediation
last_reviewed_at: YYYY-MM-DD
owner_role: platform_engineering
```

### 8.8 Strict data gates

#### Data Gate A — provenance
Every record must have provenance or be explicitly labeled controlled/synthetic.

#### Data Gate B — label completeness
Every final evaluation case must define acceptable precedents, unsafe precedents, expected state, and required facts.

#### Data Gate C — separation
No held-out case can be an exact rewrite of a corpus incident or calibration query.

#### Data Gate D — anti-leakage
No pipeline prompt/profile description may directly contain `incident_id`, `failure_mechanism`, `safe_procedure_ids`, or holdout labels.

#### Data Gate E — privacy
No raw private company data, credentials, customer IDs, internal hostnames, IPs, or sensitive operational material may enter the repository.

---

## 9. User workflow and core product behavior

### 9.1 Intake

The responder supplies:

```yaml
service: optional enum
component: optional enum
region: optional enum
severity: optional enum
started_after_change: optional boolean
what_changed: optional short text
symptoms: optional short list
what_has_been_tried: optional short text
current_state: optional enum
free_text_summary: optional short text
```

Input is intentionally short. The product must not demand a long incident form during triage.

### 9.2 Intake safety behavior

Before external inference:

1. validate shape and enum values;
2. reject or redact obvious secrets/PII patterns;
3. cap input length;
4. assign `trace_id`;
5. prefer explicit structured user fields over model-extracted candidates;
6. record only safe metadata in trace logs.

### 9.3 Core flow

```text
safe intake
  -> validation and redaction
  -> candidate extraction
  -> canonicalization
  -> IncidentFingerprint validation
  -> broad candidate retrieval
  -> rerank candidate incidents
  -> deterministic safety policy
  -> procedure eligibility filter
  -> typed EvidencePacket
```

### 9.4 User-visible output

The UI/CLI must lead with the decision state, not a confidence score.

Example:

```text
Decision: MISSING CRITICAL FACTS
Human review: Required

Candidate precedent:
INC-014: Queue backlog after worker deployment

Why it may be relevant:
- deployment-related onset
- queue backlog
- partial recovery after rollback

Why it may not apply:
- no confirmed worker rejection or consumer-error signal

Verify before inspecting the procedure:
- consumer error rate
- worker deployment version

Candidate investigation procedure:
RB-002: Queue Backlog After Consumer Failure
Status: Current
```

### 9.5 Forbidden output language

The system must not say:

- “The root cause is…”
- “Use this runbook now.”
- “Restart…”
- “Rollback…”
- “This will resolve the incident.”
- “The incident is caused by…”
- “Confidence: 96%, therefore…”

### 9.6 Permitted output language

- “Candidate precedent”
- “Candidate investigation procedure”
- “Why it may be relevant”
- “Why it may not apply”
- “Evidence is insufficient”
- “Conflicting historical precedent”
- “Verify before using”
- “Human review required”
- “Semantic retrieval currently degraded”

---

## 10. Decision-state contract and precedence

### 10.1 Exactly five decision states

```python
class EvidenceDecision(str, Enum):
    EVIDENCE_FOUND = "evidence_found"
    EVIDENCE_FOUND_WITH_CONFLICT = "evidence_found_with_conflict"
    MISSING_CRITICAL_FACTS = "missing_critical_facts"
    INSUFFICIENT_PRECEDENT = "insufficient_precedent"
    PROVIDER_DEGRADED = "provider_degraded"
```

### 10.2 State definitions

| State | Meaning | Required behavior |
|---|---|---|
| `evidence_found` | A compatible precedent and eligible procedure are supported by sufficient evidence. | Surface up to three precedents and eligible procedure(s), with caveats. |
| `evidence_found_with_conflict` | Multiple plausible precedents imply materially different investigation paths. | Surface competing evidence; no preferred procedure; human review required. |
| `missing_critical_facts` | A plausible precedent exists but required verification facts are absent. | Surface limited candidate evidence; name smallest required facts; do not promote procedure as applicable. |
| `insufficient_precedent` | No credible compatible precedent exists. | Abstain; do not surface procedure as relevant; human review required. |
| `provider_degraded` | Semantic inference capability is unavailable, invalid, timed out, or exhausted. | State degradation explicitly; do not present semantic confidence; optional lexical candidates must be visibly labeled degraded. |

### 10.3 Decision precedence

1. `provider_degraded` if required semantic provider operation fails and no valid fallback policy is available.
2. `insufficient_precedent` if candidates fail compatibility/evidence thresholds.
3. `evidence_found_with_conflict` if multiple compatible candidates lead to incompatible procedure paths.
4. `missing_critical_facts` if a plausible candidate requires unknown verification facts.
5. `evidence_found` only when all applicability gates pass.

### 10.4 Strict decision-policy gate

No model output may directly set the final decision state. Final states are assigned only by deterministic application policy based on validated signals, candidate metadata, thresholds, procedure eligibility, and failure state.

---

## 11. Superlinked inference usage

### 11.1 Superlinked role

Superlinked SIE is the real local inference engine and first provider adapter. It is not the architecture.

Use SIE for exactly three capabilities:

| Stage | SIE primitive | Purpose |
|---|---|---|
| Offline corpus preparation | `extract` | Derive candidate operational signals from controlled historical narrative. |
| Offline corpus preparation | `encode` | Build embeddings for historical incident representations. |
| Live incident intake | `extract` | Derive candidate operational fingerprint from safe free-text intake. |
| Live candidate retrieval | `encode` | Embed validated current fingerprint for local semantic retrieval. |
| Live precision ranking | `score` | Rerank query/candidate incident pairs for operational relevance. |
| Model/pipeline evaluation | `extract`, `encode`, `score` | Compare controlled profiles/pipelines on fixed cases. |

### 11.2 Explicit non-use

SIE must not:

- define ground truth;
- label safe vs unsafe precedent;
- decide final decision state;
- select a procedure without deterministic eligibility checks;
- generate remediation instructions;
- decide severity;
- infer root cause as a fact;
- write final postmortems;
- access or log secrets.

### 11.3 Required pre-build provider spike

Before implementing real adapter-dependent features, run a 2–4 hour **local Docker SIE capability spike** to verify:

- Docker is installed and the local SIE container can start;
- the local base URL is reachable at `http://localhost:8080`;
- successful `extract` call through the typed adapter;
- successful `encode` call through the typed adapter;
- successful `score` call through the typed adapter;
- selected local profile/model identifiers;
- response shape;
- latency observation;
- timeout behavior;
- known error shapes;
- one invalid-input behavior;
- trace-safe logging behavior;
- that the API key is neither required nor logged for local Docker mode.

#### Provider Spike Gate

Proceed to live integration only if:

```text
local Docker SIE responds at the configured base URL
extract works through a typed adapter
encode works through a typed adapter
score works through a typed adapter
raw response does not leak outside adapter
error mapping is possible
latency is observed and recorded
```

If the spike fails because Docker, local SIE, model loading, or operation configuration is unavailable, do not invent SIE behavior. Implement the fake client and adapter skeleton, document the blocked local-provider validation, and do not claim real-SIE validation.

The absence of a managed endpoint URL is not a blocker for this project. Managed-hosted validation remains explicitly out of scope for the 50-hour initial build.

### 11.4 Provider profiles

Profiles must be configuration, not business logic.

```yaml
profile_id: incident-retrieval-v1
purpose: incident_retrieval
provider: superlinked
operation: encode
model_id: confirmed_during_spike
timeout_ms: 1500
max_retries: 1
fallback_profile_id: null
```

```yaml
profile_id: incident-rerank-v1
purpose: incident_reranking
provider: superlinked
operation: score
model_id: confirmed_during_spike
timeout_ms: 1500
max_retries: 0
fallback_profile_id: null
```

```yaml
profile_id: incident-extraction-v1
purpose: incident_signal_extraction
provider: superlinked
operation: extract
model_id: confirmed_during_spike
timeout_ms: 1500
max_retries: 0
fallback_profile_id: null
```

No model IDs may be hard-coded in the domain workflow.

---

## 12. Architecture and package boundaries

### 12.1 Architecture diagram

```text
CLI / minimal local web UI
  -> IncidentEvidenceService
      -> intake validation + redaction
      -> IncidentFingerprint canonicalizer
      -> SemanticInferenceClient protocol
          -> SuperlinkedSIEClient
              -> SIE SDK / local Docker endpoint (`http://localhost:8080` initially)
          -> FakeSemanticInferenceClient
      -> LocalIncidentRepository
      -> RetrievalPolicy
      -> ProcedureEligibilityPolicy
      -> EvidenceDecisionPolicy
      -> TraceRecorder
      -> EvalHarness
      -> PromotionGate
```

### 12.2 Required repository tree

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
  src/incident_precedent_harness/
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

### 12.3 Dependency rules

| Package | Can import | Must not import |
|---|---|---|
| `domain` | Pydantic, stdlib | SIE SDK, retrieval implementation, CLI |
| `inference/protocol.py` | Pydantic, domain models | SIE SDK |
| `inference/superlinked_client.py` | protocol, settings, SIE SDK | business decision policy |
| `retrieval` | protocol, repositories, domain models | SIE SDK directly |
| `decisions` | domain models, procedure metadata | SIE SDK, UI |
| `evals` | public service interface, fixtures | raw SIE SDK |
| `tests` | fake provider / fixtures | live provider by default |

### 12.4 Strict architecture gate

Search must confirm:

```text
SIE SDK imports appear only in inference/superlinked_client.py
```

No route, CLI, evaluation, policy, or domain module may import the SIE SDK or provider-specific exceptions.

---

## 13. Typed domain contracts

### 13.1 Core models

At minimum:

```text
IncidentIntake
SanitizedIncidentIntake
IncidentFingerprint
HistoricalIncident
CandidatePrecedent
CandidateProcedure
ProcedureEligibility
EvidenceDecision
EvidencePacket
InferenceRequest
InferenceResponse
InferenceTrace
InferenceFailure
EvalCase
EvalResult
PromotionGateResult
```

### 13.2 IncidentFingerprint requirements

```python
class IncidentFingerprint(BaseModel):
    service: ServiceName | None
    component: ComponentName | None
    region: RegionName | None
    severity: Severity | None
    symptoms: list[Symptom] = Field(default_factory=list)
    change_context: ChangeContext | None
    started_after_change: bool | None
    mitigation_attempted: list[MitigationAction] = Field(default_factory=list)
    recovery_state: RecoveryState | None
    dependencies: list[DependencyName] = Field(default_factory=list)
    unknown_fields: list[RequiredFact] = Field(default_factory=list)
    extraction_evidence: list[ExtractedSignal] = Field(default_factory=list)
```

### 13.3 EvidencePacket requirements

```python
class EvidencePacket(BaseModel):
    trace_id: UUID
    decision: EvidenceDecision
    human_review_required: bool
    candidate_precedents: list[CandidatePrecedent]
    candidate_procedures: list[CandidateProcedure]
    missing_critical_facts: list[RequiredFact]
    conflict_summary: str | None
    degraded_mode: bool
    safety_notes: list[str]
    provider_summary: ProviderSummary
```

### 13.4 Strict schema gate

- invalid enum values reject safely;
- model outputs become typed contracts before downstream use;
- unknown extraction values are preserved as unknown or discarded with reason;
- no generic `dict[str, Any]` crosses core interfaces;
- no blanket `except`.

---

## 14. Provider boundary and failure behavior

### 14.1 Protocol

The domain depends on a provider-neutral protocol resembling:

```python
class SemanticInferenceClient(Protocol):
    def extract_incident_signals(
        self,
        request: IncidentExtractionRequest,
    ) -> IncidentExtractionResponse: ...

    def encode_incident_texts(
        self,
        request: EmbeddingRequest,
    ) -> EmbeddingResponse: ...

    def score_incident_candidates(
        self,
        request: CandidateScoringRequest,
    ) -> CandidateScoringResponse: ...
```

### 14.2 Typed provider failures

```text
provider_unavailable
provider_timeout
model_not_ready
unsupported_capability
invalid_provider_response
input_limit_exceeded
rate_limited
retry_exhausted
```

### 14.3 Degraded-mode policy

If semantic inference fails:

1. return `provider_degraded`;
2. mark `human_review_required = true`;
3. do not emit semantic confidence or normal decision language;
4. optional lexical candidate search may run only if visibly labeled as degraded;
5. never silently replace semantic retrieval with lexical retrieval.

### 14.4 Provider failure gate

All simulated provider failures must yield a typed safe result. No raw stack trace, provider exception class, secret, or raw payload may be shown to the user or written to traces.

**Required target:** `provider_failure_safe_resolution_rate = 100%` on deterministic failure tests.

---

## 15. Retrieval and evidence pipeline

### 15.1 Pipeline A — keyword baseline

```text
sanitized fingerprint text
  -> BM25 or simple lexical search over incident title + safe narrative + tags
  -> top K candidates
```

Purpose: a minimum baseline. It must be implemented before semantic pipeline work.

### 15.2 Pipeline B — dense retrieval

```text
validated fingerprint representation
  -> Superlinked encode
  -> cosine similarity against local incident embedding matrix
  -> top 12 candidates
```

Purpose: test broad semantic recall.

### 15.3 Pipeline C — dense retrieval plus reranking

```text
dense top 12
  -> Superlinked score(query, candidate)
  -> reordered candidates
```

Purpose: test precision improvement.

### 15.4 Pipeline D — full controlled pipeline

```text
structured intake + free text
  -> Superlinked extract
  -> canonicalize and validate fingerprint
  -> Superlinked encode
  -> retrieve top 12
  -> Superlinked score
  -> deterministic compatibility checks
  -> procedure eligibility checks
  -> missing-fact / conflict / abstention policy
  -> EvidencePacket
```

### 15.5 Candidate representation

Use controlled text format, not arbitrary raw narrative only:

```text
service=payments-api
component=webhook-worker
symptoms=http_5xx|queue_backlog|elevated_latency
change_context=deployment
mitigation=rollback
recovery_state=partial
narrative=...
```

### 15.6 Strict retrieval gate

Do not claim pipeline D is better unless held-out results show:

- stronger or non-inferior retrieval than simpler alternatives;
- no unsafe procedure surfacing;
- acceptable anti-anchoring rate;
- acceptable abstention;
- acceptable latency;
- safe provider failure.

---

## 16. Deterministic safety policy

### 16.1 Safe-precedent definition

A historical incident may be surfaced as a **candidate precedent** only when the deterministic policy finds enough support across applicable dimensions:

- service or component compatibility;
- primary failure-family compatibility;
- symptom pattern compatibility;
- change-context compatibility;
- recovery-state compatibility;
- procedure applicability;
- required verification facts;
- candidate score threshold;
- no explicit unsafe-precedent label.

### 16.2 Anti-anchoring policy

The system must:

- return no more than three candidate precedents;
- explain why each may be relevant;
- explain meaningful differences where known;
- never hide conflicting candidates;
- identify the smallest missing fact set;
- avoid a single “recommended fix”;
- show procedure as a candidate investigation artifact, not instruction;
- require human review for every output state except the display may also use it for evidence found.

### 16.3 Procedure eligibility policy

A procedure becomes visible only if:

```text
procedure status is current
AND incident family is listed as applicable
AND no non-applicable condition is triggered
AND required verification facts are present
AND no conflicting candidate requires a divergent procedure
AND selected precedent is not unsafe
```

If facts are missing, the procedure may be named only as:

```text
Potentially related procedure — verification required before use
```

### 16.4 Strict safety gate

Unsafe procedure surfacing must be zero across all held-out cases.

---

## 17. Evaluation design

### 17.1 Evaluation philosophy

The evaluation harness is a first-class product artifact.

A pipeline is not accepted merely because it “looks more useful.” It must be compared on fixed cases, with a baseline, intervention, scorecard, failure labels, trace review, and regression gate.

### 17.2 Evaluation dimensions

| Dimension | Meaning |
|---|---|
| Retrieval quality | Can the system find a compatible incident family? |
| Precision | Does the top candidate represent the right precedent? |
| Anti-anchoring safety | Does it avoid operationally incompatible lookalikes? |
| Procedure safety | Does it avoid surfacing inapplicable procedures? |
| Abstention quality | Does it refuse when no useful precedent exists? |
| Missing-fact quality | Does it ask for facts that matter? |
| Conflict handling | Does it show ambiguous precedent rather than force a choice? |
| Latency | Is the pipeline usable for triage? |
| Provider resilience | Does provider failure resolve safely? |
| Maintainability | Can a profile change be evaluated and blocked automatically? |

### 17.3 Required metrics

```text
incident_family_recall_at_5
correct_precedent_mrr
safe_precedent_top_1_rate
false_operational_match_rate
unsafe_procedure_surfacing_rate
no_precedent_abstention_accuracy
missing_fact_precision
conflict_state_accuracy
p50_latency_ms
p95_latency_ms
provider_failure_safe_resolution_rate
```

### 17.4 Held-out scorecard targets

These are initial non-negotiable target gates. Thresholds may be calibrated only during Phase 2 and must be frozen before held-out final tuning.

| Metric | Holdout denominator | Minimum gate |
|---|---:|---:|
| Incident-family Recall@5 | 12 standard positive cases | >= 10 / 12 |
| Correct-precedent MRR | 12 standard positive cases | Must exceed keyword baseline by >= 0.05 absolute OR complex pipeline is not promoted |
| Safe-precedent top-1 rate | 12 standard positive cases | >= 10 / 12 |
| False-operational-match rate | 12 false-friend cases | <= 1 / 12 |
| Unsafe procedure surfacing | all 36 cases | 0 / 36 |
| No-precedent abstention accuracy | 8 no-precedent cases | >= 7 / 8 |
| Conflict-state accuracy | 4 conflict cases | >= 3 / 4 |
| Missing-fact precision | applicable cases | >= 0.75, manually rubric-scored |
| Provider-failure safe resolution | deterministic simulations | 100% |
| p95 end-to-end latency | live profile runs | <= 1500 ms provisional budget; report actual observed result |

### 17.5 Metric veto rule

A candidate pipeline must be blocked if it:

- improves MRR but worsens false-operational-match rate above gate;
- surfaces any unsafe procedure;
- fails no-precedent abstention;
- fails provider-failure safe handling;
- exceeds latency budget without a documented, accepted trade-off;
- relies on undeclared fallback behavior.

### 17.6 LLM-as-judge limitation

Use deterministic labels and rubric-based human review wherever possible.

If an LLM-as-judge is used for any supplementary evidence-quality score:

- define the rubric;
- use it only as secondary evidence;
- retain supporting excerpts;
- manually spot-check every disagreement;
- do not use it as the sole pass/fail gate.

---

## 18. Failure taxonomy

### 18.1 Retrieval and decision failures

```text
retrieval_miss
false_operational_match
wrong_precedent_ranked_first
wrong_procedure_linked
unsafe_procedure_surfaced
missing_critical_incident_fact
insufficient_precedent
conflicting_precedent
overconfident_evidence_presentation
stale_procedure
```

### 18.2 Provider failures

```text
provider_unavailable
provider_timeout
model_not_ready
unsupported_capability
invalid_provider_response
input_limit_exceeded
rate_limited
retry_exhausted
fallback_used
```

### 18.3 Data failures

```text
missing_provenance
label_incomplete
holdout_leakage
schema_invalid
source_transform_unclear
```

### 18.4 Failure-gallery requirement

Final deliverable must include at least six short, sanitized failure gallery entries:

1. keyword miss;
2. dense false friend;
3. reranking improvement;
4. conflict case;
5. no-precedent abstention;
6. provider-degraded response.

Each entry contains:

```text
input summary
pipeline output
expected outcome
failure label
why it matters
final disposition
```

---

## 19. Traceability, privacy, and security controls

### 19.1 Trace fields

Traces must record safe metadata only:

```text
trace_id
run_id
timestamp
pipeline_id
profile_id
operation
candidate_count
selected_candidate_ids
decision_state
human_review_required
latency_ms
retry_count
provider_status
failure_label
fallback_used
redaction_applied
```

### 19.2 Must not be logged by default

```text
raw incident narrative
raw postmortem source text
raw provider request payload
raw provider response payload
API keys
authorization headers
secrets
customer identifiers
internal URLs
hostnames
IP addresses
full procedure text if it could be sensitive
```

### 19.3 Data boundary note

The project must document:

- which sanitized text is sent from the local Python application to the local Docker SIE server;
- which fields remain local;
- that the initial inference boundary is the developer machine, not a managed Superlinked endpoint;
- what trace metadata is retained;
- how long local artifacts would be retained in a real deployment;
- that the prototype uses fictional/synthetic source-grounded data only;
- that production customer deployment would require a separate data-processing, vendor-boundary, access-control, and retention design.

### 19.4 Privacy gate

Before final release:

- run no-sensitive-log tests;
- inspect sample trace files;
- inspect `.env.example`;
- scan repository for secrets;
- confirm public demo inputs contain no real incident data.

---

## 20. Promotion gate

### 20.1 Purpose

The promotion gate makes model/pipeline choice an executable engineering decision.

It answers:

> **Can this candidate profile/pipeline be used as the default incident-precedent retrieval configuration?**

### 20.2 Command

```text
python scripts/run_promotion_gate.py --candidate full_pipeline_v1
```

### 20.3 Required output

Machine-readable JSON and human-readable Markdown.

Example:

```text
INCIDENT EVIDENCE PROMOTION GATE
--------------------------------
Candidate: extract + dense retrieval + reranking
Held-out cases: 36

Incident-family Recall@5:          10/12   PASS
Correct precedent MRR:             0.81    PASS
Safe precedent top-1:              10/12   PASS
False operational matches:         1/12    PASS
Unsafe procedure surfacing:        0/36    PASS
No-precedent abstention:           7/8     PASS
Conflict state accuracy:           3/4     PASS
Provider failure safe resolution:  8/8     PASS
p95 latency:                       940 ms  PASS

DECISION: PROMOTE
```

### 20.4 Required blocked example

The repository must include at least one recorded blocked result:

```text
DECISION: BLOCK

Reason:
Dense retrieval improved correct-precedent MRR over keyword search,
but exceeded the false-operational-match threshold and failed
no-precedent abstention. It must not surface candidate procedures.
```

### 20.5 CI tiers

#### Tier 1 — deterministic, every code change

Runs with fake provider and fixtures:

- schema validation;
- policy tests;
- failure tests;
- procedure eligibility;
- metric calculations;
- promotion-gate logic;
- no-sensitive-log checks.

#### Tier 2 — manual real-provider profile promotion

Runs when changing SIE profile/model/configuration:

- real Superlinked extraction/encoding/scoring;
- held-out evaluation;
- live latency capture;
- promotion report artifact;
- manual trace inspection.

Do not make ordinary pull requests depend on local Docker availability or external inference availability.

### 20.6 Strict promotion gate

No profile/model configuration changes may be described as improved or default-worthy without a saved promotion report.

---

## 21. Testing requirements

### 21.1 Unit tests

At minimum:

- Pydantic input validation;
- redaction behavior;
- canonicalization;
- decision-state precedence;
- procedure eligibility;
- no unsafe procedure after missing facts;
- no unsafe procedure after conflict;
- provider error mapping;
- trace-safe serialization;
- metric calculation;
- promotion-gate pass/block behavior.

### 21.2 Contract tests

- Superlinked adapter returns validated application responses;
- raw SDK/provider objects do not escape adapter;
- fake client conforms to semantic inference protocol;
- malformed provider response maps to typed error.

### 21.3 Integration tests

- local dense index build;
- full pipeline using fake client;
- optional real-provider smoke only, separate from standard suite;
- held-out report generation.

### 21.4 Test gate

No phase is complete if tests only prove happy-path retrieval. At least one test must cover each decision state and each provider failure class.

---

## 22. Local interface and demo

### 22.1 Surface choice

Use **CLI-first**. A very small local web shell is optional only after core gates pass.

The primary demo should work with one command and one known sample input.

### 22.2 CLI requirements

```text
related-incidents triage --input examples/queue_backlog_after_deploy.yaml
```

Must render:

- decision state;
- candidate precedents;
- matching and non-matching reasons;
- missing facts;
- eligible procedure status;
- provider/degraded state;
- trace ID;
- optional link/path to safe trace and evaluation record.

### 22.3 Optional web shell

Allowed only if core work is complete:

- one intake panel;
- one evidence packet view;
- one trace/eval summary view;
- no authentication;
- no persistence;
- no dashboard sprawl.

### 22.4 Demo gate

The demo must show:

1. a blocked keyword baseline / weak pipeline;
2. a successful full-pipeline case;
3. a false-friend case;
4. an insufficient-precedent abstention;
5. a provider-degraded response.

---

## 23. Documentation and proof assets

### 23.1 README must answer in under five minutes

1. What problem is being isolated?
2. Why not build an incident-management platform?
3. What is the anti-anchoring risk?
4. What does Superlinked do versus application policy?
5. What data is used and what it does not represent?
6. How to run demo/evals/gate?
7. Which pipeline won and why?
8. What was blocked and why?
9. What are the limitations and non-claims?

### 23.2 Required documentation artifacts

- architecture diagram;
- ADRs;
- dataset constitution;
- source manifest;
- labeling guide;
- provider spike report;
- evaluation report;
- promotion report;
- failure gallery;
- demo script;
- privacy/data-boundary note;
- limitations and non-claims.

### 23.3 Buyer-facing one-paragraph explanation

> Related Incident Evidence is a production-shaped evaluation harness for historical incident retrieval. It tests whether structured incident extraction, semantic retrieval, and reranking can surface operationally compatible prior incidents and candidate investigation procedures without anchoring responders on unsafe lookalikes. The prototype blocks model/pipeline changes when retrieval quality, abstention, procedure safety, latency, or provider-failure behavior violates predefined gates.

---

## 24. Fifty-hour phased delivery plan

### Phase 0 — project framing and provider capability spike
**Budget:** 0–4 hours

#### Deliverables

- repository bootstrap;
- ADR-0001 product boundary;
- ADR-0002 provider boundary;
- `.env.example`;
- Superlinked provider spike;
- local Docker SIE start/stop runbook;
- local base-URL and no-secret configuration check;
- typed protocol skeleton;
- fake client skeleton;
- source manifest template.

#### Strict gate

Proceed only if:

```text
scope cuts are written
provider protocol exists
fake client exists
Superlinked extract/encode/score smoke behavior is proven OR
real-provider validation is explicitly documented as blocked
```

#### Kill conditions

- No confirmed SIE call contracts after 4 hours: do not build against imagined behavior.
- Scope expands to integrations or automation: cut immediately.

---

### Phase 1 — data constitution and corpus
**Budget:** 4–12 hours

#### Deliverables

- RelayOps topology;
- source manifest;
- 32 incident cards;
- 8–10 procedures;
- labeling guide;
- 12 calibration cases;
- 36 frozen held-out cases;
- schema validators.

#### Strict gate

Proceed only if:

```text
32/32 incident cards validate
all records have origin + provenance
8/8 families represented
all procedures have eligibility metadata
36/36 holdout cases have safe/unsafe labels and expected state
no raw public articles are committed
```

#### Kill conditions

- Corpus is generic LLM fiction without source grounding.
- No false-friend / no-precedent cases exist.
- Holdout labels are not frozen before pipeline tuning.

---

### Phase 2 — baseline retrieval and scoring harness
**Budget:** 12–20 hours

#### Deliverables

- keyword baseline;
- local incident repository;
- metrics implementation;
- calibration runner;
- first baseline report;
- trace schema and recorder.

#### Strict gate

Proceed only if:

```text
keyword baseline runs across all calibration cases
metrics report is generated
failure labels are recorded
all heldout cases remain untouched
```

#### Kill conditions

- No baseline report: do not start model integration.
- Evaluation cases are altered to flatter the baseline.

---

### Phase 3 — Superlinked adapter and full pipeline
**Budget:** 20–30 hours

#### Deliverables

- Superlinked adapter;
- live extract, encode, score operations;
- canonicalization;
- local vector matrix/index;
- reranking;
- fake adapter parity tests;
- provider error normalization.

#### Strict gate

Proceed only if:

```text
SIE SDK imports are isolated
full pipeline runs on calibration cases
provider failures map to typed error envelopes
raw provider payloads do not leak
canonicalized fingerprints validate
```

#### Kill conditions

- Provider-specific types leak into policies/evals.
- Reranking bypasses deterministic decision policy.
- No actual SIE operations are proven after credits/access are available.

---

### Phase 4 — safety policy, procedure eligibility, and degraded mode
**Budget:** 30–37 hours

#### Deliverables

- five decision states;
- state precedence;
- anti-anchoring policy;
- procedure eligibility;
- missing-fact logic;
- conflict logic;
- degraded-mode behavior;
- safety tests.

#### Strict gate

Proceed only if:

```text
every decision state has tests
unsafe procedure surfacing is zero on calibration data
provider degraded state is explicit
false-friend cases cannot be silently presented as normal evidence
```

#### Kill conditions

- A model score directly determines a final state.
- Procedures are shown as instructions.
- Semantic failures silently become normal lexical results.

---

### Phase 5 — held-out evaluation and promotion gate
**Budget:** 37–44 hours

#### Deliverables

- all four pipeline reports;
- held-out evaluation run;
- trace review;
- promotion-gate command;
- promoted and blocked report examples;
- failure gallery.

#### Strict gate

Proceed only if:

```text
heldout set is run without post-hoc relabeling
metrics and safety gates are reported
at least one pipeline is blocked for a real reason
winning pipeline is selected by the gate, not assumed
```

#### Kill conditions

- More complex pipeline is described as better despite safety-gate failure.
- Holdout cases are altered to make a preferred profile pass.
- No blocked example exists.

---

### Phase 6 — local demo, documentation, and final inspection
**Budget:** 44–50 hours

#### Deliverables

- CLI demo;
- README;
- architecture diagram;
- final report;
- demo script;
- privacy review;
- source/license notice;
- repository cleanup.

#### Strict final gate

The project is complete only if a skeptical reviewer can:

```text
clone it
run the deterministic tests
run the demo
inspect the source-grounded data posture
see the baseline vs candidate comparison
see a blocked pipeline
see an abstention case
see a provider-degraded case
understand what has not been proven
```

#### Kill conditions

- Polishing UI displaces evaluation/reporting work.
- README claims production readiness or incident resolution improvement.
- Demo has no visible failure/abstention story.

---

## 25. Time allocation and cut order

### 25.1 Time budget

| Workstream | Hours |
|---|---:|
| Framing + provider spike | 4 |
| Data constitution + corpus | 8 |
| Baselines + evaluation harness | 8 |
| Superlinked adapter + full pipeline | 10 |
| Safety policy + failure handling | 7 |
| Held-out evaluation + promotion gate | 7 |
| Demo + docs + final inspection | 6 |
| **Total** | **50** |

### 25.2 First features to cut if late

1. optional local web UI;
2. extra model profile comparisons beyond one confirmed profile per operation;
3. optional real-log excerpts;
4. extra incident records beyond 32;
5. decorative diagrams/screenshots;
6. non-essential procedure detail.

### 25.3 Features that may never be cut

- data constitution;
- held-out evaluation;
- unsafe false-match cases;
- abstention;
- provider boundary;
- provider failures;
- promotion gate;
- clear non-claims.

---

## 26. Risk register

| Risk | Likelihood | Impact | Control |
|---|---|---|---|
| Local Docker SIE or model loading does not work immediately | Medium | High | 2–4 hour local capability spike; fake client remains test seam; do not invent validation. Managed access is not required for the initial build. |
| Corpus feels fake | Medium | High | Source manifest, coherent RelayOps topology, human authored mechanisms, controlled variants. |
| Dataset leakage | Medium | High | Frozen holdout, separate calibration folder, source transformation notes. |
| Dense retrieval looks good but is operationally unsafe | High | High | False-friend cases, anti-anchoring metric, procedure safety gate. |
| Reranking adds latency without safety improvement | Medium | Medium | Promotion gate requires documented benefit; reject profile if it fails. |
| Scope creep into incident platform features | High | High | Explicit out-of-scope list and 90-minute scope kill rule. |
| Public source licensing/attribution is mishandled | Medium | Medium | Source manifest, NOTICE file, copied-text prohibition, preserve license attribution where applicable. |
| Sensitive text leaks into traces | Medium | High | Synthetic data only, redaction, no raw payload logging, tests. |
| Demo overclaims | Medium | High | Mandatory non-claims section and demo script wording. |
| Small holdout produces unstable metrics | Medium | Medium | Report raw counts, case groups, confidence limitations; do not make broad claims. |

---

## 27. Acceptance criteria

### 27.1 Functional acceptance

- Intake validates structured fields and optional free text.
- Full pipeline produces one of five typed decision states.
- Candidate precedents show relevance and caution.
- Procedure visibility respects eligibility policy.
- Provider failure becomes explicit degraded mode.
- CLI demo runs locally.

### 27.2 Architecture acceptance

- Superlinked SDK only exists inside adapter.
- Tests run with fake inference client.
- Core policy/eval code is provider-neutral.
- Pydantic validates all model boundary outputs.
- No raw provider exceptions leak upward.

### 27.3 Evaluation acceptance

- Four pipeline conditions are compared.
- Held-out set is frozen and runnable.
- False-friend, no-precedent, conflict, and positive cases exist.
- Promotion gate emits pass/block.
- One candidate pipeline is documented as blocked.
- Safety metrics can veto retrieval metric gains.

### 27.4 Privacy acceptance

- Synthetic/source-grounded data only.
- No secrets/PII/raw payloads in traces.
- Source provenance documented.
- No-sensitive-log tests pass.
- Vendor/data boundary is documented.

### 27.5 Documentation acceptance

- README explains project in under five minutes.
- Architecture and ADRs exist.
- Data constitution exists.
- Final report has baseline, intervention, metrics, failure examples, residual risk, and non-claims.
- Demo script contains both successful and blocked/abstention examples.

---

## 28. Final reviewer test

A skeptical staff engineer should be able to say:

> This is not trying to replace an incident platform. It isolates a difficult reliability decision: whether historical incident evidence is comparable enough to surface. The author separated inference from policy, used a real provider behind an adapter, built data and evaluation assets deliberately, measured dangerous false matches, tested abstention and provider degradation, and made model/pipeline promotion conditional on safety as well as retrieval quality.

A skeptical CTO should be able to say:

> This person understands that AI operational tooling should support evidence gathering, not make ungrounded production decisions.

A Superlinked engineer should be able to say:

> This person used extract, encode, and score as separable inference primitives, made profile choice testable, and did not couple the application to provider-specific SDK behavior.

---

## 29. Source and attribution register

This PRD requires a versioned `docs/data/source-manifest.md` with the exact records used. Initial approved source categories:

1. **Superlinked SIE documentation**  
   Use for official operation/capability references: `extract`, `encode`, `score`, adapters, examples, and performance evaluation.  
   - https://superlinked.com/docs  
   - https://superlinked.com/docs/engine/adapters  
   - https://superlinked.com/docs/score  
   - https://superlinked.com/docs/evals/performance  
   - https://superlinked.com/docs/examples

2. **PostHog public postmortems**  
   Public historical source. Repository license must be retained where applicable. Use source material selectively and do not imply RelayOps incidents occurred at PostHog.  
   - https://github.com/PostHog/post-mortems  
   - https://github.com/PostHog/post-mortems/blob/main/LICENSE

3. **Official public incident write-ups**  
   Use as cited reference material only. Derive and document general mechanisms; do not copy full text into repository.  
   - Cloudflare postmortems: https://blog.cloudflare.com/tag/post-mortem/  
   - GitHub incident analyses: official GitHub Blog incident analysis pages  
   - OpenAI status incident write-ups: https://status.openai.com/

4. **Rootly AI Labs logs dataset (optional, limited use)**  
   Apache-2.0 dataset of real production logs. Use only reviewed, small excerpts as secondary noisy evidence; do not turn it into a root-cause dataset.  
   - https://github.com/Rootly-AI-Labs/logs-dataset

5. **Rootly SRE Skills Bench (methodology reference only)**  
   Apache-2.0 benchmark for SRE-task evaluation. Do not present it as the project’s corpus.  
   - https://github.com/Rootly-AI-Labs/SRE-skills-bench

### Attribution rule

Every source-grounded record must point to the source manifest. The final README must state:

> The incident archive is a fictional, source-grounded dataset designed for reproducible evaluation. It derives operational mechanisms and patterns from public materials but does not represent any organization’s private incident history, production environment, or operational advice.

---

## 30. Repository bootstrap and local Docker orientation

### 29.1 Repository location

```text
GitHub: https://github.com/kablewithak/incident-precedent-retrieval-harness
Local target:
C:\Users\kabom\Documents\Machine Learning\Machine Learning Workspace\incident-precedent-retrieval-harness
```

### 29.2 Initial local SIE command

The local SIE process is started from PowerShell in a separate terminal window:

```powershell
docker run --rm -p 8080:8080 ghcr.io/superlinked/sie-server:latest-cpu-default
```

This is an initial local-development command, not proof that all configured models are ready. The provider spike must separately validate `extract`, `encode`, and `score` through the application adapter.

### 29.3 Initial repository verification

Before beginning the first implementation slice, capture fresh evidence from the intended local repository folder:

```powershell
Set-Location "C:\Users\kabom\Documents\Machine Learning\Machine Learning Workspace\incident-precedent-retrieval-harness"

git status
git remote -v
Get-Location
```

Run `git log -1 --oneline` only after the repository has its first commit.

### 29.4 Environment configuration rule

`.env.example` must contain placeholders only:

```dotenv
SIE_BASE_URL=http://localhost:8080
SIE_API_KEY=
SIE_TIMEOUT_SECONDS=30
```

The real Superlinked key must not be added to `.env.example`, source files, test fixtures, terminal screenshots, handovers, PR descriptions, trace logs, or any committed artifact.

### 29.5 Future managed-endpoint seam

The adapter may later accept a non-local `SIE_BASE_URL` and optional `SIE_API_KEY` through settings. That is a compatibility seam only. The initial deliverable is evaluated against local Docker SIE and must not claim managed-hosted validation.

## 31. Instruction to the next implementation assistant

Treat this PRD as binding unless a change is explicitly approved and documented.

Before writing code:

1. perform the provider capability spike;
2. create the data constitution and schemas;
3. freeze the holdout plan;
4. create the repository and dependency boundaries;
5. implement baselines before the full pipeline;
6. implement tests beside each behavior;
7. do not create a UI before the promotion gate is functional;
8. do not make capability claims without evidence.

For every behavior change, preserve:

```text
boundary
-> fixed cases
-> baseline
-> intervention
-> score
-> failure labels
-> trace review
-> regression decision
-> non-claim
```

Final instruction:

> **Build the harness first. The model is a component, not the product.**

---
