import type { TriagePayload, TriageResponse } from "@/lib/contracts"

export class LocalDemoApiError extends Error {}

export async function requestTriage(payload: TriagePayload): Promise<TriageResponse> {
  const response = await fetch("/api/triage", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok || !body || typeof body !== "object" || (body as { status?: unknown }).status !== "ok") {
    const safeMessage = body && typeof body === "object" && "safe_message" in body && typeof (body as { safe_message?: unknown }).safe_message === "string"
      ? (body as { safe_message: string }).safe_message
      : "The local demo could not safely create an evidence packet."
    throw new LocalDemoApiError(safeMessage)
  }
  return body as TriageResponse
}
