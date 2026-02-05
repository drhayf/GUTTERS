import type { ReactNode } from 'react'
import { AnimatePresence } from 'framer-motion'

interface OnboardingLayoutProps {
    children: ReactNode
}

export default function OnboardingLayout({ children }: OnboardingLayoutProps) {
    return (
        <div className="min-h-screen bg-background text-foreground flex flex-col relative overflow-hidden selection:bg-primary/20">
            {/* Background Ambience */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/5 blur-[120px] rounded-full mix-blend-screen" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-blue-500/5 blur-[120px] rounded-full mix-blend-screen" />
            </div>

            {/* Header / Brand - Minimal */}
            <header className="relative z-10 p-6 flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <div className="w-6 h-6 bg-primary rounded opacity-90" />
                    <span className="font-bold tracking-tight text-lg">GUTTERS</span>
                </div>
            </header>

            {/* Content Container */}
            <main className="flex-1 flex flex-col items-center justify-center relative z-10 p-4 md:p-8">
                <div className="w-full max-w-2xl">
                    <AnimatePresence mode="wait">
                        {children}
                    </AnimatePresence>
                </div>
            </main>
        </div>
    )
}
