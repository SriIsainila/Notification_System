import { createContext, useContext, useState, useEffect } from 'react'
import { loginUser, registerUser } from '../api/auth.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('nilify_token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const storedUser = localStorage.getItem('nilify_user')
    if (storedUser) setUser(JSON.parse(storedUser))
    setLoading(false)
  }, [])

  async function login(email, password) {
    const data = await loginUser({ email, password })
    setToken(data.token)
    setUser(data.user)
    localStorage.setItem('nilify_token', data.token)
    localStorage.setItem('nilify_user', JSON.stringify(data.user))
    return data
  }

  async function register(name, email, password) {
    const data = await registerUser({ name, email, password })
    return data
  }

  function logout() {
    setUser(null)
    setToken(null)
    localStorage.removeItem('nilify_token')
    localStorage.removeItem('nilify_user')
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
