import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Card, CardContent } from "@/components/ui/card"
import type { TriageEvidencePacket } from "@/lib/contracts"

type Props = { packet: TriageEvidencePacket | null }

export function TechnicalPacket({ packet }: Props) {
  if (!packet) return null
  return <Card className="bg-slate-950/50"><CardContent className="pt-0"><Accordion type="single" collapsible><AccordionItem value="technical" className="border-none"><AccordionTrigger>Inspect technical details</AccordionTrigger><AccordionContent><p className="mb-3 text-xs leading-5 text-slate-400">This is the typed packet returned by the local Python boundary. It is shown for inspection, not browser-side decision making.</p><pre className="max-h-96 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-4 text-xs leading-5 text-slate-300">{JSON.stringify(packet, null, 2)}</pre></AccordionContent></AccordionItem></Accordion></CardContent></Card>
}
