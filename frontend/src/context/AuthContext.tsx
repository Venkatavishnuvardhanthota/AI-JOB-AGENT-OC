import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import { api } from '../api/client'
import type { User } from '../types'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>
  register: (email: string, password: string, firstName: string, lastName: string) => Promise<void>
  logout: () => Promise<void>
  forgotPassword: (email: string) => Promise<void>
  resetPassword: (token: string, newPassword: string) => Promise<void>
  verifyEmail: (token: string) => Promise<void>
  resendVerification: (email: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setIsLoading(false)
      return
    }
    try {
      const res = await api.get<any>('/auth/me')
      const userData = res?.data ?? res
      setUser(userData as User)
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const login = useCallback(
    async (email: string, password: string, rememberMe?: boolean) => {
      const res = await api.post<any>('/auth/login', { email, password })
      const tokens = res?.data ?? res
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
      if (rememberMe) {
        localStorage.setItem('remembered_email', email)
      } else {
        localStorage.removeItem('remembered_email')
      }
      const userRes = await api.get<any>('/auth/me')
      const userData = userRes?.data ?? userRes
      setUser(userData as User)
    },
    [],
  )

  const register = useCallback(
    async (email: string, password: string, firstName: string, lastName: string) => {
      await api.post('/auth/register', {
        email,
        password,
        first_name: firstName,
        last_name: lastName,
      })
      await login(email, password)
    },
    [login],
  )

  const logout = useCallback(async () => {
    const refreshToken = localStorage.getItem('refresh_token')
    try {
      if (refreshToken) {
        await api.post('/auth/logout', { refresh_token: refreshToken })
      }
    } catch {
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      setUser(null)
    }
  }, [])

  const forgotPassword = useCallback(async (email: string) => {
    await api.post('/auth/forgot-password', { email })
  }, [])

  const resetPassword = useCallback(async (token: string, newPassword: string) => {
    await api.post('/auth/reset-password', { token, new_password: newPassword })
  }, [])

  const verifyEmail = useCallback(async (token: string) => {
    await api.post('/auth/verify-email', { token })
  }, [])

  const resendVerification = useCallback(async (email: string) => {
    await api.post('/auth/resend-verification', { email })
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        forgotPassword,
        resetPassword,
        verifyEmail,
        resendVerification,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
