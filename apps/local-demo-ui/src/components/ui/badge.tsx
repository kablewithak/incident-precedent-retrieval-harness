import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex w-fit items-center rounded-full border px-2.5 py-1 text-xs font-semibold leading-none",
  {
    variants: {
      variant: {
        positive: "border-emerald-400/40 bg-emerald-400/10 text-emerald-200",
        warning: "border-amber-300/40 bg-amber-300/10 text-amber-100",
        critical: "border-rose-400/40 bg-rose-400/10 text-rose-100",
        neutral: "border-slate-600 bg-slate-800 text-slate-200",
      },
    },
    defaultVariants: { variant: "neutral" },
  },
)

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
