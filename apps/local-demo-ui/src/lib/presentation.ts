import type { FactValue, TriageEvidencePacket } from "@/lib/contracts"

export type DecisionTone = "positive" | "warning" | "critical" | "neutral"

export type DecisionCopy = {
  title: string
  description: string
  tone: DecisionTone
}

const decisionCopy: Record<string, DecisionCopy> = {
  evidence_found: {
    title: "Relevant historical evidence found",
    description: "The system found historical evidence that is safe to review. A human still decides what to investigate next.",
    tone: "positive",
  },
  evidence_found_with_conflict: {
    title: "More than one plausible explanation remains",
    description: "The evidence points to more than one possible path. The system is deliberately not choosing a single explanation or procedure.",
    tone: "warning",
  },
  missing_critical_facts: {
    title: "More verification is needed",
    description: "Plausible historical evidence exists, but key facts have not been confirmed yet.",
    tone: "warning",
  },
  insufficient_precedent: {
    title: "No safe historical match found",
    description: "The system does not have enough grounded historical evidence to show a reliable precedent.",
    tone: "critical",
  },
  provider_degraded: {
    title: "Evidence service unavailable",
    description: "The system is failing closed. It is not showing precedent or procedure candidates while required evidence capability is unavailable.",
    tone: "critical",
  },
}

const selectionCopy: Record<string, string> = {
  not_requested: "No closest-example comparison was requested. The policy display is unchanged.",
  selection_not_applied: "A closest-example comparison was not safe or applicable here, so the system preserved the complete policy-approved set.",
  single_representative_applied: "One approved past example best matches the additional details you supplied. This does not change the system conclusion.",
  explicit_tie_applied: "More than one approved past example remains equally relevant, so the system kept the full tie set visible.",
}

export function decisionPresentation(state: string): DecisionCopy {
  return decisionCopy[state] ?? {
    title: "Governed evidence decision returned",
    description: "The system returned a governed evidence decision for human review.",
    tone: "neutral",
  }
}

export function selectionPresentation(status: string | undefined): string {
  return status ? selectionCopy[status] ?? "The closest-example comparison produced a trace-safe result." : selectionCopy.not_requested
}

export function displayRepresentativeIds(packet: TriageEvidencePacket): string[] {
  return packet.representative_selection?.displayed_representative_ids ?? packet.policy_decision.retained_precedent_ids
}

export function factLabel(value: FactValue): string {
  return value === "unknown" ? "Not checked yet" : value === "confirmed" ? "Confirmed" : "Ruled out"
}
