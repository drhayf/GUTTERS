import { useRef } from 'react'
import { Terminal, Shield, Cpu, Zap } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { Badge } from '@/components/ui/badge'
import { useGlobalEvents } from '@/contexts/GlobalEventsContext'

export default function SystemActivityWidget() {
    const { isConnected, events } = useGlobalEvents()
    const scrollRef = useRef<HTMLDivElement>(null)

    // Optional: Auto-scroll to top (since we're prepending) or bottom
    // Current UI seems to prepend new events.

    // Helper functions for UI
    const getEventColor = (type: string) => {
        if (type.includes('error')) return 'text-red-400'
        if (type.includes('success') || type.includes('confirmed')) return 'text-emerald-400'
        if (type.includes('hypothesis')) return 'text-purple-400'
        if (type.includes('worker')) return 'text-amber-400'
        if (type.includes('module')) return 'text-blue-400'
        return 'text-primary/70'
    }

    const getEventIcon = (type: string) => {
        if (type.includes('hypothesis')) return <Zap className="w-3 h-3" />
        if (type.includes('worker')) return <Cpu className="w-3 h-3" />
        return <Shield className="w-3 h-3" />
    }

    return (
        <div className="flex flex-col w-full h-[60vh] md:h-[500px] border border-border/60 rounded-2xl bg-black shadow-2xl overflow-hidden group">
            {/* Terminal Header */}
            <div className="flex items-center justify-between px-3 md:px-4 py-3 bg-secondary/20 border-b border-border/20 shrink-0">
                <div className="flex items-center gap-2 md:gap-3 overflow-hidden">
                    <div className="flex gap-1.5 shrink-0">
                        <div className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-red-500/20 border border-red-500/40" />
                        <div className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-amber-500/20 border border-amber-500/40" />
                        <div className="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-emerald-500/20 border border-emerald-500/40" />
                    </div>
                    <div className="h-4 w-[1px] bg-border/40 mx-1 shrink-0" />
                    <div className="flex items-center gap-2 overflow-hidden">
                        <Terminal className="w-3.5 h-3.5 md:w-4 md:h-4 text-emerald-500 shrink-0" />
                        <span className="text-[10px] md:text-[11px] font-bold uppercase tracking-widest text-emerald-500/80 truncate">System.Log</span>
                    </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                    <Badge variant="outline" className={`text-[9px] md:text-[10px] h-5 border-none ${isConnected ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'}`}>
                        {isConnected ? 'LIVE' : 'OFFLINE'}
                    </Badge>
                </div>
            </div>

            {/* Terminal Console */}
            <div className="flex-1 overflow-y-auto px-4 py-4 font-mono text-[11px] md:text-[12px] leading-relaxed scrollbar-thin scrollbar-thumb-white/10" ref={scrollRef}>
                <AnimatePresence initial={false}>
                    {events.map((event, i) => (
                        <motion.div
                            key={`${event.timestamp}-${i}`}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="mb-2 flex flex-col md:flex-row md:items-start gap-1 md:gap-3 group/item hover:bg-white/5 rounded px-2 py-1 -mx-2 transition-colors border-l-2 border-transparent hover:border-white/10"
                        >
                            <span className="text-muted-foreground/40 shrink-0 text-[10px]">
                                {new Date(event.timestamp).toLocaleTimeString([], { hour12: false })}
                            </span>
                            <div className="flex items-center gap-1.5 shrink-0">
                                {getEventIcon(event.event_type)}
                                <span className={`font-bold transition-all ${getEventColor(event.event_type)}`}>
                                    {event.event_type.split('.').pop()?.toUpperCase()}
                                </span>
                            </div>
                            <span className="text-foreground/80 break-all md:break-words whitespace-pre-wrap">
                                {typeof event.payload === 'string'
                                    ? event.payload
                                    : event.payload.message || event.payload.content || JSON.stringify(event.payload)}
                            </span>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {events.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center gap-4 py-8">
                        <div className="relative">
                            <Terminal className={`w-10 h-10 md:w-12 md:h-12 ${isConnected ? 'text-emerald-500/50 animate-pulse' : 'text-red-500/30'}`} />
                            {isConnected && (
                                <motion.div
                                    className="absolute inset-0 bg-emerald-500 blur-2xl opacity-20"
                                    animate={{ scale: [1, 1.2, 1] }}
                                    transition={{ duration: 3, repeat: Infinity }}
                                />
                            )}
                        </div>
                        <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground/50 text-center px-4">
                            {isConnected ? 'System online. Awaiting telemetry...' : 'Connecting to Neural Interface...'}
                        </p>
                    </div>
                )}
            </div>

            {/* Footer Status Bar */}
            <div className="px-3 md:px-4 py-2 bg-emerald-500/5 border-t border-emerald-500/10 flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2 md:gap-4 text-[9px] md:text-[10px] text-emerald-500/50 uppercase font-bold tracking-widest">
                    <span className="truncate max-w-[100px] md:max-w-none">Node: sydney-01</span>
                    <span>Buffer: {events.length}</span>
                </div>
                <div className="flex items-center gap-1.5">
                    <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-ping' : 'bg-red-500'}`} />
                    <span className="text-[9px] md:text-[10px] text-emerald-500/80 font-mono tracking-tighter">
                        {isConnected ? 'LISTENING' : 'RECONNECTING'}
                    </span>
                </div>
            </div>
        </div>
    )
}
