import { useEffect } from 'react'
import { useOnboardingStore } from '@/stores/onboardingStore'
import { Button } from '@/components/ui/button'
import { motion } from 'framer-motion'
import { Sparkles, AlertTriangle, ArrowRight } from 'lucide-react'

export default function GenesisStep() {
    const { generateSynthesis, synthesisStream, isSynthesizing, calculationResult } = useOnboardingStore()

    useEffect(() => {
        generateSynthesis()
    }, [])

    const handleComplete = () => {
        // Force reload or redirect to allow OnboardingCheck to update
        window.location.href = '/chat'
    }

    // Extract probabilistic data if any
    const getProbabilisticInfo = () => {
        if (!calculationResult) return []
        const modules = calculationResult.results
        const probModules = []

        if (modules.human_design?.accuracy === 'probabilistic') {
            const bestGuess = modules.human_design.type
            const confidence = modules.human_design.confidence
            probModules.push({
                name: "Human Design",
                msg: `Type estimated as ${bestGuess} (${Math.round(confidence * 100)}% Match).`,
                details: "Birth time unknown. We've sampled 24h of data to form this hypothesis."
            })
        }

        if (modules.astrology?.accuracy === 'probabilistic') {
            const bestGuess = modules.astrology.ascendant?.sign || "Unknown"
            const confidence = modules.astrology.rising_confidence || 0
            probModules.push({
                name: "Astrology",
                msg: `Rising Sign likely ${bestGuess} (${Math.round(confidence * 100)}% Match).`,
                details: "Exact House system and Ascendant degree require precise time. We will refine this through dialogue."
            })
        }

        return probModules
    }

    const probInfo = getProbabilisticInfo()

    return (
        <div className="flex flex-col gap-8 w-full max-w-2xl mx-auto">
            <div className="text-center">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="inline-flex p-3 rounded-full bg-primary/10 mb-4"
                >
                    <Sparkles className="w-8 h-8 text-primary" />
                </motion.div>
                <h2 className="text-3xl font-bold mb-2">Genesis Complete</h2>
                <p className="text-muted-foreground">Your cosmic baseline has been established.</p>
            </div>

            {/* Synthesis Content */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-card border border-border rounded-xl p-6 shadow-sm min-h-[200px]"
            >
                {isSynthesizing ? (
                    <div className="flex items-center justify-center h-full gap-3 text-muted-foreground animate-pulse">
                        <span className="text-lg">Weaving synthesis threads...</span>
                    </div>
                ) : (
                    <div className="prose dark:prose-invert max-w-none">
                        <p className="text-lg leading-relaxed">{synthesisStream}</p>
                    </div>
                )}
            </motion.div>

            {/* Probabilistic Warnings / Hypothesis UI */}
            {probInfo.length > 0 && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1 }}
                    className="flex flex-col gap-3"
                >
                    <div className="flex items-center gap-2 text-amber-500 mb-2">
                        <AlertTriangle className="w-5 h-5" />
                        <h3 className="font-semibold">Hypothesis Active</h3>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4">
                        {probInfo.map((info, idx) => (
                            <div key={idx} className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                                <h4 className="font-bold text-amber-500 mb-1">{info.name}</h4>
                                <p className="font-medium mb-1">{info.msg}</p>
                                <p className="text-xs text-muted-foreground">{info.details}</p>
                            </div>
                        ))}
                    </div>
                    <p className="text-xs text-center text-muted-foreground mt-2">
                        Don't worry. GUTTERS will refine these hypotheses as we interact.
                    </p>
                </motion.div>
            )}

            <div className="flex justify-center mt-4">
                <Button
                    size="lg"
                    className="px-8"
                    onClick={handleComplete}
                    disabled={isSynthesizing}
                >
                    Enter GUTTERS <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
            </div>
        </div>
    )
}
