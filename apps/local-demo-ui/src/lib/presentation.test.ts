import { describe, expect, it } from "vitest"
import type { TriageEvidencePacket } from "@/lib/contracts"
import { decisionPresentation, displayRepresentativeIds, selectionPresentation } from "@/lib/presentation"

const packet = {
  packet_kind: "typed_triage_evidence_packet_v1",
  policy_decision: { decision_state: "evidence_found", retained_precedent_ids: ["INC-009"], candidate_procedure_ids: [], missing_critical_facts: [], conflict_summary: null, safety_notes: [] },
  semantic_advisory: { status: "available", candidate_evidence: [], profile_id: "local-sie-encode-v1" },
  representative_selection: { status: "single_representative_applied", displayed_representative_ids: ["INC-009"], policy_admitted_candidate_ids: ["INC-009", "INC-010"], trace_reason: "safe", selector_invoked: true },
  procedure_execution_authorized: false,
  non_claims: [],
} satisfies TriageEvidencePacket

describe("presentation controls", () => {
  it("uses plain-language, safety-oriented copy for a governed decision", () => {
    expect(decisionPresentation("evidence_found").title).toBe("Relevant historical evidence found")
    expect(decisionPresentation("provider_degraded").tone).toBe("critical")
  })

  it("uses the display refinement only as a separate visual layer", () => {
    expect(displayRepresentativeIds(packet)).toEqual(["INC-009"])
    expect(selectionPresentation(packet.representative_selection.status)).toContain("does not change the system conclusion")
  })
})
