import { FileText, CheckCircle, Clock, AlertTriangle, ArrowUpRight, Search, Filter } from "lucide-react"

export default function Dashboard() {
  const stats = [
    { name: "Total Collections", value: "1,248", icon: FileText, change: "+12.3%", changeType: "positive" },
    { name: "Verified Documents", value: "1,180", icon: CheckCircle, change: "+9.2%", changeType: "positive" },
    { name: "Pending Verification", value: "54", icon: Clock, change: "-4.1%", changeType: "negative" },
    { name: "Failed Matches", value: "14", icon: AlertTriangle, change: "+0.5%", changeType: "neutral" },
  ]

  const mockDocuments = [
    { id: "DOC-8291", name: "Enterprise_License_Agreement.pdf", type: "License", client: "Acme Corp", status: "Verified", date: "2026-07-02" },
    { id: "DOC-8290", name: "VAT_Tax_Certificate_2025.pdf", type: "Tax Form", client: "SaaSify Inc", status: "Pending", date: "2026-07-02" },
    { id: "DOC-8289", name: "Incorporation_Articles_Final.pdf", type: "Corporate", client: "Nova Ventures", status: "Verified", date: "2026-07-01" },
    { id: "DOC-8288", name: "ISO_Security_Certification.pdf", type: "Compliance", client: "Alpha Cloud", status: "Failed", date: "2026-06-30" },
    { id: "DOC-8287", name: "AML_Know_Your_Customer_Verification.pdf", type: "KYC", client: "Zeta Payments", status: "Verified", date: "2026-06-29" },
  ]

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Upper header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Workspace Overview</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Real-time status of document ingestion, AI-extraction pipelines, and validation tasks.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="inline-flex h-9 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-white shadow hover:brightness-110 transition-all">
            Ingest Document
          </button>
        </div>
      </div>

      {/* Grid of stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, i) => {
          const Icon = stat.icon
          return (
            <div key={i} className="rounded-xl border border-white/5 bg-white/[0.02] p-6 shadow-sm flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-muted-foreground">{stat.name}</span>
                <div className="rounded-lg bg-white/5 border border-white/5 p-2">
                  <Icon className="h-5 w-5 text-indigo-400" />
                </div>
              </div>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white tracking-tight">{stat.value}</span>
                <span className={`text-xs font-semibold ${
                  stat.changeType === "positive" ? "text-emerald-400" :
                  stat.changeType === "negative" ? "text-red-400" : "text-slate-400"
                }`}>
                  {stat.change}
                </span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Main content split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Document Ingestion Stream */}
        <div className="lg:col-span-2 rounded-xl border border-white/5 bg-white/[0.02] p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white">Recent Document Ingestions</h3>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search collections..."
                  className="pl-9 h-9 w-48 rounded-md bg-white/5 border border-white/5 text-xs text-white placeholder-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <button className="flex h-9 w-9 items-center justify-center rounded-md bg-white/5 border border-white/5 text-muted-foreground hover:text-white hover:bg-white/10 transition-colors">
                <Filter className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 text-xs text-muted-foreground font-semibold">
                  <th className="pb-3">Doc ID</th>
                  <th className="pb-3">Name</th>
                  <th className="pb-3">Type</th>
                  <th className="pb-3">Client</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3 text-right">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm text-slate-300">
                {mockDocuments.map((doc) => (
                  <tr key={doc.id} className="hover:bg-white/[0.01] transition-colors">
                    <td className="py-3.5 font-mono text-xs text-indigo-400">{doc.id}</td>
                    <td className="py-3.5 font-medium text-white max-w-[200px] truncate">{doc.name}</td>
                    <td className="py-3.5 text-xs">{doc.type}</td>
                    <td className="py-3.5 text-xs">{doc.client}</td>
                    <td className="py-3.5">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium border ${
                        doc.status === "Verified" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                        doc.status === "Pending" ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" :
                        "bg-red-500/10 text-red-400 border-red-500/20"
                      }`}>
                        {doc.status}
                      </span>
                    </td>
                    <td className="py-3.5 text-right text-xs text-muted-foreground">{doc.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Verification Status Summary */}
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-6 space-y-6">
          <h3 className="text-lg font-bold text-white">System Status</h3>
          <div className="space-y-4">
            <div className="rounded-lg bg-white/5 border border-white/5 p-4 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold text-white">Extraction Accuracy</span>
                <span className="text-xs font-bold text-emerald-400">98.4%</span>
              </div>
              <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                <div className="bg-primary h-full rounded-full" style={{ width: "98.4%" }} />
              </div>
            </div>

            <div className="rounded-lg bg-white/5 border border-white/5 p-4 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold text-white">API Response Time</span>
                <span className="text-xs font-bold text-emerald-400">42ms</span>
              </div>
              <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                <div className="bg-indigo-500 h-full rounded-full" style={{ width: "85%" }} />
              </div>
            </div>

            <div className="rounded-lg bg-white/5 border border-white/5 p-4 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-semibold text-white">Storage Utilization</span>
                <span className="text-xs font-bold text-yellow-400">72.3%</span>
              </div>
              <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                <div className="bg-yellow-500/80 h-full rounded-full" style={{ width: "72.3%" }} />
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-primary/20 bg-primary/5 p-4 flex flex-col justify-between h-32">
            <div className="flex justify-between items-start">
              <span className="text-xs font-semibold text-primary uppercase tracking-wider">AI Coprocessor</span>
              <ArrowUpRight className="h-4 w-4 text-primary" />
            </div>
            <div>
              <p className="text-white text-sm font-bold">FastAPI Service Connected</p>
              <p className="text-xs text-muted-foreground mt-0.5">Model version v1.2-distilbert running.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
