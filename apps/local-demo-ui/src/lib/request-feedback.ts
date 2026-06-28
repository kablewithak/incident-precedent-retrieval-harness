export type RequestFeedbackTone = "good" | "bad"

export type RequestFeedback = {
  tone: RequestFeedbackTone
  message: string
  displayMode: "screen_reader_only" | "inline_alert"
}

export function createRequestFeedback(
  tone: RequestFeedbackTone,
  message: string,
): RequestFeedback {
  return {
    tone,
    message,
    displayMode: tone === "good" ? "screen_reader_only" : "inline_alert",
  }
}
