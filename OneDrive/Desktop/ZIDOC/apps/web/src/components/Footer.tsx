export default function Footer() {
  return (
    <footer className="mt-auto border-t border-white/5 bg-background py-4 px-6">
      <div className="flex flex-col sm:flex-row justify-between items-center gap-2 text-xs text-muted-foreground">
        <span>&copy; 2026 Zidoc platform. Distributed System Core.</span>
        <div className="flex gap-4">
          <a href="#" className="hover:text-white transition-colors">Privacy</a>
          <a href="#" className="hover:text-white transition-colors">Terms</a>
          <span className="font-mono text-white/40">v1.0.0-foundation</span>
        </div>
      </div>
    </footer>
  )
}
