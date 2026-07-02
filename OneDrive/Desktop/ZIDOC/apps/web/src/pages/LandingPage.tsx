import { Link } from "react-router-dom"
import { Shield, Sparkles, Workflow, ArrowRight, CheckCircle2, FileText, Database, Activity } from "lucide-react"

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background text-foreground selection:bg-primary/30 selection:text-white">
      {/* Background Decorative Blobs */}
      <div className="absolute top-[-20%] left-[-10%] h-[600px] w-[600px] rounded-full bg-primary/10 blur-[120px] animate-pulse-slow" />
      <div className="absolute bottom-[-10%] right-[-10%] h-[600px] w-[600px] rounded-full bg-indigo-500/5 blur-[120px]" />

      {/* Header */}
      <header className="sticky top-0 z-50 w-full glass border-b border-white/5 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-tr from-primary to-indigo-500 shadow-lg shadow-primary/20">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">
              Zidoc<span className="text-primary font-light">.</span>
            </span>
          </div>

          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#platform" className="hover:text-white transition-colors">Platform</a>
            <a href="#compliance" className="hover:text-white transition-colors">Security</a>
          </nav>

          <div className="flex items-center gap-4">
            <Link
              to="/dashboard"
              className="inline-flex h-9 items-center justify-center rounded-md bg-white/5 px-4 text-sm font-medium text-white border border-white/10 hover:bg-white/10 transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/dashboard"
              className="inline-flex h-9 items-center justify-center rounded-md bg-gradient-to-r from-primary to-indigo-500 px-4 text-sm font-medium text-white shadow-lg shadow-primary/20 hover:brightness-110 transition-all gap-1.5"
            >
              Start Free <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative mx-auto max-w-7xl px-4 pt-20 pb-16 sm:px-6 lg:px-8 lg:pt-32">
        <div className="text-center">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary mb-6 animate-fade-in">
            <Sparkles className="h-3 w-3" /> Introducing Zidoc 1.0 Foundation
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-6xl lg:text-7xl max-w-5xl mx-auto leading-[1.1] animate-fade-in">
            AI-Powered Document Collection & <span className="text-gradient">Workflow Automation</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground animate-fade-in">
            Automate document intake, run instant compliance screenings, and construct complex verification pipelines in a secure, enterprise-ready environment.
          </p>
          <div className="mt-10 flex justify-center gap-4 animate-fade-in">
            <Link
              to="/dashboard"
              className="inline-flex h-11 items-center justify-center rounded-lg bg-gradient-to-r from-primary to-indigo-500 px-6 font-medium text-white shadow-lg shadow-primary/25 hover:brightness-110 transition-all gap-2"
            >
              Launch Dashboard <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="#features"
              className="inline-flex h-11 items-center justify-center rounded-lg bg-white/5 px-6 font-medium text-white border border-white/10 hover:bg-white/10 transition-colors"
            >
              Explore Features
            </a>
          </div>
        </div>

        {/* Visual Mockup */}
        <div className="relative mt-20 rounded-xl border border-white/10 bg-black/40 p-4 shadow-2xl backdrop-blur-sm glow-purple animate-fade-in">
          <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent z-10" />
          <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
            <div className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-full bg-red-500/80" />
              <span className="h-3 w-3 rounded-full bg-yellow-500/80" />
              <span className="h-3 w-3 rounded-full bg-green-500/80" />
            </div>
            <span className="text-xs text-muted-foreground font-mono">zidoc-workspace-preview.web</span>
            <div className="w-12" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 h-[350px]">
            <div className="rounded-lg bg-white/5 border border-white/5 p-4 flex flex-col justify-between">
              <div className="space-y-4">
                <div className="h-4 w-2/3 bg-white/10 rounded" />
                <div className="h-8 w-full bg-white/5 rounded" />
                <div className="h-8 w-full bg-white/5 rounded" />
                <div className="h-8 w-full bg-white/5 rounded" />
              </div>
              <div className="h-8 w-full bg-primary/20 rounded border border-primary/30" />
            </div>
            <div className="col-span-3 rounded-lg bg-white/5 border border-white/5 p-6 flex flex-col justify-between">
              <div className="flex items-start justify-between">
                <div className="space-y-2">
                  <div className="h-6 w-[200px] bg-white/10 rounded" />
                  <div className="h-4 w-[300px] bg-white/5 rounded" />
                </div>
                <div className="h-6 w-20 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded flex items-center justify-center text-xs font-bold">
                  Active
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="h-24 bg-white/5 rounded border border-white/5 p-3 flex flex-col justify-between">
                  <FileText className="h-5 w-5 text-indigo-400" />
                  <div className="h-3 w-2/3 bg-white/10 rounded" />
                </div>
                <div className="h-24 bg-white/5 rounded border border-white/5 p-3 flex flex-col justify-between">
                  <Database className="h-5 w-5 text-purple-400" />
                  <div className="h-3 w-1/2 bg-white/10 rounded" />
                </div>
                <div className="h-24 bg-white/5 rounded border border-white/5 p-3 flex flex-col justify-between">
                  <Activity className="h-5 w-5 text-blue-400" />
                  <div className="h-3 w-3/4 bg-white/10 rounded" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8 border-t border-white/5">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Designed for Modern Enterprise Standards
          </h2>
          <p className="mt-4 text-muted-foreground">
            A modular monolith architecture that optimizes execution speeds, maintains system auditability, and integrates compliance out of the box.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-8 hover:bg-white/[0.04] transition-all hover:scale-[1.02]">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-6">
              <Shield className="h-6 w-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Audit & Traceability</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Every request is stamped with a unique trace ID and logged structured with transaction details, audit events, and caller context.
            </p>
          </div>

          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-8 hover:bg-white/[0.04] transition-all hover:scale-[1.02]">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20 mb-6">
              <Workflow className="h-6 w-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Clean Architecture</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Strict separations of concerns. Domain entities are fully decoupled from framework layers to permit frictionless expansion.
            </p>
          </div>

          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-8 hover:bg-white/[0.04] transition-all hover:scale-[1.02]">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 mb-6">
              <Sparkles className="h-6 w-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Multi-Service Sync</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Unified telemetry across our Go API backend, FastAPI AI analysis system, and React web interface.
            </p>
          </div>
        </div>
      </section>

      {/* Compliance / Enterprise Section */}
      <section id="compliance" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 border-t border-white/5 bg-gradient-to-b from-transparent to-primary/[0.02]">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-white mb-6">
              High Performance & Reliability
            </h2>
            <div className="space-y-4">
              <div className="flex gap-3">
                <CheckCircle2 className="h-6 w-6 text-emerald-400 shrink-0" />
                <div>
                  <h4 className="text-white font-medium">PostgreSQL Connection Pooling</h4>
                  <p className="text-muted-foreground text-sm">GORM-backed pool management with pgx optimized for low-latency queries.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <CheckCircle2 className="h-6 w-6 text-emerald-400 shrink-0" />
                <div>
                  <h4 className="text-white font-medium">Redis Core Integration</h4>
                  <p className="text-muted-foreground text-sm">Session store and cache engine with automated readiness checks.</p>
                </div>
              </div>
              <div className="flex gap-3">
                <CheckCircle2 className="h-6 w-6 text-emerald-400 shrink-0" />
                <div>
                  <h4 className="text-white font-medium">Containerized Deployment</h4>
                  <p className="text-muted-foreground text-sm">Local docker-compose setup and complete Kubernetes Kustomize manifests.</p>
                </div>
              </div>
            </div>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-8 space-y-6">
            <h3 className="text-lg font-bold text-white">System Telemetry status</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                <span className="text-muted-foreground">Go API Gateway</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-400" />Healthy</span>
              </div>
              <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                <span className="text-muted-foreground">FastAPI AI service</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-400" />Healthy</span>
              </div>
              <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
                <span className="text-muted-foreground">Database Pool</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-400" />25 Conns</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span className="text-muted-foreground">Redis Client</span>
                <span className="text-emerald-400 font-mono flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-emerald-400" />Connected</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8 border-t border-white/5">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-primary to-indigo-500">
              <Shield className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight text-white">Zidoc</span>
          </div>
          <span className="text-xs text-muted-foreground">
            &copy; 2026 Zidoc Technologies Inc. All rights reserved.
          </span>
        </div>
      </footer>
    </div>
  )
}
