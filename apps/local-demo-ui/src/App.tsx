import { useState } from "react"
import { ShieldCheck } from "lucide-react"
import { IncidentIntake, fromScenario, type IntakeState } from "@/components/incident-intake"
import { EvidenceReview } from "@/components/evidence-review"
import { TechnicalPacket } from "@/components/technical-packet"
import { Badge } from "@/components/ui/badge"
import { requestTriage } from "@/lib/api"
import type { TriageEvidencePacket, TriagePayload } from "@/lib/contracts"
import {
  createRequestFeedback,
  type RequestFeedback,
} from "@/lib/request-feedback"

export default function App() {
  const [intake, setIntake] = useState<IntakeState>(() => fromScenario("pool"))
  const [packet, setPacket] = useState<TriageEvidencePacket | null>(null)
  const [pending, setPending] = useState(false)
  const [feedback, setFeedback] = useState<RequestFeedback | null>(null)

  function updateIntake(nextValue: IntakeState) {
    setIntake(nextValue)
    if (feedback?.displayMode === "inline_alert") {
      setFeedback(null)
    }
  }

  async function submit(payload: TriagePayload) {
    if (!payload.input_summary) {
      setFeedback(
        createRequestFeedback(
          "bad",
          "Add a sanitized description of what is happening.",
        ),
      )
      return
    }

    setPending(true)
    setFeedback(null)

    try {
      const response = await requestTriage(payload)
      setPacket(response.packet)
      setFeedback(
        createRequestFeedback(
          "good",
          "Evidence review ready. The conclusion, supporting evidence, and human-review limit are shown separately.",
        ),
      )
    } catch (error) {
      setFeedback(
        createRequestFeedback(
          "bad",
          error instanceof Error
            ? error.message
            : "The local demo could not safely create a packet.",
        ),
      )
    } finally {
      setPending(false)
    }
  }

  const visibleRequestError =
    feedback?.displayMode === "inline_alert" ? feedback.message : null
  const liveStatusMessage =
    feedback?.displayMode === "screen_reader_only" ? feedback.message : ""

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,_rgba(14,116,144,0.24),_transparent_42%),linear-gradient(160deg,#07111e_0%,#09101e_48%,#050914_100%)] text-slate-100">
      <header className="mx-auto flex max-w-7xl flex-col justify-between gap-6 px-5 pb-7 pt-8 lg:flex-row lg:items-start lg:px-8">
        <div className="max-w-3xl">
          <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-sky-300">
            <ShieldCheck className="h-4 w-4" />
            Related Incident Evidence · Local Demo
          </div>
          <h1 className="text-4xl font-semibold tracking-[-0.045em] text-white sm:text-5xl">
            Evidence before action.
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
            Tell the system what you have confirmed. It will show safe historical
            evidence, preserve uncertainty, and keep every action with a human.
          </p>
        </div>
        <div className="max-w-sm rounded-2xl border border-slate-700/80 bg-slate-950/60 p-4 text-sm leading-6 text-slate-300">
          <strong className="text-white">Local synthetic demonstration only.</strong>
          <br />
          Human review is always required. Nothing here diagnoses root cause, runs a
          procedure, uploads company data, or creates a customer account.
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-5 pb-10 lg:px-8">
        <div aria-live="polite" className="sr-only" role="status">
          {liveStatusMessage}
        </div>
        <div className="grid gap-6 xl:grid-cols-[minmax(390px,0.9fr)_minmax(0,1.35fr)]">
          <IncidentIntake
            value={intake}
            pending={pending}
            requestError={visibleRequestError}
            onChange={updateIntake}
            onSubmit={submit}
          />
          <section className="space-y-4">
            <EvidenceReview packet={packet} />
            <TechnicalPacket packet={packet} />
          </section>
        </div>
      </main>

      <footer className="mx-auto flex max-w-7xl flex-wrap items-center gap-3 px-5 pb-8 text-xs text-slate-500 lg:px-8">
        <Badge variant="neutral">Loopback-only local surface</Badge>
        <span>·</span>
        <span>No payload persistence</span>
        <span>·</span>
        <span>Synthetic RelayOps corpus</span>
        <span>·</span>
        <span>Human review required</span>
        <span>·</span>
        <span>No procedure runs automatically</span>
      </footer>
    </div>
  )
}
