# ADR-0004: Deterministic Anti-Anchoring Policy Before Semantic Retrieval

## Context

The calibration keyword baseline retrieves acceptable precedents well but does not
know when a lexical candidate is operationally incompatible, when critical facts
are unknown, or when competing historical paths should block a procedure.

The baseline report records two false-operational matches across eleven safety-
evaluable calibration cases, and it returns lexical candidates for every
insufficient-precedent case. The retrieval metric alone is therefore not a safe
promotion signal.

## Decision

Add a deterministic anti-anchoring policy before dense retrieval or a real SIE
adapter is introduced.

The policy consumes:

- ranked candidate incident IDs;
- validated incident and procedure records;
- structured intake fact observations with `confirmed`, `contradicted`, or
  `unknown` status;
- an explicit provider-availability signal.

It returns only one of the five existing decision states. It does not use an LLM
to assign final state, invent facts, choose a root cause, or authorize remediation.

## Rules

1. Provider unavailable always returns `provider_degraded` and blocks ordinary
   evidence presentation.
2. A candidate with contradicted required facts is excluded.
3. No compatible candidates returns `insufficient_precedent` and blocks
   procedures.
4. Compatible candidates with unknown required facts return
   `missing_critical_facts` and block procedures.
5. Multiple compatible incident families return
   `evidence_found_with_conflict`; no procedure is preferred.
6. A candidate procedure can appear only when its current status, family
   applicability, and verification prerequisites all pass.

## Consequences

The current calibration fixtures gain explicit structured fact observations. These
observations are simulated intake fields, not hidden evaluator labels: the policy
reads them as input and the report evaluates its result independently.

The policy currently covers only the three authored families. New family support
requires new fixed cases, compatibility rules, and regression tests.

## Non-claims

This ADR does not establish semantic retrieval quality, extraction capability,
held-out safety, customer-data validity, or production incident-response safety.
