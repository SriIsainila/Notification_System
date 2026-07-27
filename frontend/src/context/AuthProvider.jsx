import { useCallback, useEffect, useMemo, useState } from 'react'
import { getCurrentUser, loginUser, logoutUser, registerUser } from '../services/authService.js'
import { AuthContext } from './authContext.js'

export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const clearSession = useCallback(() => {
    setUser(null)
  }, [])

  useEffect(() => {
    window.addEventListener('auth:unauthorized', clearSession)
    return () => window.removeEventListener('auth:unauthorized', clearSession)
  }, [clearSession])

  useEffect(() => {
    let active = true

    async function restoreSession() {
      try {
        const currentUser = await getCurrentUser()
        if (active) setUser(currentUser)
      } catch {
        if (active) clearSession()
      } finally {
        if (active) setLoading(false)
      }
    }

    restoreSession()
    return () => { active = false }
  }, [clearSession])

  const login = useCallback(async (email, password) => {
    const data = await loginUser({ email, password })
    setUser(data.user)
    return data
  }, [])

  const register = useCallback((name, email, password) => (
    registerUser({ name, email, password })
  ), [])

  const logout = useCallback(async () => {
    clearSession()
    try {
      await logoutUser()
    } catch {
      // Keep the local session cleared if the backend is unavailable.
    }
  }, [clearSession])

  const value = useMemo(() => ({ user, loading, login, register, logout }), [
    user,
    loading,
    login,
    register,
    logout,
  ])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
