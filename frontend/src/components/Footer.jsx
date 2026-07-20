export default function Footer() {
  return (
    <footer className="border-t border-white/10 mt-24">
      <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted">
        <p>© {new Date().getFullYear()} Nilify. Watch prices, not screens.</p>
        <div className="flex gap-6">
          <a href="#how-it-works" className="hover:text-ink transition-colors focus-ring rounded">
            How it works
          </a>
          <a href="mailto:hello@nilify.app" className="hover:text-ink transition-colors focus-ring rounded">
            Contact
          </a>
        </div>
      </div>
    </footer>
  )
}
