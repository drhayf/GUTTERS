import { create } from 'zustand'
import api from '@/lib/api'

interface User {
    id: number
    email: string
    name?: string
    username: string
}

interface AuthState {
    user: User | null
    isAuthenticated: boolean
    isLoading: boolean

    login: (formData: FormData) => Promise<void>
    logout: () => Promise<void>
    checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    isAuthenticated: false,
    isLoading: true,

    login: async (formData) => {
        const { data } = await api.post('/api/v1/login', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        })
        localStorage.setItem('access_token', data.access_token)

        // Fetch profile
        const { data: user } = await api.get('/api/v1/user/me/')
        set({ user, isAuthenticated: true })
    },

    logout: async () => {
        try {
            await api.post('/api/v1/logout')
        } finally {
            localStorage.removeItem('access_token')
            set({ user: null, isAuthenticated: false })
        }
    },

    checkAuth: async () => {
        try {
            const token = localStorage.getItem('access_token')
            if (!token) {
                set({ isLoading: false })
                return
            }

            const { data } = await api.get('/api/v1/user/me/')
            set({ user: data, isAuthenticated: true, isLoading: false })
        } catch {
            set({ user: null, isAuthenticated: false, isLoading: false })
        }
    }
}))
