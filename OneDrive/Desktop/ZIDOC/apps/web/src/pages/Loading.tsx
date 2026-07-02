import { Shield } from "lucide-react"

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="relative flex flex-col items-center gap-4">
        {/* Glowing backdrop */}
        <div className="absolute h-24 w-24 rounded-full bg-primary/20 blur-[20px] animate-pulse" />

        <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-tr from-primary to-indigo-500 shadow-xl shadow-primary/25">
          <Shield className="h-8 w-8 text-white animate-pulse" />
        </div>
        <span className="text-xs font-mono text-muted-foreground uppercase tracking-widest animate-pulse">
          Loading Workspace...
        </span>
      </div>
    </div>
  )
}
