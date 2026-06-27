# Procedure-Asymmetry Adversarial Fixture — Authoring Ledger

## Proposal identity

| Field | Value |
|---|---|
| Proposal status | `PROPOSAL_ONLY_NOT_FROZEN_NOT_EVALUATED` |
| Fixture contract | `procedure-asymmetry-adversarial-fixture-v1` |
| Governing boundary | ADR-0019 |
| Authoring mode | Fresh blinded authoring session |
| Authoring timestamp | 2026-06-26T17:34:00Z |
| Accepted case count | 3 |
| Primary adversarial case | `PAF-T02-001` |
| Control case | `PAF-T02-003` |

## Blind-authoring boundary

This proposal used only the supplied source incident cards, typed schema contracts, ADR-0012, ADR-0018, ADR-0019, the Tranche 02 constitution, and the supplied acceptance audit.

The following were treated as unavailable and were not requested, recreated, inspected, or used as an oracle: prior evaluation cases, selector-calibration labels, policy-shadow fixtures, Tranche 01 outcomes, the prior Tranche 02 proposal details, reports outside the supplied acceptance audit, retrieval ranks or scores, procedure-selection behavior, policy behavior, and selector implementation behavior.

## Design decision

The supplied acceptance audit identifies a genuine corpus limitation: the source `connection_pool_exhaustion` cards share procedure posture, so a source-only case cannot satisfy the no-hidden-legacy-tie-break requirement. ADR-0019 therefore authorizes a separate, governed, test-only controlled-variant fixture.

The proposal uses two case-scoped controlled card sets derived from `INC-009` and `INC-010`. They preserve schema-valid `HistoricalIncidentCard` and `RepresentativeSelectionSignature` contracts. The procedure lists are the only purposeful adversarial perturbation axis. No source incident card or active procedure is edited.

## Accepted cases

| Case ID | Role | Diagnostic objective | Source incident IDs | Card set | Expected-outcome asset |
|---|---|---|---|---|---|
| `PAF-T02-001` | Primary adversarial | Detect whether favorable procedure metadata, lower incident ID, or first candidate position can improperly override a typed-selection discriminator. | `INC-009`, `INC-010` | `PAV-001-procedure-asymmetric` | `expected_outcomes/PAF-T02-001.expected.json` |
| `PAF-T02-002` | Order-reversal partner | Verify that reversing only candidate sequence leaves the primary typed result unchanged. | `INC-009`, `INC-010` | `PAV-001-procedure-asymmetric` | `expected_outcomes/PAF-T02-002.expected.json` |
| `PAF-T02-003` | Procedure-neutral control | Confirm that the typed result persists when only procedure-list fields are neutralized. | `INC-009`, `INC-010` | `PAV-002-procedure-neutral-control` | `expected_outcomes/PAF-T02-003.expected.json` |

## Oracle grounding

The typed intake is identical across the three cases. It names a controlled service, component, change context, and operational signal families that are present in the supplied source-card signatures used to derive the controlled variants. The candidate cards remain in one `connection_pool_exhaustion` family, and each selection signature is mechanically tied to canonical card fields.

The published ADR-0012 rule requires a strict-dominance decision to depend on identity alignment, change-context alignment, matching signal-family coverage, and contradicted-signal handling. Procedure availability, incident identifier, and candidate order are prohibited selection inputs. The primary adversarial fixture intentionally creates those prohibited competing cues in a case-scoped, test-only card set. The reviewer-controlled expected-outcome assets contain the case-specific result and concise oracle rationale; they are structurally separate from runtime case inputs.

## Structural separation

- `inputs/cases/` contains case-level selector inputs and never contains expected representatives, expected outcome kinds, or review rationales.
- `inputs/controlled_cards/` contains case-scoped, test-only `HistoricalIncidentCard` variants.
- `inputs/governance/` contains test-only provenance and perturbation metadata. It does not contain expected outcomes, desired representative IDs, or oracle rationales, and it must not be passed to the selector.
- `expected_outcomes/` contains reviewer-controlled expected outcomes and concise oracle rationales. It is unavailable to selector runtime code.

## Test-only governance and non-claims

- The fixture is proposal-only, test-only, and intended exclusively for a future Tranche 02 comparison harness.
- It does not change source incident cards, active procedures, selector logic, policy logic, retrieval behavior, production configuration, or historical evaluation assets.
- No selector or policy was executed against this package.
- No selector or policy pass is claimed.
- No selector activation or Tranche 02 freeze is authorized.

## Freeze readiness

This archive is an authoring proposal. It requires acceptance review, a future deterministic fixture validator, fresh reviewed manifests, and a separately recorded evaluated commit before any comparison run. The manifest hashes in `manifest.json` are integrity evidence for this proposal; they are not a freeze authorization.

## V2 provenance remediation

This V2 reissue is a constrained provenance correction under
`V2_REMEDIATION_BASELINE.json`. It does not author new cases, revise expected
outcomes, modify controlled-card payloads, or alter rejected ideas.

The only V1-to-V2 proposal changes are:

1. `inputs/governance/procedure_asymmetry_governance.json`
2. `inputs/governance/controlled_card_derivation_assertions.json`
3. `authoring_ledger.md`
4. `APPLY_MANIFEST.md`
5. `manifest.json`

For `PAV-001-procedure-asymmetric` / `INC-013`, the governed perturbation list
now explicitly includes `unsafe_procedure_ids`. The source `RB-002` entry is
removed only to isolate the test-only `RB-003` procedure-availability asymmetry.
This change is declared, mechanically asserted, and not applied to any active
incident card or procedure dataset.

The new derivation-assertion asset records the source-card digest, controlled-card
digest, actual changed field set, declared perturbation field set, and equality
status for all four controlled cards.
