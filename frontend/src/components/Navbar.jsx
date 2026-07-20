import { Link, useNavigate } from 'react-router-dom'
import { Bell, Plus } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <header className="border-b border-white/10 bg-night/80 backdrop-blur sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 focus-ring rounded">
          <span className="w-8 h-8 rounded-full bg-gold flex items-center justify-center">
            <Bell size={16} className="text-night" strokeWidth={2.5} />
          </span>
          <span className="font-display font-bold text-xl tracking-tight">Nilify</span>
        </Link>

        <nav className="flex items-center gap-3">
          {user ? (
            <>
              <Link
                to="/dashboard"
                className="text-sm text-muted hover:text-ink transition-colors focus-ring rounded px-2 py-1"
              >
                Dashboard
              </Link>
              <Link
                to="/add-product"
                className="flex items-center gap-1.5 bg-gold text-night text-sm font-semibold px-4 py-2 rounded-full hover:bg-gold-soft transition-colors focus-ring"
              >
                <Plus size={16} strokeWidth={2.5} />
                Track a product
              </Link>
              <button
                onClick={() => {
                  logout()
                  navigate('/')
                }}
                className="text-sm text-muted hover:text-ink transition-colors focus-ring rounded px-2 py-1"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="text-sm text-muted hover:text-ink transition-colors focus-ring rounded px-2 py-1"
              >
                Log in
              </Link>
              <Link
                to="/register"
                className="bg-gold text-night text-sm font-semibold px-4 py-2 rounded-full hover:bg-gold-soft transition-colors focus-ring"
              >
                Get started
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
