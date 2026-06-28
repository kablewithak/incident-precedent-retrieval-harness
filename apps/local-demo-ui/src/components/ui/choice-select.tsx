import { Check, ChevronsUpDown } from "lucide-react"
import { useEffect, useId, useRef, useState } from "react"

import { cn } from "@/lib/utils"

type ChoiceSelectProps = {
  label: string
  value: string
  choices: readonly string[]
  onValueChange: (value: string) => void
  className?: string
}

/**
 * Local shadcn-style menu selector for fixed, non-sensitive demo values.
 *
 * This component deliberately replaces browser-native select rendering only in
 * the advanced presentation layer. It does not transform values, add choices,
 * or change the typed triage payload contract.
 */
export function ChoiceSelect({
  label,
  value,
  choices,
  onValueChange,
  className,
}: ChoiceSelectProps) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)
  const menuId = useId()

  useEffect(() => {
    if (!open) return

    function closeWhenOutside(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false)
      }
    }

    document.addEventListener("mousedown", closeWhenOutside)
    document.addEventListener("keydown", closeOnEscape)

    return () => {
      document.removeEventListener("mousedown", closeWhenOutside)
      document.removeEventListener("keydown", closeOnEscape)
    }
  }, [open])

  return (
    <div ref={rootRef} className={cn("relative min-w-0", className)}>
      <button
        aria-controls={menuId}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label={`${label}: ${value}`}
        className="flex h-10 w-full items-center justify-between gap-3 rounded-xl border border-slate-700 bg-slate-900 px-3 text-left text-sm font-medium text-slate-100 shadow-sm outline-none transition hover:border-slate-500 focus:border-sky-400 focus:ring-2 focus:ring-sky-400/20"
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        <span className="min-w-0 truncate" title={value}>
          {value}
        </span>
        <ChevronsUpDown aria-hidden="true" className="h-4 w-4 shrink-0 text-slate-400" />
      </button>

      {open ? (
        <div
          className="absolute z-30 mt-2 max-h-72 w-full min-w-full overflow-y-auto rounded-xl border border-slate-700 bg-slate-950 p-1.5 shadow-2xl shadow-black/45"
          id={menuId}
          role="menu"
        >
          {choices.map((choice) => {
            const selected = choice === value
            return (
              <button
                aria-checked={selected}
                className={cn(
                  "flex min-h-10 w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-sm leading-5 outline-none transition",
                  selected
                    ? "bg-sky-500/20 text-sky-100"
                    : "text-slate-200 hover:bg-slate-800 focus:bg-slate-800",
                )}
                key={choice}
                onClick={() => {
                  onValueChange(choice)
                  setOpen(false)
                }}
                role="menuitemradio"
                type="button"
              >
                <span className="min-w-0 break-words">{choice}</span>
                {selected ? <Check aria-hidden="true" className="h-4 w-4 shrink-0 text-sky-300" /> : null}
              </button>
            )
          })}
        </div>
      ) : null}
    </div>
  )
}
