
import { useState, useEffect } from 'react'
import { WifiOff } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export function useNetworkStatus() {
    const [isOnline, setIsOnline] = useState(navigator.onLine)

    useEffect(() => {
        const handleOnline = () => setIsOnline(true)
        const handleOffline = () => setIsOnline(false)

        window.addEventListener('online', handleOnline)
        window.addEventListener('offline', handleOffline)

        return () => {
            window.removeEventListener('online', handleOnline)
            window.removeEventListener('offline', handleOffline)
        }
    }, [])

    return isOnline
}

export function OfflineIndicator() {
    const isOnline = useNetworkStatus()

    return (
        <AnimatePresence>
            {!isOnline && (
                <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="w-full bg-destructive/10 border-b border-destructive/20 overflow-hidden"
                >
                    <div className="container max-w-7xl mx-auto px-4 py-1.5 flex items-center justify-center gap-2 text-[11px] font-bold uppercase tracking-widest text-destructive">
                        <WifiOff className="w-3 h-3" />
                        <span>Offline Mode • Intelligence Disconnected</span>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    )
}
