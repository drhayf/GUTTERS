import { useEffect, useState } from 'react'
import { useOnboardingStore } from '@/stores/onboardingStore'
import { motion } from 'framer-motion'
import { CheckCircle2, Circle, Loader2 } from 'lucide-react'
import { Progress } from '@/components/ui/progress'

export default function CalculationStep() {
    const { fetchModules, modules, calculateProfile, setStep, calculationResult } = useOnboardingStore()
    const [progress, setProgress] = useState(0)
    const [activeModuleIndex, setActiveModuleIndex] = useState(0)

    useEffect(() => {
        fetchModules()
    }, [])

    useEffect(() => {
        if (modules.length > 0 && activeModuleIndex < modules.length) {
            // Simulation of progress for current module
            const interval = setInterval(() => {
                setProgress(p => {
                    if (p >= 100) {
                        clearInterval(interval)
                        setActiveModuleIndex(i => i + 1)
                        return 0
                    }
                    return p + 2 // Speed of simulation
                })
            }, 30)
            return () => clearInterval(interval)
        } else if (modules.length > 0 && activeModuleIndex >= modules.length) {
            // All visualization done, trigger actual calculation if not already
            if (!calculationResult) {
                calculateProfile().then(() => {
                    setTimeout(() => setStep('genesis'), 1000)
                })
            }
        }
    }, [modules, activeModuleIndex, calculationResult])

    const totalProgress = modules.length > 0
        ? ((activeModuleIndex / modules.length) * 100) + (progress / modules.length)
        : 0

    return (
        <div className="flex flex-col gap-10 w-full max-w-lg mx-auto">
            <div className="text-center space-y-2">
                <h2 className="text-2xl font-bold">Resonating with Cosmic Data</h2>
                <p className="text-muted-foreground animate-pulse">
                    {activeModuleIndex < modules.length
                        ? `Activating ${modules[activeModuleIndex]?.display_name || 'Modules'}...`
                        : "Synthesizing Profile..."}
                </p>
            </div>

            {/* Main Progress Bar */}
            <Progress value={totalProgress} className="h-2" />

            {/* Module List */}
            <div className="grid gap-3">
                {modules.map((mod, idx) => {
                    const isActive = idx === activeModuleIndex
                    const isCompleted = idx < activeModuleIndex

                    return (
                        <motion.div
                            key={mod.name}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            className={`p-4 rounded-lg border border-border transition-all duration-300 flex items-center gap-4 ${isActive ? 'bg-primary/5 border-primary/50 scale-[1.02] shadow-lg' :
                                    isCompleted ? 'bg-card/50 opacity-60' : 'bg-card opacity-40'
                                }`}
                        >
                            <div className="shrink-0">
                                {isCompleted ? (
                                    <CheckCircle2 className="w-5 h-5 text-primary" />
                                ) : isActive ? (
                                    <Loader2 className="w-5 h-5 text-primary animate-spin" />
                                ) : (
                                    <Circle className="w-5 h-5 text-muted-foreground" />
                                )}
                            </div>

                            <div className="flex-1">
                                <div className="flex justify-between items-center mb-1">
                                    <span className="font-semibold">{mod.display_name}</span>
                                    {isActive && <span className="text-xs text-primary font-mono">{Math.round(progress)}%</span>}
                                </div>
                                <p className="text-xs text-muted-foreground">{mod.description}</p>

                                {isActive && (
                                    <div className="h-1 w-full bg-primary/10 rounded-full mt-2 overflow-hidden">
                                        <motion.div
                                            className="h-full bg-primary"
                                            style={{ width: `${progress}%` }}
                                        />
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    )
                })}
            </div>
        </div>
    )
}
