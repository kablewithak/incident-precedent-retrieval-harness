# Local Demo Script

## Purpose

Demonstrate that the system surfaces historical incident evidence while preserving uncertainty and preventing automatic operational action.

**Audience:** evaluator, technical interviewer, reliability reviewer.  
**Length:** 5–7 minutes.  
**Data boundary:** synthetic RelayOps data only.

## Setup

Follow the [shadcn local demo development runbook](../runbooks/shadcn-local-demo-development-runbook.md).

Open the polished local UI at:

```text
http://127.0.0.1:5173
```

Keep the Python boundary running at `127.0.0.1:8765`.

## Opening — 30 seconds

Say:

> “This is a local synthetic demonstration of Related Incident Evidence. The system does not diagnose an outage, execute a procedure, upload company data, or create a customer account. It accepts a sanitized incident summary plus structured verification facts, then returns a typed evidence packet. The deterministic policy decides what is safe to show; semantic retrieval is advisory only.”

Point to the local-only / human-review notice.

## Scenario 1 — Pool-pressure evidence — 90 seconds

Click **Pool-pressure evidence**, then click **Check the evidence safely**.

Say:

> “Here, several direct database-pool signals are confirmed and migration lock waits are ruled out. The system may surface relevant historical evidence because the verification facts support that narrow family.”

Point out:

- **Relevant historical evidence found**.
- The retained policy precedent(s).
- **Human review required** / no automatic action.
- Suggested investigation material, if present.
- `Procedure execution authorized: false`.

Then open **Advanced: choose the closest past example**.

Say:

> “This optional section cannot decide whether evidence exists. It only adds structured details that may select the closest display example from evidence the policy already admitted.”

Toggle advanced selection off and submit again.

Say:

> “The policy conclusion remains unchanged. The optional selector affects display refinement only.”

## Scenario 2 — Conflicting evidence — 90 seconds

Click **Conflicting evidence**, then submit.

Say:

> “This is the anti-anchoring case. Both queue or worker signals and connection-pool signals remain plausible. A less reliable system might choose the top-ranked historical incident and present it as the answer. This system returns conflict and deliberately does not choose a preferred procedure.”

Point out:

- **More than one plausible explanation remains**.
- Missing facts, conflict posture, or the broader policy-admitted set.
- No automatic procedure execution.
- Superlinked SIE only as **supporting context**, not the system conclusion.

## Scenario 3 — No safe match — 60 seconds

Click **No safe match**, then submit.

Say:

> “The input is vague and does not establish the decisive verification facts. Rather than make a similarity-based guess, the system returns no safe historical match.”

Point out:

- **No safe historical match found**.
- No fabricated precedent.
- No candidate procedure being treated as a recommendation.

## Scenario 4 — Evidence service unavailable — 60 seconds

Click **Evidence service unavailable**, then submit.

Say:

> “This forces the provider-degraded path. The system fails closed: it does not continue showing precedent and procedure candidates as though the required evidence capability were healthy.”

Point out:

- **Evidence service unavailable**.
- No usable historical precedent or procedure being presented.
- The same no-execution posture.

## Technical proof — 45 seconds

Open **Inspect technical details** on any scenario.

Say:

> “The UI is a renderer of a typed server packet. It does not create a conclusion in the browser. You can inspect the raw packet, including the policy decision, semantic advisory status, optional representative selection, and `procedure_execution_authorized=false`.”

## Closing — 30 seconds

Say:

> “The core reliability behavior is not that it always finds a match. It is that it visibly distinguishes safe evidence, conflict, missing information, insufficient precedent, and provider degradation. The system preserves those states rather than hiding them behind retrieval rank or a fluent recommendation.”

## Do not say

Do not say:

- “The system knows the root cause.”
- “This procedure will fix the outage.”
- “The semantic result is the decision.”
- “This is production-ready.”
- “This was tested on customer incidents.”
- “The selector improved the frozen active policy.”

Use the [maturity and non-claims statement](maturity-and-nonclaims.md) when you need exact safe wording.
