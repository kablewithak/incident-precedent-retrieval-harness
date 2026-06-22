# Incident Precedent Retrieval Harness — Sprint Context

Paste this file at the beginning of a new working session **before** the stable Context Bundle, the latest filled handover, and the current Session Brief.

This file is the **project-specific operating constitution**. It defines how work on this repository must be approached. It is stable unless the product thesis, scope, or engineering doctrine materially changes.

It does not replace the system prompt.

```text
SPRINT_CONTEXT.md = how to think and operate.
CONTEXT_BUNDLE.md = stable project facts and confirmed paths.
Filled handover = current verified state and phase evidence.
SESSION_BRIEF.md = today’s mission.
Live terminal output = final authority for current Git/runtime facts.
```

---

## 1. Project Identity

**Repository:** `incident-precedent-retrieval-harness`  
**Public label:** Related Incident Evidence  
**GitHub:** `https://github.com/kablewithak/incident-precedent-retrieval-harness`

**North Star**

> Build a production-shaped, source-grounded, evaluated incident-precedent retrieval harness that proves whether structured incident extraction, semantic retrieval, and reranking can surface useful historical incident evidence without causing unsafe operational anchoring.

**Technical thesis**

> The quality of an incident-evidence system is not proven by retrieving a plausible historical incident. It is proven by surfacing evidence safely, abstaining when precedent is weak, exposing conflict and missing facts, and blocking regressions through fixed evaluation.

**Target maturity claim**

```text
Production-shaped.
Locally validated.
Source-grounded synthetic-data validated.

Not production incident-response tested.
Not customer-data tested.
Not integrated with live incident systems.
Not authorised for automatic remediation.
```

---

## 2. Product Promise and Strict Non-Goals

### Product promise

Help an on-call engineer during early incident triage find **candidate historical precedents** and **candidate investigation procedures**, while clearly stating:

- why each result may match;
- why it may not apply;
- what facts must be verified before acting;
- when evidence is missing, conflicting, insufficient, or degraded.

### Strict non-goals

This repository must **not** become:

- a PagerDuty, Datadog, Rootly, FireHydrant, incident.io, or BigPanda competitor;
- an alerting, paging, scheduling, status-page, or incident-command product;
- a Slack/Teams bot;
- a live telemetry, logs, metrics, traces, or observability integration;
- a root-cause engine;
- an autonomous SRE agent;
- an action executor, remediation tool, auto-rollback tool, or deployment controller;
- a generic RAG chatbot or general incident search portal;
- a cloud-deployment exercise;
- a hosted vector-database demonstration;
- a multi-agent system.

No scope addition is acceptable unless it directly strengthens at least one of:

```text
provider-boundary proof
source-grounded corpus integrity
safe-precedent retrieval
anti-anchoring evaluation
abstention / missing-facts behaviour
promotion-gate evidence
portfolio communication
```

---

## 3. Primary User and Workflow Position

**Primary user:** a backend, platform, or product engineer on call at a growth-stage B2B SaaS company.

**Workflow position:**

```text
Alert acknowledged
→ responder checks current telemetry and recent changes
→ responder needs historical context
→ Related Incident Evidence surfaces candidate precedent
→ responder verifies evidence and chooses next investigation step
```

The system supports human decision-making. It must not claim to diagnose root cause or choose a remediation path.

---

## 4. Safety Doctrine: Prevent Unsafe Operational Anchoring

The main safety risk is a **false operational match**:

> A plausible but materially incompatible historical incident nudges the responder toward the wrong diagnosis, procedure, or mitigation.

This risk is more important than raw semantic similarity.

### Required behaviour

The system must:

- return candidate precedents, not “the answer”;
- return one to three candidates when evidence exists, not a single “recommended fix”;
- show match reasons;
- show mismatch, conflict, or applicability caveats;
- show required verification facts;
- identify missing critical facts;
- abstain when precedent is insufficient;
- label provider-degraded behaviour honestly;
- never present a historical event as proof of current root cause;
- never instruct automated remediation.

### Typed decision states

```text
evidence_found
evidence_found_with_conflict
missing_critical_facts
insufficient_precedent
provider_degraded
```

### Procedure language

Use **candidate investigation procedure**, not “run this now”, “recommended fix”, or “root cause”.

---

## 5. Architecture Doctrine

### Core separation

```text
domain workflow
→ provider-neutral semantic inference protocol
→ Superlinked SIE adapter
→ validated provider response
→ deterministic evidence policy
→ typed EvidencePacket
```

**Superlinked/SIE is an inference provider, not the architecture.**

### Provider boundary

Core domain, evaluation, reporting, and policy code must not import Superlinked SDK classes, response objects, or exception types.

The adapter alone owns:

- SIE SDK or HTTP client use;
- base URL configuration;
- optional API key configuration;
- model/profile configuration;
- timeout and retry limits;
- raw provider response parsing;
- provider error normalization;
- provider latency capture;
- trace-safe provider events.

Tests must use deterministic fake provider clients wherever live SIE is not specifically being validated.

### Initial inference mode

```text
Local Docker SIE.
SIE_BASE_URL=http://localhost:8080
SIE_API_KEY=
```

The supplied Superlinked API key must never be committed, logged, pasted into docs, or treated as proof of hosted-provider access.

A managed SIE claim requires a real base URL and successful validation against it. API key alone does not prove managed access.

### Intended inference flow

```text
Structured intake + optional free text
→ validation + redaction
→ optional extraction to candidate operational signals
→ deterministic canonicalization
→ Pydantic IncidentFingerprint validation
→ local dense candidate retrieval
→ reranking
→ deterministic anti-anchoring evidence policy
→ typed EvidencePacket
```

---

## 6. Dataset and Provenance Constitution

### Dataset posture

Use a coherent, fictional SaaS environment and a **source-grounded synthetic incident archive**.

Public incident material may inform mechanisms, timelines, uncertainty, and terminology. It must not be copied wholesale unless the licence explicitly permits it.

Do not use:

- private incident records;
- customer tickets;
- Slack/Teams exports;
- production logs;
- infrastructure identifiers;
- credentials;
- private postmortems;
- raw data that cannot be safely redistributed.

### Planned scope

```text
32 historical incident cards
8 incident families
8–10 candidate investigation procedures
36 fixed evaluation cases
12 false-operational-match cases
8 no-precedent cases
4 conflicting-precedent cases
6–8 provider-failure simulations
```

### Incident families

```text
1. Deployment-related worker crash loop
2. Queue backlog caused by consumer failure
3. Database migration lock contention
4. Connection-pool exhaustion
5. Cache stampede / invalidation failure
6. Third-party webhook or provider degradation
7. Feature-flag rollout regression
8. Rate-limit or authentication configuration regression
```

### Required provenance controls

Every source-grounded record needs:

- source record identifier;
- source name and URL;
- publication date where known;
- usage mode: licensed source / cited reference / manually authored variant;
- transformation note;
- human-verification status.

Every evaluation case needs:

- expected decision state;
- acceptable precedent IDs;
- unsafe precedent IDs;
- expected candidate procedure IDs where relevant;
- expected missing facts;
- failure-label intent.

### Eval integrity rules

```text
Corpus / development calibration / held-out test data are separated.
Held-out cases are never used to tune thresholds, prompts, labels,
ranking rules, canonicalisation, or selection policy.
Any new hard case records why it was accepted or rejected.
```

---

## 7. Evaluation and Promotion-Gate Doctrine

### Pipeline comparisons

Evaluate:

```text
1. Keyword retrieval baseline
2. Dense retrieval baseline
3. Dense retrieval + reranking
4. Extraction + dense retrieval + reranking + safety policy
```

### Required metrics

```text
incident_family_recall_at_5
correct_precedent_mrr
safe_precedent_top_1_rate
false_operational_match_rate
candidate_procedure_top_1_relevance
unsafe_procedure_surfacing_rate
no_precedent_abstention_accuracy
missing_fact_precision
p50_pipeline_latency_ms
p95_pipeline_latency_ms
provider_failure_safe_resolution_rate
```

### Promotion rule

Do not promote a configuration simply because MRR improves.

A configuration is promotable only when the frozen promotion gate confirms that relevance, anti-anchoring safety, abstention behaviour, procedure safety, latency, and provider-failure resolution remain within accepted thresholds.

Thresholds must be calibrated against the baseline, explicitly recorded, then frozen for the evaluated release.

### CI posture

```text
Deterministic fake-provider evaluation:
runs in normal local/CI tests.

Live local-Docker SIE smoke / profile validation:
runs intentionally, records explicit evidence, and does not become
a hidden dependency of every test run.
```

---

## 8. Technical Operating Defaults

Use:

- Python 3.11+;
- type hints;
- Pydantic v2;
- pytest;
- JSON-safe structured logs;
- `trace_id` and `run_id` where useful;
- typed error envelopes;
- environment-based settings;
- deterministic fake clients;
- local-first scripts and tests;
- full-file replacements for code changes unless the user asks for a patch.

Do not use vague dictionaries at application boundaries.

Use:

- explicit enums;
- refusal/abstention states;
- validation errors;
- retry limits;
- timeout behaviour;
- provider error taxonomy;
- trace fields;
- data minimization;
- redaction before any logging or provider call where needed.

Use FastAPI only if an API becomes necessary. A CLI or minimal local view is sufficient for the 50-hour scope.

---

## 9. Privacy, Security, and Logging Rules

Engineering controls should align with POPIA, GDPR, and GLBA principles without claiming legal advice.

Defaults:

- data minimization;
- input classification;
- redact potential PII/secrets before logging;
- no raw incident narratives in ordinary logs;
- no raw source documents in ordinary logs;
- no API keys, tokens, headers, or secrets in logs;
- no hard-coded credentials;
- configurable retention/TTL design notes where artifacts are retained;
- clear vendor-boundary notes;
- local environment separation.

For every external/provider interaction, preserve the question:

> What data leaves the application boundary, why, and what is retained?

---

## 10. 50-Hour Delivery Discipline

```text
0–4 hours: local-Docker SIE capability spike + provider-boundary ADR
4–12 hours: source manifest, corpus, candidate procedures, fixed eval split
12–20 hours: keyword and dense baselines
20–30 hours: SIE extract / encode / score adapter
30–37 hours: anti-anchoring policy, abstention, missing facts, provider failures
37–44 hours: eval harness, reports, failure gallery, promotion gate
44–48 hours: minimal CLI or local review surface + safe traces
48–50 hours: README, architecture diagram, demo script, cleanup
```

The active handover must track:

```text
hours_spent
hours_remaining
current_phase
current_phase_gate
scope_removed
scope_risk
```

Prefer scope reduction over late-stage infrastructure addition.

---

## 11. GitOps and File-Delivery Preferences

### Working style

The user works in Windows PowerShell and VS Code, one repository slice at a time.

For implementation work:

```text
1. Confirm branch/current state from user-provided terminal output.
2. Create needed folders first.
3. Provide full-file replacements or a ZIP for many files.
4. State exact target paths.
5. Run targeted validation when behaviour changes.
6. Show git status before staging.
7. git add exact paths.
8. Show git status after staging.
9. Semantic commit.
10. Push branch.
11. Provide a clean PR description.
12. Provide one complete after-merge sync/delete PowerShell block.
13. Confirm main is clean before the next slice.
```

### PowerShell preference

Do not repeat `Set-Location` if the user is already in the correct repo. Use it only when a new terminal tab, parent directory, or different repository makes location ambiguous.

### File delivery preference

- One or few generated files: individual downloads with exact final filenames.
- More than two replacement/generated files: ZIP plus PowerShell extraction/copy commands.
- Full-file replacements, not patches, by default.
- Download filename must match final repository filename.
- Do not use Downloads as a staging directory unless the workflow is specifically ZIP-based.
- For docs-only slices, `git status` is normally sufficient; do not add artificial tests.

### Validation preference

- One pytest command per line.
- Tests before Git commands.
- No install command unless dependencies/package configuration changed or environment setup is stale.
- Current terminal output is evidence; do not make the user repeat it.
- Do not invent branch names, Git status, test results, or commits.

### Git cleanup preference

When Git commands are provided for a branch slice, include the PR description and a single complete after-merge sync/delete PowerShell block in the same response. Verify merged status before deleting local or remote branches.

---

## 12. Handover Protocol

A filled handover is required at a meaningful phase boundary, not after every tiny file change.

Create or update a handover when one of these occurs:

- a strict phase gate passes or fails;
- a material ADR or safety decision is made;
- the data constitution or held-out split is frozen;
- the local-Docker SIE capability spike concludes;
- a baseline/report/promotion-gate result is generated;
- a PR is merged and `main` is clean;
- work pauses intentionally at a clean boundary.

The filled handover must contain **current facts only**:

- phase and hours;
- branch and verified Git state;
- current files/reports;
- validation evidence;
- corpus/eval freeze status;
- provider status;
- promotion-gate status;
- safety metrics or known absence of them;
- unresolved risks;
- next safe slice.

It must not duplicate the full stable Context Bundle.

---

## 13. Commercial Translation

This project supports the following offer directions:

```text
AI System Evaluation Audit
RAG Reliability Improvement Sprint
AI Reliability Pilot
AI Reliability Retainer
```

For each meaningful artifact, capture:

1. Buyer pain.
2. Failure mode.
3. Engineering cost or risk.
4. Evidence produced.
5. Residual risk.
6. Relevant offer.
7. Why a CTO pays for ongoing ownership.

Commercial language should focus on:

```text
reliability
unsafe retrieval
regression prevention
traceability
human review
engineering time saved
operational risk
evidence-based release decisions
```

Avoid:

```text
AI transformation
AI magic
autonomous incident resolution
production-grade without proof
```

---

## 14. Start-of-Session Rules

At the beginning of a working session, use the documents in this order:

```text
1. Incident_Precedent_Retrieval_Harness_SPRINT_CONTEXT.md
2. Incident_Precedent_Retrieval_Harness_CONTEXT_BUNDLE.md
3. Latest filled project handover
4. Current filled Incident_Precedent_Retrieval_Harness_SESSION_BRIEF.md
5. Latest terminal output, logs, screenshots, or test evidence
```

Resolve conflicts in this order:

```text
Live terminal/runtime evidence
→ latest filled handover
→ current session brief
→ context bundle
→ sprint context
```

Do not ask the user to repeat facts already supplied in those documents.

---

## 15. Final Instruction

Be strict.

Do not flatter the project into readiness.

Preserve the distinction:

```text
Production-shaped != production-ready.
Local Docker validation != hosted-provider access.
A health check != model-specific inference readiness.
A smoke test != retrieval reliability.
A passing unit suite != safe operational use.
Better MRR != safe promotion.
Synthetic-data validation != customer-data validation.
```

Build an inspectable system with typed contracts, source provenance, fixed evals, anti-anchoring controls, trace-safe failures, maintainable seams, and buyer-relevant proof.
