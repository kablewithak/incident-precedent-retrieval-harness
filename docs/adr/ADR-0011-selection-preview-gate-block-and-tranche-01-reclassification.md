# ADR-0011: Block Representative-Selection Activation and Reclassify Tranche 01 for This Decision Boundary

## Status

Accepted. No active-policy integration or new Tranche 01 comparison is authorized.

## Context

PR #13 added a calibration-only preview for choosing a representative
connection-pool incident after the current anti-anchoring policy has already
found multiple cards compatible. The preview remains isolated from
`AntiAnchoringDecisionPolicy`; it does not modify keyword retrieval, held-out
files, baseline artifacts, or promotion-gate behavior.

The preview review confirmed useful safeguards:

- active policy code is unchanged;
- the preview does not load held-out cases;
- the preview does not read lexical rank or score in its selection key;
- explicit ties remain ties rather than silently falling back to rank order.

The review also found that the current preview cannot justify activation or a
new controlled comparison:

1. The calibration report covers only three preview-producing cases.
2. The sidecar selection profiles contain manually authored text cues that are
   not linked to versioned incident-card fields with per-cue rationale.
3. Selection scores raw cue-count. Semantically overlapping or substring-related
   cues can multiply one underlying signal, for example `auth` and
   `authentication`.
4. The current text matcher uses normalized substring containment, which can
   yield accidental matches.
5. The profile schema does not prove exact coverage of every currently authored
   connection-pool card, nor does it prove that a profile cue is grounded in the
   card it represents.
6. Held-Out Tranche 01 and its expected EVAL-110 representative contract were
   already visible during investigation and preview design. It must not be
   treated as unseen evidence for further representative-selection tuning.

Tranche 01 remains immutable and valuable as historical baseline and comparison
evidence. Its validity for prior measurements is unchanged. It is no longer a
valid blind promotion gate for **new representative-selection behavior**.

## Decision

1. Do not integrate the PR #13 preview into `AntiAnchoringDecisionPolicy`.
2. Do not run a new Tranche 01 representative-selection comparison.
3. Preserve all Tranche 01 manifests, baseline, autopsy, ADR-0009 comparison,
   and reports unchanged.
4. Treat Tranche 01 as an observed diagnostic set for representative-selection
   work only. It may explain the original failure but may not validate a new
   selector as a fresh holdout result.
5. Before another selector is implemented, define a schema-derived selection
   contract using only canonical, versioned incident-card fields or explicitly
   source-linked annotations.
6. Freeze a fresh evaluation tranche before any future activation comparison.
   The fresh tranche must be recorded separately from calibration and must not
   be used to tune selector rules, profile annotations, thresholds, or
   canonicalisation.

## Requirements for a successor calibration selector

A successor design must:

- derive signals from canonical incident fields such as service, component,
  change context, symptoms, or observability signals, or from annotations that
  explicitly name their source fields and review rationale;
- treat correlated aliases as one signal family, not multiple score increments;
- use token or phrase-boundary matching rather than arbitrary substring
  containment;
- require complete profile coverage for every connection-pool card that may
  enter the candidate pool;
- exclude profile records that cannot be tied to a card field and review note;
- preserve explicit ties when available evidence does not discriminate safely;
- remain separate from the active policy until calibration and a fresh frozen
  evaluation tranche justify a predeclared comparison.

## Consequences

The project loses the option of claiming a Tranche 01 representative-selection
improvement. This is the correct cost of preserving evaluation integrity.

The project gains a stronger reliability story:

```text
known held-out failure
-> calibration-only exploration
-> integrity review finds contamination and weak evidence signals
-> no premature comparison
-> fresh frozen tranche required before promotion evidence
```

## Non-claims

This decision does not change:

- active anti-anchoring policy behavior;
- current keyword baseline behavior;
- any frozen Tranche 01 artifact;
- provider status;
- dense retrieval, reranking, extraction, or deployment status;
- production, customer-data, or incident-response readiness.
