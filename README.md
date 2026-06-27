# Related Incident Evidence

**An evaluated AI reliability harness for surfacing historical incident evidence without unsafe operational anchoring.**

> **Maturity:** locally validated + synthetic-data validated.
> **Not a claim:** deployed, customer-data tested, production-ready, or authorized to execute operational procedures.

Related Incident Evidence is a deliberately narrow system. It tests one operational safety question:

> When is a historical incident comparable enough to show as evidence to a responder, and when must the system preserve uncertainty or abstain?

It is **not** an incident-management platform, root-cause engine, remediation agent, alerting product, or generic RAG chatbot.

---

## Start here

An evaluator should read these in order:

1. [Evaluator guide](docs/submission/evaluator-start-here.md)
2. [Architecture and decision boundaries](docs/architecture/related-incident-evidence-architecture.md)
3. [Evidence map](docs/submission/evidence-map.md)
4. [Local demo script](docs/submission/demo-script.md)
5. [Maturity and non-claims](docs/submission/maturity-and-nonclaims.md)

The key result is intentionally mixed: the repository preserves a **blocked** frozen Tranche 01 promotion result rather than relabeling it as success. A separate representative-selection capability is locally integrated under narrow, display-only conditions; that does not erase the Tranche 01 baseline limitation.

---

## What the system does

```text
sanitized incident summary + structured verification facts
    -> deterministic keyword candidate path
    -> AntiAnchoringDecisionPolicy
    -> typed TriageEvidencePacket
    -> optional display-only representative refinement
    + advisory local Superlinked SIE evidence
    -> local reviewer interface
```

The deterministic policy is the authority for:

- top-level decision state;
- evidence admission;
- retained precedent IDs;
- missing critical facts;
- conflict handling;
- candidate procedure eligibility;
- provider-degraded behavior.

The local Superlinked SIE layer is **advisory only**. It cannot change the policy conclusion, missing facts, retained precedents, procedure posture, or execution authority.

Representative selection is narrower still: it may refine **which already policy-approved same-family precedent is displayed** only when validated selection intake is supplied and all activation preconditions hold. It never sets policy state or procedure posture.

---

## Decision states

| State | Meaning |
|---|---|
| `evidence_found` | Historical evidence is safe to review. A human still decides what to investigate. |
| `evidence_found_with_conflict` | More than one plausible explanation remains. The system preserves ambiguity. |
| `missing_critical_facts` | Plausible evidence exists, but key verification is incomplete. |
| `insufficient_precedent` | No grounded historical match is safe to show. |
| `provider_degraded` | Required evidence capability is unavailable. The system fails closed. |

Every path retains:

```text
procedure_execution_authorized = false
```

Candidate procedures are investigation material for a human. They never create authority to restart services, alter configuration, apply a runbook, or perform any production action.

---

## Run the local demo

The demo uses only the synthetic RelayOps corpus, a local dense index, local Docker SIE for provider-available scenarios, and loopback-only HTTP processes.

### 1. Validate the Python harness

```powershell
python -m pytest .\tests\unit
```

### 2. First-time frontend setup

```powershell
Push-Location .\apps\local-demo-ui

npm ci

npm run test

npm run build

Pop-Location
```

`node_modules/`, Vite caches, and `dist/` are generated local artifacts and must not be committed.

### 3. Start the Python boundary

Open a PowerShell window at repository root:

```powershell
docker start incident-sie

python .\scripts\run_local_submission_demo.py `
    --repository-root . `
    --port 8765
```

### 4. Start the React presentation layer

Open a second PowerShell window at repository root:

```powershell
Push-Location .\apps\local-demo-ui

npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

The React process proxies only `/api` to the local Python boundary on `127.0.0.1:8765`. It does not call retrieval, Superlinked SIE, policy, representative selection, or procedures directly.

For detailed controls and the four reviewer scenarios, read [the demo script](docs/submission/demo-script.md).

---

## Evaluation evidence

| Evidence asset | What it tested | Recorded result | What it does **not** prove |
|---|---|---|---|
| [Frozen typed-triage promotion gate](docs/reports/frozen-typed-triage-promotion-gate.md) | Typed packet parity against frozen Tranche 01 | **BLOCK**; `EVAL-110` remains unresolved | Promotion, production readiness, or semantic retriever authority |
| [EVAL-110 autopsy](docs/reports/eval-110-representative-selection-autopsy.md) | Cause of the frozen representative divergence | `UNDOCUMENTED_CONFLICT_RULE` | That a selector fix promotes the active policy |
| [Procedure-asymmetry comparison](docs/reports/procedure-asymmetry-fixture-comparison.md) | Whether procedure availability can alter isolated selector output | `COMPARISON_PASSED_ACTIVATION_BLOCKED` | Active-policy or end-to-end runtime safety |
| [Future-held-out Tranche 02 comparison](docs/reports/tranche-02-future-heldout-comparison.md) | Strict-dominance selector on frozen future-held-out cases | `comparison_passed_activation_blocked` | Policy integration, procedure safety, or production use |
| [Conditional selection activation readiness](docs/reports/conditional-representative-selection-activation-readiness.md) | Local typed integration controls | `implementation_validated_activation_blocked` | Retrieval improvement, customer-data safety, or production readiness |

The detailed source-to-claim map is in [Evidence map](docs/submission/evidence-map.md).

---

## Repository map

```text
src/incident_precedent_harness/
  decisions/                  deterministic policy and display refinement
  domain/                     typed incident and procedure contracts
  evaluation/                 governed evaluation and comparison harnesses
  retrieval/                  bounded candidate generation / adapter seams
  triage/                     typed TriageEvidencePacket boundary
  demo/                       loopback-only Python browser boundary

apps/local-demo-ui/           React + Vite + shadcn-compatible presentation layer

data/
  incidents/                  synthetic RelayOps incident cards
  procedures/                 synthetic candidate investigation material
  evals/
    calibration/              calibration-only evaluation assets
    heldout/                  frozen Tranche 01 and future-held-out Tranche 02

docs/
  adr/                        architecture and activation decisions
  reports/                    committed human-readable evidence
  runbooks/                   reproducible local operations
  submission/                 evaluator guide, evidence map, demo script

evidence_vault/
  reports/                    machine-readable immutable evidence receipts
  indexes/                    local dense index used by the local demo
```

---

## Key safety controls

- Schema-first typed boundaries with Pydantic validation.
- Explicit decision states and refusal-safe behavior.
- No browser-side policy, retrieval, selection, or procedure logic.
- Local loopback-only demo servers; no public bind, tunnel, or hosted endpoint.
- Input minimization and sensitive-content rejection at the browser boundary.
- No persistence of browser incident summaries.
- Synthetic RelayOps corpus only; do not paste real logs, customer identifiers, secrets, or post-mortems.
- Frozen held-out data and write-once reports are not retuned or overwritten.
- Procedure execution authorization is always false.

---

## Known evidence boundary

The frozen Tranche 01 typed-triage gate remains blocked on **EVAL-110** despite correct decision-state parity. The recorded issue is a same-family representative-selection divergence: the baseline retained `INC-012` where the frozen contract required `INC-009`, while the conflict state remained correct.

The later selector work is deliberately constrained: it is evaluated separately, activated only as a conditional display refinement, and does not alter the underlying active policy conclusion or rewrite the frozen baseline. This is a reliability artifact, not a “problem solved” claim.

---

## Do not claim

This repository does **not** establish:

- a production deployment;
- customer-data validation;
- real-incident performance;
- load, concurrency, or uptime guarantees;
- provider reliability under production conditions;
- automated diagnosis;
- automated remediation;
- authorization to execute procedures;
- a general-purpose incident response platform.

See [Maturity and non-claims](docs/submission/maturity-and-nonclaims.md).
