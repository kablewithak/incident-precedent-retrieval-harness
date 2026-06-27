# Evaluator Start Here

## What you are reviewing

Related Incident Evidence is a local, synthetic-data reliability harness. It asks whether a system can present related historical incident evidence **without turning similarity into an unsafe operational recommendation**.

Do not evaluate it as a production incident platform. Evaluate it as a bounded, inspectable system with explicit policy authority, held-out evidence boundaries, failure states, and non-claims.

## Fast review path: 15 minutes

### 1. Read the core claim — 2 minutes

Read the root [README](../../README.md), then [Architecture and decision boundaries](../architecture/related-incident-evidence-architecture.md).

You should understand:

- the policy, not the model or UI, is decision authority;
- Superlinked SIE is advisory only;
- candidate procedures are review-only;
- `procedure_execution_authorized` is always false;
- the local browser surface cannot create policy authority.

### 2. Inspect the evidence posture — 5 minutes

Read the [Evidence map](evidence-map.md) in this order:

1. [Frozen typed-triage promotion gate](../reports/frozen-typed-triage-promotion-gate.md)
2. [EVAL-110 representative-selection autopsy](../reports/eval-110-representative-selection-autopsy.md)
3. [Procedure-asymmetry fixture comparison](../reports/procedure-asymmetry-fixture-comparison.md)
4. [Future-held-out Tranche 02 comparison](../reports/tranche-02-future-heldout-comparison.md)
5. [Conditional selection activation readiness](../reports/conditional-representative-selection-activation-readiness.md)

Expected conclusion:

```text
The base Tranche 01 promotion path is blocked.
The later selection work has passing isolated/future-held-out controls
but remains activation-blocked except for the narrow local display-only integration.
No report proves production readiness.
```

A reliable evaluator should treat the recorded block as a strength of the harness, not as a defect to hide.

### 3. Run deterministic tests — 2 minutes

From repository root:

```powershell
python -m pytest .\tests\unit
```

### 4. Run the local presentation check — 2 minutes

For first-time setup:

```powershell
Push-Location .\apps\local-demo-ui

npm ci

npm run test

npm run build

Pop-Location
```

### 5. Run the local demo — 4 minutes

Use [the demo script](demo-script.md).

Focus on four fixed scenarios:

1. Pool-pressure evidence.
2. Conflicting evidence.
3. No safe match.
4. Evidence service unavailable.

## What good behavior looks like

| Scenario | Correct system behavior |
|---|---|
| Pool-pressure evidence | Surface a safe evidence state; keep a human responsible for investigation; no procedure execution |
| Conflicting evidence | Preserve multiple plausible paths; do not force a single root cause or preferred procedure |
| No safe match | Abstain rather than fabricate a comparable precedent |
| Evidence service unavailable | Fail closed; do not show precedent or procedure candidates |
| Representative selection enabled | Only change the highlighted policy-approved example, never the decision state or procedure posture |

## What not to infer

Do not infer that this repository:

- diagnoses root cause;
- executes procedures;
- has seen customer data;
- is deployed or load-tested;
- establishes production provider reliability;
- is a complete incident-management platform.

## Useful inspection points

- `src/incident_precedent_harness/demo/application.py` — narrow browser request boundary.
- `src/incident_precedent_harness/demo/local_demo_server.py` — loopback-only transport.
- `src/incident_precedent_harness/triage/` — typed evidence-packet boundary.
- `src/incident_precedent_harness/decisions/conditional_representative_selection.py` — optional display-only refinement.
- `apps/local-demo-ui/` — React/Vite presentation layer.
- `data/evals/heldout/` — frozen evaluation assets.
- `docs/reports/` and `evidence_vault/reports/` — readable and machine-readable evidence receipts.

## Reviewer conclusion template

```text
I verified that the system is a local synthetic-data evidence harness.
The deterministic policy remains decision authority, semantic evidence is advisory,
and procedure execution remains unauthorized. I observed that the project preserves
a blocked frozen promotion result and distinguishes it from later narrower selector
evidence. I do not interpret the artifact as production-ready or customer-data tested.
```
