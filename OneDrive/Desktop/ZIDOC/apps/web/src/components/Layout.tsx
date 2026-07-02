import { Outlet } from "react-router-dom"
import { useAppStore } from "../store/useAppStore"
import Sidebar from "./Sidebar"
import Navbar from "./Navbar"
import Footer from "./Footer"

export default function Layout() {
  const { sidebarOpen } = useAppStore()

  return (
    <div className="min-h-screen bg-background text-foreground flex">
      {/* Navigation Sidebar */}
      <Sidebar />

      {/* Main Viewport Container */}
      <div
        className={`flex-1 flex flex-col min-w-0 transition-all duration-300 ${
          sidebarOpen ? "md:pl-64" : "md:pl-16"
        }`}
      >
        <Navbar />

        <main className="flex-1 p-6 md:p-8 overflow-y-auto">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>

        <Footer />
      </div>
    </div>
  )
}
