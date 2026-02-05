import { create } from 'zustand'
import api from '@/lib/api'

export type OnboardingStep = 'welcome' | 'birth-data' | 'calculation' | 'manifesto' | 'genesis'

interface BirthData {
    birth_date: string
    birth_time: string | null
    birth_location: string
    latitude: number
    longitude: number
    timezone: string
    time_unknown: boolean
}

interface ModuleMetadata {
    name: string
    display_name: string
    description: string
    weight: number
    requires_birth_time: boolean
}

interface CalculationResult {
    success: boolean
    modules_calculated: string[]
    results: any
}

interface OnboardingState {
    currentStep: OnboardingStep
    birthData: BirthData | null
    modules: ModuleMetadata[]
    calculationResult: CalculationResult | null
    isCalculating: boolean
    isSynthesizing: boolean
    synthesisStream: string
    error: string | null

    setStep: (step: OnboardingStep) => void
    setBirthData: (data: BirthData) => void
    fetchModules: () => Promise<void>
    calculateProfile: () => Promise<void>
    generateSynthesis: () => Promise<void>
    checkStatus: () => Promise<boolean> // Returns true if complete
}

export const useOnboardingStore = create<OnboardingState>((set) => ({
    currentStep: 'welcome',
    birthData: null,
    modules: [],
    calculationResult: null,
    isCalculating: false,
    isSynthesizing: false,
    synthesisStream: '',
    error: null,

    setStep: (step) => set({ currentStep: step }),
    setBirthData: (data) => set({ birthData: data }),

    fetchModules: async () => {
        try {
            const { data } = await api.get('/api/v1/profile/modules')
            set({ modules: data.modules })
        } catch (err) {
            console.error('Failed to fetch modules', err)
        }
    },

    checkStatus: async () => {
        try {
            const { data } = await api.get('/api/v1/profile/onboarding-status')
            return data.onboarding_completed
        } catch {
            return false
        }
    },

    calculateProfile: async () => {
        set({ isCalculating: true, error: null })
        try {
            // 1. Submit birth data if not already (or just ensure it's saved)
            // Ideally birth data is submitted in the previous step, calculate just triggers calc
            const { data } = await api.post('/api/v1/profile/calculate')
            set({ calculationResult: data, isCalculating: false })

            // Move to Genesis automatically or let UI handle it?
            // Let UI handle transition based on isCalculating -> false
        } catch (err: any) {
            set({
                error: err.response?.data?.detail || 'Calculation failed',
                isCalculating: false
            })
        }
    },

    generateSynthesis: async () => {
        set({ isSynthesizing: true, synthesisStream: '' })
        try {
            // For now, just a simple get. Streaming would require a different approach (EventSource or similar)
            // The backend /synthesis endpoint runs sync in the test implementation (wait for completion)
            // Implementation plan says "streams the synthesis". 
            // If backend supports streaming, we need fetch API or EventSource.
            // Current backend implementation seems to be synchronous/blocking for the first version based on tests.
            // We will treat it as async request for now.
            const { data } = await api.get('/api/v1/profile/synthesis')
            set({ synthesisStream: data.synthesis.synthesis, isSynthesizing: false })
        } catch (err: any) {
            set({
                error: err.response?.data?.detail || 'Synthesis failed',
                isSynthesizing: false
            })
        }
    }
}))
