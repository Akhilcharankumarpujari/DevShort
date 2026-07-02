import { useAppStore } from "../store/useAppStore"
import { useTheme } from "../context/ThemeContext"
import { Menu, Sun, Moon, Bell, ShieldCheck, User } from "lucide-react"

export default function Navbar() {
  const { sidebarOpen, toggleSidebar } = useAppStore()
  const { theme, setTheme } = useTheme()

  return (
    <header className="sticky top-0 z-10 flex h-16 w-full shrink-0 items-center justify-between border-b border-white/5 bg-background/80 px-6 backdrop-blur-md">
      <div className="flex items-center gap-4">
        {!sidebarOpen && (
          <button
            onClick={toggleSidebar}
            className="rounded-md border border-white/10 p-1.5 text-muted-foreground hover:text-white hover:bg-white/5 md:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-primary" />
          <span className="text-sm font-semibold text-white">Production Gateway</span>
          <span className="hidden sm:inline-flex h-2 w-2 rounded-full bg-emerald-500" />
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Connection status */}
        <div className="hidden md:flex items-center gap-1.5 rounded-full border border-white/10 px-2.5 py-0.5 text-xs text-muted-foreground font-mono">
          API: <span className="text-emerald-400">Connected</span>
        </div>

        {/* Theme Toggle */}
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="rounded-md border border-white/10 p-1.5 text-muted-foreground hover:text-white hover:bg-white/5"
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        {/* Notifications */}
        <button className="relative rounded-md border border-white/10 p-1.5 text-muted-foreground hover:text-white hover:bg-white/5">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-primary" />
        </button>

        {/* User avatar */}
        <div className="h-8 w-8 rounded-full border border-white/10 bg-white/5 flex items-center justify-center text-muted-foreground hover:text-white cursor-pointer hover:bg-white/10">
          <User className="h-4 w-4" />
        </div>
      </div>
    </header>
  )
}
