import {
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  ShieldCheck,
} from "lucide-react"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"
import { ChoiceSelect } from "@/components/ui/choice-select"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { FactValue, TriagePayload } from "@/lib/contracts"
import {
  changeContexts,
  components,
  factDefinitions,
  scenarios,
  services,
  signalDefinitions,
  type ScenarioKey,
} from "@/lib/scenarios"

export type IntakeState = {
  scenario: ScenarioKey
  summary: string
  facts: Record<string, FactValue>
  selectionEnabled: boolean
  service: string
  component: string
  changeContext: string
  signals: string[]
}

type Props = {
  value: IntakeState
  pending: boolean
  requestError: string | null
  onChange: (value: IntakeState) => void
  onSubmit: (payload: TriagePayload) => void
}

function initialFactState(): Record<string, FactValue> {
  return Object.fromEntries(factDefinitions.map(([id]) => [id, "unknown"]))
}

export function fromScenario(key: ScenarioKey): IntakeState {
  const scenario = scenarios[key]
  return {
    scenario: key,
    summary: scenario.summary,
    facts: { ...initialFactState(), ...scenario.facts },
    selectionEnabled: scenario.selectionEnabled,
    service: scenario.service,
    component: scenario.component,
    changeContext: scenario.changeContext,
    signals: [...scenario.signals],
  }
}

function toPayload(value: IntakeState): TriagePayload {
  const scenario = scenarios[value.scenario]
  const observed_facts = Object.entries(value.facts)
    .filter(([, status]) => status !== "unknown")
    .map(([fact, status]) => ({
      fact,
      status: status as "confirmed" | "contradicted",
    }))

  return {
    input_summary: value.summary.trim(),
    observed_facts,
    provider_available: scenario.providerAvailable,
    ...(value.selectionEnabled
      ? {
          representative_selection_intake: {
            service: value.service,
            component: value.component,
            change_context: value.changeContext,
            operational_signal_families: value.signals,
            contradicted_signal_families: [],
          },
        }
      : {}),
  }
}

export function IncidentIntake({
  value,
  pending,
  requestError,
  onChange,
  onSubmit,
}: Props) {
  function update(patch: Partial<IntakeState>) {
    onChange({ ...value, ...patch })
  }

  function selectScenario(key: ScenarioKey) {
    onChange(fromScenario(key))
  }

  function updateFact(fact: string, status: FactValue) {
    onChange({ ...value, facts: { ...value.facts, [fact]: status } })
  }

  function toggleSignal(signal: string) {
    onChange({
      ...value,
      signals: value.signals.includes(signal)
        ? value.signals.filter((item) => item !== signal)
        : [...value.signals, signal],
    })
  }

  function submit() {
    const payload = toPayload(value)
    if (!payload.input_summary) return
    onSubmit(payload)
  }

  return (
    <Card className="h-fit bg-slate-950/80">
      <CardHeader className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle>Review the current incident</CardTitle>
            <CardDescription className="mt-1">
              Choose a safe demo scenario or describe a sanitized incident. The system
              will show what is safe to review and what still needs human judgment.
            </CardDescription>
          </div>
          <ShieldCheck className="h-5 w-5 shrink-0 text-sky-300" />
        </div>
        <div className="flex flex-wrap gap-2">
          {(Object.keys(scenarios) as ScenarioKey[]).map((key) => (
            <Button
              key={key}
              type="button"
              size="sm"
              variant={value.scenario === key ? "default" : "secondary"}
              onClick={() => selectScenario(key)}
            >
              {scenarios[key].label}
            </Button>
          ))}
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-slate-100" htmlFor="summary">
            What is happening right now?
          </label>
          <p className="text-xs leading-5 text-slate-400">
            Use a short sanitized summary. Do not paste credentials, customer
            identifiers, or raw logs.
          </p>
          <textarea
            id="summary"
            value={value.summary}
            onChange={(event) => update({ summary: event.target.value })}
            className="min-h-32 w-full resize-y rounded-xl border border-slate-700 bg-slate-900 px-3 py-3 text-sm leading-6 text-slate-100 outline-none ring-0 placeholder:text-slate-500 focus:border-sky-400"
          />
        </div>

        <Accordion
          type="single"
          collapsible
          defaultValue="facts"
          className="rounded-xl border border-slate-800 px-4"
        >
          <AccordionItem value="facts" className="border-none">
            <AccordionTrigger>
              <span className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-sky-300" />
                What have we confirmed?
              </span>
            </AccordionTrigger>
            <AccordionContent>
              <p className="mb-4 text-xs leading-5 text-slate-400">
                Mark a fact as confirmed when you observed it, ruled out when you
                checked and rejected it, or leave it as not checked when it has not
                been verified.
              </p>
              <div className="space-y-2">
                {factDefinitions.map(([fact, label]) => (
                  <div
                    key={fact}
                    className="grid grid-cols-[1fr_132px] items-center gap-3 rounded-lg px-1 py-1.5"
                  >
                    <span className="text-sm text-slate-300">{label}</span>
                    <select
                      aria-label={label}
                      value={value.facts[fact] ?? "unknown"}
                      onChange={(event) =>
                        updateFact(fact, event.target.value as FactValue)
                      }
                      className="h-9 rounded-lg border border-slate-700 bg-slate-900 px-2 text-sm text-slate-100 outline-none focus:border-sky-400"
                    >
                      <option value="unknown">Not checked yet</option>
                      <option value="confirmed">Confirmed</option>
                      <option value="contradicted">Ruled out</option>
                    </select>
                  </div>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>

        <Accordion
          type="single"
          collapsible
          className="rounded-xl border border-slate-800 px-4"
        >
          <AccordionItem value="advanced" className="border-none">
            <AccordionTrigger>
              <span className="flex items-center gap-2">
                <ChevronRight className="h-4 w-4 text-slate-400" />
                Advanced: choose the closest past example
              </span>
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4">
                <p className="text-xs leading-5 text-slate-400">
                  Optional. This only changes which already-approved past example is
                  highlighted. It cannot change the conclusion, missing facts,
                  procedure posture, or safety limits.
                </p>
                <label className="flex cursor-pointer items-center justify-between gap-3 rounded-lg bg-slate-900/80 px-3 py-2 text-sm text-slate-200">
                  <span>Highlight the closest approved past example</span>
                  <input
                    type="checkbox"
                    checked={value.selectionEnabled}
                    onChange={(event) =>
                      update({ selectionEnabled: event.target.checked })
                    }
                    className="h-4 w-4 accent-sky-400"
                  />
                </label>
                <div
                  className={
                    value.selectionEnabled
                      ? "space-y-4"
                      : "pointer-events-none space-y-4 opacity-45"
                  }
                >
                  <div className="grid gap-4 sm:grid-cols-[minmax(0,1.35fr)_minmax(0,0.9fr)]">
                    <label className="space-y-1 text-xs font-semibold text-slate-300 sm:col-span-2">
                      Service
                      <ChoiceSelect
                        label="Service"
                        value={value.service}
                        choices={services}
                        onValueChange={(service) => update({ service })}
                      />
                    </label>
                    <label className="space-y-1 text-xs font-semibold text-slate-300">
                      Component
                      <ChoiceSelect
                        label="Component"
                        value={value.component}
                        choices={components}
                        onValueChange={(component) => update({ component })}
                      />
                    </label>
                    <label className="space-y-1 text-xs font-semibold text-slate-300">
                      Change context
                      <ChoiceSelect
                        label="Change context"
                        value={value.changeContext}
                        choices={changeContexts}
                        onValueChange={(changeContext) => update({ changeContext })}
                      />
                    </label>
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {signalDefinitions.map(([signal, label]) => (
                      <label
                        key={signal}
                        className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2 text-xs text-slate-300"
                      >
                        <input
                          type="checkbox"
                          checked={value.signals.includes(signal)}
                          onChange={() => toggleSignal(signal)}
                          className="h-4 w-4 accent-sky-400"
                        />
                        {label}
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>

        <div className="flex items-center justify-between gap-3">
          <Badge variant="neutral">Local synthetic demo</Badge>
          <Button
            type="button"
            disabled={pending || !value.summary.trim()}
            onClick={submit}
            className="min-w-48"
          >
            {pending ? "Checking evidence…" : "Check the evidence safely"}
          </Button>
        </div>

        {requestError ? (
          <div
            role="alert"
            className="flex items-start gap-2 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-3 text-sm leading-5 text-rose-50"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{requestError}</span>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
