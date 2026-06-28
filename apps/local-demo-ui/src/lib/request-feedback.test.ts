import { describe, expect, it } from "vitest"
import { createRequestFeedback } from "@/lib/request-feedback"

describe("request feedback presentation", () => {
  it("keeps successful evidence-review confirmation out of the visible layout", () => {
    const feedback = createRequestFeedback("good", "Evidence review ready.")

    expect(feedback.displayMode).toBe("screen_reader_only")
    expect(feedback.message).toBe("Evidence review ready.")
  })

  it("keeps a refused request visible next to the intake action", () => {
    const feedback = createRequestFeedback("bad", "The local demo request was refused.")

    expect(feedback.displayMode).toBe("inline_alert")
    expect(feedback.message).toBe("The local demo request was refused.")
  })
})
