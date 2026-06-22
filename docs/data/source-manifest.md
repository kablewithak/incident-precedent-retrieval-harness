# Source Manifest

## Purpose

This manifest records the public material used to inform source-grounded synthetic RelayOps incident cards. It is not an incident corpus. Do not paste full articles, private incident records, customer data, production logs, credentials, or internal identifiers into this repository.

## Current status

- **Source review:** not started
- **Corpus cards authored:** 0 / 32
- **Candidate investigation procedures authored:** 0 / 8–10
- **Held-out cases frozen:** no

## Required fields for every reviewed source

| Field | Requirement |
|---|---|
| `source_record_id` | Stable manifest identifier, for example `SRC-001`. |
| `source_name` | Publisher or repository name. |
| `source_url` | Canonical public URL. |
| `source_date` | Publication date, or `unknown` when unavailable. |
| `usage_mode` | `licensed_source`, `cited_reference`, or `manually_authored_variant`. |
| `license_or_terms_note` | Short note on why the planned use is permitted. |
| `mechanisms_observed` | Brief, original-language summary of operational mechanisms. |
| `transformation_note` | How it becomes a fictional RelayOps record without copying prose. |
| `human_verified` | `true` only after manual review. |

## Approved source categories

1. PostHog public postmortems, with licence/attribution handling verified per source.
2. Official public incident analyses from Cloudflare, GitHub, and OpenAI, used as cited references for mechanisms and terminology.
3. Optional, carefully reviewed Rootly AI Labs public log excerpts as noisy evidence examples only, never as the core incident corpus.
4. Rootly SRE Skills Bench as a methodology reference only.

## Records

| source_record_id | source_name | source_url | source_date | usage_mode | license_or_terms_note | mechanisms_observed | transformation_note | human_verified |
|---|---|---|---|---|---|---|---|---|
