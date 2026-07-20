// These call your Express backend (see backend/src/routes/authRoutes.js),
// which handles password hashing and JWT creation before touching Supabase.

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

export async function registerUser({ name, email, password }) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.message || 'Registration failed')
  }
  return res.json()
}

export async function loginUser({ email, password }) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.message || 'Login failed')
  }
  return res.json() // expected: { token, user }
}
