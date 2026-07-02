import { Link, useLocation } from "react-router-dom"
import { useAppStore } from "../store/useAppStore"
import {
  Shield,
  LayoutDashboard,
  FileText,
  Workflow,
  Settings,
  BarChart2,
  ChevronLeft,
  ChevronRight,
  Database
} from "lucide-react"

export default function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useAppStore()
  const location = useLocation()

  const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Collections", href: "/dashboard/collections", icon: FileText },
    { name: "Workflows", href: "/dashboard/workflows", icon: Workflow },
    { name: "Databases", href: "/dashboard/databases", icon: Database },
    { name: "Analytics", href: "/dashboard/analytics", icon: BarChart2 },
    { name: "Settings", href: "/dashboard/settings", icon: Settings },
  ]

  return (
    <div
      className={`fixed inset-y-0 left-0 z-20 flex flex-col border-r border-white/5 bg-background transition-all duration-300 ${
        sidebarOpen ? "w-64" : "w-16"
      }`}
    >
      {/* Sidebar Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-white/5">
        <Link to="/" className="flex items-center gap-2 overflow-hidden">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-tr from-primary to-indigo-500 shadow-md">
            <Shield className="h-4 w-4 text-white" />
          </div>
          {sidebarOpen && (
            <span className="text-lg font-bold tracking-tight text-white transition-opacity duration-300">
              Zidoc<span className="text-primary">.</span>
            </span>
          )}
        </Link>
        {sidebarOpen && (
          <button
            onClick={toggleSidebar}
            className="rounded-md border border-white/10 p-1 text-muted-foreground hover:text-white hover:bg-white/5"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Sidebar Navigation */}
      <nav className="flex-1 space-y-1 px-2 py-4 overflow-y-auto">
        {navigation.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              className={`group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-muted-foreground hover:bg-white/5 hover:text-white border border-transparent"
              }`}
            >
              <Icon className={`h-5 w-5 shrink-0 ${isActive ? "text-primary" : "text-muted-foreground group-hover:text-white"}`} />
              {sidebarOpen && <span className="truncate">{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Sidebar Collapse Toggle (When Collapsed) */}
      {!sidebarOpen && (
        <div className="flex h-12 items-center justify-center border-t border-white/5">
          <button
            onClick={toggleSidebar}
            className="rounded-md border border-white/10 p-1 text-muted-foreground hover:text-white hover:bg-white/5"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  )
}
