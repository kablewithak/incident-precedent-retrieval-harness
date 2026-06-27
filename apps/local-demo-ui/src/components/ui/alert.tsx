import * as React from "react"
import { cn } from "@/lib/utils"

function Alert({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div role="alert" className={cn("relative w-full rounded-xl border border-amber-400/35 bg-amber-400/10 px-4 py-3 text-sm text-amber-50", className)} {...props} /> }
function AlertTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) { return <h5 className={cn("mb-1 font-semibold tracking-tight", className)} {...props} /> }
function AlertDescription({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={cn("leading-5 text-amber-100/90", className)} {...props} /> }

export { Alert, AlertTitle, AlertDescription }
