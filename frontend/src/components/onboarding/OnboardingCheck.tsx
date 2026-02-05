import { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { useOnboardingStore } from '@/stores/onboardingStore'
import { Loader2 } from 'lucide-react'

export default function OnboardingCheck({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, isLoading: authLoading } = useAuthStore()
    const { checkStatus } = useOnboardingStore()
    const [isChecking, setIsChecking] = useState(true)
    const [isComplete, setIsComplete] = useState(false)
    const location = useLocation()

    useEffect(() => {
        const verify = async () => {
            if (isAuthenticated) {
                const complete = await checkStatus()
                setIsComplete(complete)
            }
            setIsChecking(false)
        }

        if (!authLoading) {
            verify()
        }
    }, [isAuthenticated, authLoading, checkStatus])

    if (authLoading || isChecking) {
        return (
            <div className="h-screen flex items-center justify-center bg-background">
                <Loader2 className="w-8 h-8 text-primary animate-spin" />
            </div>
        )
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    // If on onboarding route but already complete, go to chat
    if (location.pathname.startsWith('/onboarding') && isComplete) {
        return <Navigate to="/chat" replace />
    }

    // If on normal route but incomplete, go to onboarding
    // EXCEPTION: Don't redirect if we are ALREADY on onboarding
    if (!location.pathname.startsWith('/onboarding') && !isComplete) {
        return <Navigate to="/onboarding" replace />
    }

    return <>{children}</>
}
