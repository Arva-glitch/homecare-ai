import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { authApi } from '../api/services'
import { setUnauthorizedHandler, tokenStore } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setUnauthorizedHandler(() => setUser(null))
    if (!tokenStore.get()) { setLoading(false); return }
    authApi.me().then(setUser).catch(() => tokenStore.clear()).finally(() => setLoading(false))
  }, [])

  const handleToken = useCallback((data) => {
    tokenStore.set(data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  const login = async (email, password) => handleToken(await authApi.login(email, password))
  const register = async (body) => handleToken(await authApi.register(body))
  const logout = async () => {
    try { await authApi.logout() } catch { /* token may already be invalid */ }
    tokenStore.clear()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, register, logout, handleToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
