import * as React from "react"
import { cn } from "@/lib/utils"

function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={cn("rounded-2xl border border-slate-800 bg-slate-950/65 text-slate-100 shadow-sm", className)} {...props} /> }
function CardHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={cn("flex flex-col space-y-1.5 p-5", className)} {...props} /> }
function CardTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) { return <h3 className={cn("text-base font-semibold tracking-tight text-white", className)} {...props} /> }
function CardDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) { return <p className={cn("text-sm leading-6 text-slate-400", className)} {...props} /> }
function CardContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={cn("p-5 pt-0", className)} {...props} /> }
function CardFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) { return <div className={cn("flex items-center p-5 pt-0", className)} {...props} /> }

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
