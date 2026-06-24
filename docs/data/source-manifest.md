# Source Manifest — Related Incident Evidence

## Use rule

This manifest approves sources for controlled, attributed adaptation into a
fictional RelayOps corpus. It does **not** authorize copying articles wholesale,
using real customer data, or presenting source events as RelayOps events.

A record may be marked `source_grounded` only after a human confirms the exact
source, the transformation note, and the absence of copied narrative. Until then,
use `controlled_variant` and record the proposed source linkage in a batch review
file.

## Approved source records

| ID | Source | Date | Usage mode | Approved use | Status |
|---|---|---|---|---|---|
| SRC-001 | PostHog public post-mortems repository | n/a | licensed_source | incident structure, engineering terminology, manually authored variants | approved |
| SRC-002 | Cloudflare: Tenant Service API / dashboard outage | 2025-09-13 | cited_reference | overload after software change, dependency amplification, timeline structure | approved |
| SRC-003 | Cloudflare: 1.1.1.1 incident | 2025-07-15 | cited_reference | configuration/topology change and globally visible failure timeline | approved |
| SRC-004 | Cloudflare: service-token code release outage | 2023-01-25 | cited_reference | authorization/configuration regression mechanism and response uncertainty | approved |
| SRC-005 | GitHub availability reports | rolling | cited_reference | incident-report cadence and concise impact framing only | review_required |
| SRC-006 | PostHog Feature Flags Service Outage | 2025-09-29 | licensed_source | deployment-adjacent connection failure, retry amplification, crash-loop pattern | approved |
| SRC-007 | PostHog Feature Flags Service Multiple Outages | 2025-10-21 | licensed_source | consumer capacity loss, retry amplification, connection-pool pressure | approved |
| SRC-008 | PostHog Feature Flags Cache Degradation | 2026-02-06 | licensed_source | worker OOM pattern, task backlog, cache-staleness impact | approved |
| SRC-009 | PostHog Data Processing Delays — Events & Persons Ingestion | 2025-11-15 | licensed_source | database-driven processing delay and backlog recovery pattern | approved |
| SRC-010 | PostgreSQL documentation: Explicit Locking | rolling | cited_reference | general lock conflict, transaction-bound lock lifetime, and lock-wait concepts | approved |
| SRC-011 | PostgreSQL documentation: `pg_locks` view | rolling | cited_reference | lock-observation vocabulary and verification-fact design only | approved |
| SRC-012 | PostgreSQL documentation: Connections and Authentication | rolling | cited_reference | connection-limit and reserved-slot vocabulary for verification-fact design only | approved |

## Licence and transformation controls

### SRC-001 — PostHog post-mortems

- URL: `https://github.com/PostHog/post-mortems`
- Licence: MIT; retain copyright and licence notices where applicable.
- Transformation: never copy postmortem narrative wholesale. Derive a distinct,
  fictional RelayOps record with a written transformation note.

### SRC-002 — Cloudflare Tenant Service API / dashboard outage

- URL: `https://blog.cloudflare.com/deep-dive-into-cloudflares-sept-12-dashboard-and-api-outage/`
- Usage: cited reference only.
- Transformation: extract only general mechanisms such as a software change,
  increased request load, dependency sensitivity, and recovery uncertainty.
  Do not copy narrative, service names, timelines, or remediation instructions.

### SRC-003 — Cloudflare 1.1.1.1 incident

- URL: `https://blog.cloudflare.com/cloudflare-1-1-1-1-incident-on-july-14-2025/`
- Usage: cited reference only.
- Transformation: use only general configuration-change and impact-pattern
  concepts; adapt into RelayOps without source infrastructure identifiers.

### SRC-004 — Cloudflare service-token code release outage

- URL: `https://blog.cloudflare.com/tag/post-mortem/page/2/`
- Usage: cited reference only. Locate the individual January 25, 2023 postmortem
  before authoring a record.
- Transformation: record the exact individual source URL and date in the
  authored incident provenance record.

### SRC-005 — GitHub availability reports

- URL: `https://github.blog/category/company-news/`
- Status: review required before any record is authored.
- Restriction: do not use a monthly report as evidence for a specific failure
  mechanism unless its linked incident analysis provides that detail.

### SRC-006 — PostHog Feature Flags Service Outage

- URL: `https://github.com/PostHog/post-mortems/blob/main/2025-09-29-flags-is-down.md`
- Licence: MIT; retain notices where applicable.
- Usage: source review for connection timeout, retry amplification, and
  crash-loop mechanisms only.
- Transformation: remove organization-specific services, exact chronology,
  direct operational remediation, and implementation identifiers.

### SRC-007 — PostHog Feature Flags Service Multiple Outages

- URL: `https://github.com/PostHog/post-mortems/blob/main/2025-10-21-feature-flags-recurring-outages.md`
- Licence: MIT; retain notices where applicable.
- Usage: source review for worker-capacity loss, retry amplification, and
  connection-pool pressure only.
- Transformation: map to fictional RelayOps components; do not copy incident
  narrative, source infrastructure names, or production details.

### SRC-008 — PostHog Feature Flags Cache Degradation

- URL: `https://github.com/PostHog/post-mortems/blob/main/2026-02-06-feature-flags-cache-degradation.md`
- Licence: MIT; retain notices where applicable.
- Usage: source review for worker OOM, backlogged tasks, and stale-cache
  consequences only.
- Transformation: remove source organization names, counts, dates, and direct
  remediation steps; use only the generalized failure mechanism.

### SRC-009 — PostHog Data Processing Delays — Events & Persons Ingestion

- URL: `https://github.com/PostHog/post-mortems/blob/main/2025-11-15-persons-db-migration.md`
- Licence: MIT; retain notices where applicable.
- Usage: source review for database-write delay, pipeline backlog, and recovery
  sequencing only.
- Transformation: retain no source database identifiers, exact metrics, or
  remediation instructions.

### SRC-010 — PostgreSQL Explicit Locking

- URL: `https://www.postgresql.org/docs/current/explicit-locking.html`
- Usage: cited reference only.
- Transformation: use only generalized lock conflict and transaction-bound
  waiting concepts. Do not copy SQL snippets, lock-mode tables, or procedures.

### SRC-011 — PostgreSQL `pg_locks` view

- URL: `https://www.postgresql.org/docs/current/view-pg-locks.html`
- Usage: cited reference only.
- Transformation: use only safe verification-fact vocabulary. Do not copy source
  queries, production schema names, or operational commands.

### SRC-012 — PostgreSQL Connections and Authentication

- URL: `https://www.postgresql.org/docs/current/runtime-config-connection.html`
- Usage: cited reference only.
- Transformation: use only general connection-limit and reserved-slot concepts to
  define safe verification facts. Do not copy configuration snippets, recommend
  increasing limits, or infer a production database configuration.

## Batch review status

- Batch 01 uses `SRC-006` through `SRC-009` as proposed linkage for four
  controlled queue-backlog variants. See `docs/data/batch-01-source-review.md`.
- Batch 02 uses `SRC-009` through `SRC-011` as proposed linkage for four
  controlled migration-lock variants. See `docs/data/batch-02-source-review.md`.
- Batch 03 uses `SRC-006`, `SRC-007`, and `SRC-012` as proposed linkage for four
  controlled connection-pool variants. See
  `docs/data/batch-03-source-review.md`.

No controlled variant is source-grounded until the source-review checklist below
is completed.

## Source-review checklist

Before promoting any controlled variant to `source_grounded`:

1. Confirm the source is public and the individual URL works.
2. Confirm the source date, usage mode, and source identifier.
3. Confirm the transformation note describes only retained general mechanisms.
4. Confirm organization names, account identifiers, infrastructure names,
   internal URLs, IP addresses, copied timelines, and remediation detail are
   absent from the RelayOps card.
5. Set `human_verified: true` only after this review is complete.
