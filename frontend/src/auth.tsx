import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api, post, errorMessage } from './api'
import type { User } from './types'

interface AuthState { user: User | null; loading: boolean; error: string; authenticate: (action: 'signup' | 'signin', username: string, password: string) => Promise<void>; signout: () => Promise<void> }
const AuthContext = createContext<AuthState>(null!)
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  useEffect(() => { api<{ user: User | null }>('session/').then(r => setUser(r.user)).catch(e => setError(errorMessage(e))).finally(() => setLoading(false)) }, [])
  async function authenticate(action: 'signup' | 'signin', username: string, password: string) {
    await api('session/')
    const result = await post<{ user: User }>(`auth/${action}/`, { username, password })
    setUser(result.user); setError('')
  }
  async function signout() { await post('auth/signout/'); setUser(null) }
  return <AuthContext.Provider value={{ user, loading, error, authenticate, signout }}>{children}</AuthContext.Provider>
}
export function useAuth() { return useContext(AuthContext) }
