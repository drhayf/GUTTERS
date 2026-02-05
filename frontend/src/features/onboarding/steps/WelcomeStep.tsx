import { useOnboardingStore } from '@/stores/onboardingStore'
import { Button } from '@/components/ui/button'
import { motion } from 'framer-motion'
import { ArrowRight } from 'lucide-react'

export default function WelcomeStep() {
    const { setStep } = useOnboardingStore()

    return (
        <div className="flex flex-col gap-8 text-center items-center">
            <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="flex flex-col gap-4"
            >
                <h1 className="text-5xl md:text-7xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-br from-foreground to-foreground/50">
                    Know Thyself.
                </h1>
                <p className="text-xl text-muted-foreground max-w-md mx-auto leading-relaxed">
                    GUTTERS unifies Astrology, Human Design, and Numerology into a single source of truth.
                </p>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4, duration: 0.6 }}
                className="p-6 bg-card/50 border border-border/50 rounded-xl backdrop-blur-sm max-w-lg"
            >
                <div className="grid grid-cols-3 gap-6 text-sm">
                    <div className="flex flex-col gap-2">
                        <span className="text-2xl">✨</span>
                        <span className="font-semibold text-foreground/80">Stellar</span>
                        <span className="text-xs text-muted-foreground">Planetary Transits</span>
                    </div>
                    <div className="flex flex-col gap-2">
                        <span className="text-2xl">🧬</span>
                        <span className="font-semibold text-foreground/80">Genetic</span>
                        <span className="text-xs text-muted-foreground">Bodygraph Analysis</span>
                    </div>
                    <div className="flex flex-col gap-2">
                        <span className="text-2xl">🔢</span>
                        <span className="font-semibold text-foreground/80">Numeric</span>
                        <span className="text-xs text-muted-foreground">Vibrational Patterns</span>
                    </div>
                </div>
            </motion.div>

            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
            >
                <Button
                    size="lg"
                    className="h-12 px-8 text-lg rounded-full shadow-[0_0_20px_-5px_rgba(var(--primary),0.5)] hover:shadow-[0_0_25px_-5px_rgba(var(--primary),0.8)] transition-all"
                    onClick={() => setStep('birth-data')}
                >
                    Begin Calibration <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
            </motion.div>
        </div>
    )
}
