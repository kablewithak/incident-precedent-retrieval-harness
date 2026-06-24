# Source Manifest — Related Incident Evidence

## Use rule

This manifest approves sources for controlled, attributed adaptation into a
fictional RelayOps corpus. It does **not** authorize copying articles wholesale,
using real customer data, or presenting source events as RelayOps events.

Each authored record must link to exactly one source record here when
`record_origin: source_grounded`.

## Approved source records

| ID | Source | Date | Usage mode | Approved use | Status |
|---|---|---|---|---|---|
| SRC-001 | PostHog public post-mortems repository | n/a | licensed_source | incident structure, engineering terminology, manually authored variants | approved |
| SRC-002 | Cloudflare: Tenant Service API / dashboard outage | 2025-09-13 | cited_reference | overload after software change, dependency amplification, timeline structure | approved |
| SRC-003 | Cloudflare: 1.1.1.1 incident | 2025-07-15 | cited_reference | configuration/topology change and globally visible failure timeline | approved |
| SRC-004 | Cloudflare: service-token code release outage | 2023-01-25 | cited_reference | authorization/configuration regression mechanism and response uncertainty | approved |
| SRC-005 | GitHub availability reports | rolling | cited_reference | incident-report cadence and concise impact framing only | review_required |

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

## Source-review checklist

Before authoring a card:

1. Confirm the source is public and the individual URL works.
2. Record the date, usage mode, and source identifier.
3. Write a transformation note explaining what general mechanism was retained.
4. Remove organization names, account identifiers, infrastructure names,
   internal URLs, IP addresses, exact copied timelines, and remediation detail.
5. Set `human_verified: true` only after a human has checked the result.
