# Maturity and Non-Claims

## Current maturity label

```text
locally validated + synthetic-data validated
```

This label is deliberate. The repository includes deterministic tests, frozen-evaluation controls, local provider-adapter behavior, a typed runtime boundary, and a loopback-only reviewer demo. It does not include the operational proof required for a production-ready claim.

## What has been demonstrated

- Schema-first typed browser-to-triage request boundary.
- Deterministic top-level policy states.
- Explicit conflict, abstention, missing-facts, and provider-degraded behavior.
- Semantic advisory evidence separated from policy authority.
- Strict-dominance representative selection tested in isolated and future-held-out settings.
- Conditional display-only selection refinement that leaves policy authority unchanged.
- Candidate procedures as review-only investigation material.
- Procedure execution authorization fixed to `false`.
- Frozen Tranche 01 baseline block preserved as evidence.
- Loopback-only Python and React demo surfaces.
- Synthetic RelayOps corpus and no browser-payload persistence.

## What has not been demonstrated

- Production deployment or operational ownership.
- Authentication, authorization, tenancy, audit retention, or incident commander workflow.
- Customer-data validation or processing.
- Real post-mortem, raw log, dashboard, or ticket ingestion.
- Provider reliability, production latency, load, concurrency, or failover behavior.
- Security testing beyond the local scope controls in this repository.
- Procedure versioning, approval, execution validation, rollback, or action realization.
- End-to-end frozen promotion of the active policy path.
- Generalization beyond the authored synthetic incident families.
- Root-cause diagnosis quality.
- Automated remediation safety.

## Safe language

Use:

> “A local, synthetic-data evaluated reliability harness for historical incident evidence.”

> “The deterministic policy is decision authority; semantic retrieval is advisory.”

> “The system can preserve uncertainty and abstain rather than forcing a recommendation.”

> “Procedure candidates are human-review investigation material. Execution remains unauthorized.”

> “The frozen Tranche 01 promotion result is blocked and retained as evidence.”

Do not use:

> “Production-ready.”

> “Proven on customer data.”

> “Automatically identifies root cause.”

> “Executes incident remediation.”

> “The selector fixes the baseline.”

> “The model determines what action to take.”

## Privacy and data boundaries

- Do not enter real logs, stack traces, incident tickets, post-mortems, customer identifiers, secrets, or credentials.
- Do not run the demo on a public host, LAN bind, tunnel, or shared endpoint.
- Do not commit generated local artifacts, browser payloads, environment files, or provider responses.
- Do not represent the synthetic corpus as customer or source-grounded operational evidence.

## Future evidence required before broader claims

| Desired future claim | Required proof |
|---|---|
| Customer-data tested | Approved data boundary, minimization/redaction, retention/deletion controls, vendor review, controlled evaluation |
| Production-ready | Deployment ownership, monitoring, incident response, security review, load behavior, rollback, real operational runbooks |
| Procedure execution | Authenticated approval, action validators, least privilege, dry run, audit records, rollback, human signoff |
| Broader policy promotion | New independent frozen end-to-end evaluation, baseline comparison, explicit gate, no regression of existing safety controls |
| General retrieval quality | Larger independently authored held-out corpus, grounded relevance judgements, provenance, failure taxonomy, repeatable reports |
