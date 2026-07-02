import { Link } from "react-router-dom"
import { ArrowLeft, FileQuestion } from "lucide-react"

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 text-center relative overflow-hidden">
      {/* Glow effect */}
      <div className="absolute h-96 w-96 rounded-full bg-primary/10 blur-[80px]" />

      <div className="max-w-md w-full glass border border-white/5 p-8 rounded-2xl relative z-10 space-y-6">
        <div className="flex justify-center">
          <div className="rounded-xl bg-primary/10 border border-primary/20 p-4">
            <FileQuestion className="h-12 w-12 text-primary" />
          </div>
        </div>
        <div className="space-y-2">
          <h1 className="text-4xl font-extrabold tracking-tight text-white">404</h1>
          <h2 className="text-xl font-bold text-slate-200">Page Not Found</h2>
          <p className="text-sm text-muted-foreground">
            The page you are looking for doesn't exist or has been relocated to another workspace.
          </p>
        </div>
        <div className="pt-2">
          <Link
            to="/"
            className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-6 text-sm font-medium text-white shadow hover:brightness-110 transition-all gap-2 w-full"
          >
            <ArrowLeft className="h-4 w-4" /> Back to Safety
          </Link>
        </div>
      </div>
    </div>
  )
}
