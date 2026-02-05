import { useRegisterSW } from 'virtual:pwa-register/react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles } from 'lucide-react'

export default function ReloadPrompt() {
    const {
        needRefresh: [needRefresh, setNeedRefresh],
        updateServiceWorker,
    } = useRegisterSW({
        onRegistered(r: any) {
            console.log('SW Registered: ' + r)
        },
        onRegisterError(error: any) {
            console.log('SW registration error', error)
        },
    })

    const close = () => {
        setNeedRefresh(false)
    }

    return (
        <AnimatePresence>
            {needRefresh && (
                <motion.div
                    initial={{ opacity: 0, y: 50, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 20, scale: 0.95 }}
                    className="fixed bottom-6 right-6 z-50 max-w-sm w-full md:w-auto"
                >
                    <div className="bg-background/80 backdrop-blur-md border border-primary/20 rounded-xl shadow-2xl p-4 flex items-center gap-4 relative overflow-hidden group">

                        {/* Cosmic ambient glow */}
                        <div className="absolute inset-0 bg-primary/5 blur-xl group-hover:bg-primary/10 transition-colors" />

                        <div className="relative flex items-center gap-4">
                            <div className="h-10 w-10 bg-primary/10 rounded-full flex items-center justify-center border border-primary/20 shrink-0">
                                <Sparkles className="w-5 h-5 text-primary animate-pulse" />
                            </div>

                            <div className="flex-1 space-y-1">
                                <h4 className="text-sm font-bold text-foreground">Evolution Available</h4>
                                <p className="text-xs text-muted-foreground">A new version of the system has been deployed.</p>
                            </div>

                            <button
                                onClick={() => updateServiceWorker(true)}
                                className="ml-2 px-4 py-2 bg-primary text-primary-foreground text-xs font-bold uppercase tracking-wider rounded-lg hover:bg-primary/90 transition-colors shrink-0"
                            >
                                Evolve
                            </button>

                            <button
                                onClick={close}
                                className="absolute -top-2 -right-2 p-1 text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity"
                                aria-label="Close"
                            >
                                ×
                            </button>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    )
}
