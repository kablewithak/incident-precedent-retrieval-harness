export type VerificationStatus = "confirmed" | "contradicted"
export type FactValue = VerificationStatus | "unknown"

export type ObservedFact = {
  fact: string
  status: VerificationStatus
}

export type RepresentativeSelectionIntake = {
  service: string | null
  component: string | null
  change_context: string | null
  operational_signal_families: string[]
  contradicted_signal_families: string[]
}

export type TriagePayload = {
  input_summary: string
  observed_facts: ObservedFact[]
  provider_available: boolean
  representative_selection_intake?: RepresentativeSelectionIntake
}

export type PolicyDecision = {
  decision_state: string
  retained_precedent_ids: string[]
  candidate_procedure_ids: string[]
  missing_critical_facts: string[]
  conflict_summary: string | null
  safety_notes: string[]
}

export type AdvisoryCandidate = {
  incident_id: string
  rank: number
  cosine_similarity: number
}

export type SemanticAdvisory = {
  status: string
  candidate_evidence: AdvisoryCandidate[]
  profile_id: string | null
}

export type RepresentativeSelection = {
  status: string
  displayed_representative_ids: string[]
  policy_admitted_candidate_ids: string[]
  trace_reason: string
  selector_invoked: boolean
}

export type TriageEvidencePacket = {
  packet_kind: string
  policy_decision: PolicyDecision
  semantic_advisory: SemanticAdvisory
  representative_selection: RepresentativeSelection | null
  procedure_execution_authorized: false
  non_claims: string[]
}

export type TriageResponse = {
  status: "ok"
  packet: TriageEvidencePacket
  runtime_boundary: string
}
