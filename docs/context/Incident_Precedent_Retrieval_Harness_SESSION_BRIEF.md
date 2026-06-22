# Incident Precedent Retrieval Harness — Session Brief

Paste this file **after** the project Sprint Context, stable Context Bundle, and latest filled handover at the beginning of each working session.

This file is the **current mission order**. Keep it short, current, and specific. Update it before each session.

```text
SPRINT_CONTEXT.md = how to operate.
CONTEXT_BUNDLE.md = stable facts.
Filled handover = verified current state.
SESSION_BRIEF.md = what happens in this session.
```

---

## 1. Session Identity

**Session date:**

```text

```

**Session mode**  
Choose one primary mode:

```text
Build / Debug-Refactor / Eval-Harness / RAG / Provider Spike /
Data Authoring / Documentation / Business Translation / Handover
```

Selected mode:

```text

```

**Primary objective:**

```text

```

**Expected assistant output:**

```text

```

Examples:

```text
branch → files → validation → GitOps
ADR → implementation → tests → GitOps
eval design → fixed cases → scoring → gate
debug reasoning → full-file fix → tests → GitOps
data constitution → manifests → split evidence
handover update
```

---

## 2. Current Phase and 50-Hour Budget

**Current PRD phase:**

```text

```

**Current strict phase gate:**

```text

```

**Gate status:**

```text
not_started / in_progress / passed / failed / blocked
```

**Hours spent:**

```text

```

**Hours remaining:**

```text

```

**Scope removed or deferred:**

```text

```

**Current scope risk:**

```text

```

---

## 3. Current Repository and Workspace Evidence

**Repository:**

```text
incident-precedent-retrieval-harness
```

**GitHub URL:**

```text
https://github.com/kablewithak/incident-precedent-retrieval-harness
```

**Local path:**

```text
C:\Users\kabom\Documents\Machine Learning\Machine Learning Workspace\incident-precedent-retrieval-harness
```

**Current branch:**

```text

```

**Latest known Git status:**

```text

```

**Latest known commit / PR state:**

```text

```

**Virtual environment / Python setup:**

```text

```

**Commands already verified as passing:**

```text

```

**Commands known to fail or remain blocked:**

```text

```

**Terminal output, logs, screenshots, or test evidence supplied this session:**

```text

```

---

## 4. Current Build Boundary

**Boundary being changed or evaluated:**

```text

```

Examples:

```text
Pydantic incident intake
source manifest schema
provider-neutral inference protocol
local Docker SIE client adapter
canonicalisation
local retrieval baseline
reranking
anti-anchoring policy
EvidencePacket decision state
eval scorer
promotion gate
safe trace event
CLI review surface
```

**Expected behaviour:**

```text

```

**Observed behaviour or current blocker:**

```text

```

**Invariants that must remain true:**

```text

```

---

## 5. Current Inference / Provider Status

**Active inference mode:**

```text
fake client / local Docker SIE / managed SIE (only if real URL is verified)
```

**SIE base URL:**

```text

```

**API-key handling:**

```text
not required locally / configured privately / not verified / other
```

**Model or profile being tested:**

```text

```

**Provider capabilities currently verified:**

```text
health / readiness / extract / encode / score / typed failure normalisation
```

**Provider capability not yet verified:**

```text

```

**No-hosted-access claim check:**

```text
Confirm whether any managed-hosted inference claim is prohibited because
only an API key, rather than a verified endpoint URL, is available.
```

---

## 6. Dataset and Evaluation State

**Dataset stage:**

```text
not_started / source review / corpus authoring / dev calibration /
held-out test authoring / frozen / changed with justification
```

**Current corpus counts:**

```text
historical incident cards:
candidate investigation procedures:
source manifest records:
dev/calibration eval cases:
held-out eval cases:
false-operational-match cases:
no-precedent cases:
conflicting-precedent cases:
provider-failure cases:
```

**Provenance status:**

```text

```

**Held-out split status:**

```text
not created / separated / frozen / changed with documented reason
```

**Baseline currently available:**

```text
none / keyword / dense / dense + rerank / full pipeline
```

**Current candidate pipeline:**

```text

```

**Required scoring metrics for this session:**

```text

```

**Known failure labels:**

```text

```

---

## 7. Anti-Anchoring and Decision-State Check

**Expected decision state(s):**

```text
evidence_found / evidence_found_with_conflict /
missing_critical_facts / insufficient_precedent / provider_degraded
```

**False-operational-match risk in this slice:**

```text

```

**Required match caveats / verification facts:**

```text

```

**Unsafe procedure or response patterns to block:**

```text

```

**Abstention / escalation condition:**

```text

```

---

## 8. Files and Sources

**Files uploaded or pasted for this session:**

```text

```

**Files that are source of truth:**

```text

```

**Files that are stale, superseded, or untrusted:**

```text

```

**Exact target paths for files to create or replace:**

```text

```

**External source or licence constraints relevant to this session:**

```text

```

---

## 9. Constraints and Preferences

**Important constraints:**

```text
local-first
no cloud deployment unless explicitly requested
no live/private incident data
no raw sensitive content in logs
full-file replacements by default
no Superlinked SDK leakage outside adapter
no unmeasured claims of improvement
```

**Additional session-specific constraints:**

```text

```

**Preferred response format:**

```text

```

Examples:

```text
branch → files → validation → Git → PR → after-merge
diagnosis → divergence → full-file fix → tests → Git
eval design → fixed cases → baseline → intervention → gate
docs-only replacement → Git status → commit
```

**What must not be done in this session:**

```text

```

---

## 10. Acceptance Criteria and Non-Claims

**This session succeeds only when:**

```text

```

**Minimum verification required:**

```text

```

**Evidence artifact to create or update:**

```text

```

Examples:

```text
ADR
source manifest
dataset constitution
eval fixture set
baseline report
trace sample
promotion-gate report
failure gallery
README section
demo script
handover
```

**Non-claims for this session:**

```text

```

Examples:

```text
does not prove production incident-response readiness
does not prove customer-data readiness
does not prove hosted-provider access
does not prove real-world incident recall
does not prove safe remediation
does not prove scale or load behaviour
```

---

## 11. Commercial Translation

**Offer supported:**

```text
AI System Evaluation Audit /
RAG Reliability Improvement Sprint /
AI Reliability Pilot /
AI Reliability Retainer /
Other
```

**Buyer pain addressed:**

```text

```

**Failure mode or cost reduced:**

```text

```

**Proof asset created or improved:**

```text

```

**Why a CTO would pay for ongoing ownership:**

```text

```

---

## 12. Open Questions and Instruction to Assistant

**Questions to answer in this session:**

```text

```

**Missing evidence required before confident implementation/debugging claims:**

```text

```

**Known uncertainty:**

```text

```

**Instruction to assistant:**

```text
Use the project Sprint Context, stable Context Bundle, latest filled
handover, this Session Brief, and current terminal/runtime evidence together.

Do not invent Git state, branch names, test results, provider access,
source licences, dataset counts, implementation status, or production claims.

When implementation behaviour changes, define the boundary, fixed cases,
validation, trace fields, failure labels, and regression risk before
claiming improvement.

Use the smallest maintainable next slice. Preserve strict scope.
```
