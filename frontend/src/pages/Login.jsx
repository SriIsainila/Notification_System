import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form.email, form.password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Something went wrong. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-sm mx-auto px-6 py-20">
      <h1 className="font-display text-3xl font-bold mb-2">Welcome back</h1>
      <p className="text-muted mb-8 text-sm">Log in to see what's dropped in price.</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm text-muted mb-1.5">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full bg-night-surface border border-white/10 rounded-lg px-4 py-2.5 focus-ring outline-none"
            placeholder="you@example.com"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm text-muted mb-1.5">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="w-full bg-night-surface border border-white/10 rounded-lg px-4 py-2.5 focus-ring outline-none"
            placeholder="••••••••"
          />
        </div>

        {error && <p className="text-coral text-sm">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-gold text-night font-semibold py-2.5 rounded-full hover:bg-gold-soft transition-colors focus-ring disabled:opacity-60"
        >
          {loading ? 'Logging in…' : 'Log in'}
        </button>
      </form>

      <p className="text-sm text-muted mt-6 text-center">
        New to Nilify?{' '}
        <Link to="/register" className="text-gold hover:text-gold-soft focus-ring rounded">
          Create an account
        </Link>
      </p>
    </div>
  )
}
