import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { BrainCircuit, ChevronRight, Sparkles, Lightbulb, Target, Eye } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

interface IntelligenceFeedItem {
    id: string
    type: string
    title: string
    description: string
    confidence: number
    timestamp: string
    metadata: any
}

const getTypeConfig = (type: string) => {
    const configs: Record<string, { icon: React.ElementType; color: string; bg: string; label: string }> = {
        'pattern': { icon: Eye, color: 'text-emerald-500', bg: 'bg-emerald-500', label: 'Pattern Detected' },
        'hypothesis': { icon: Lightbulb, color: 'text-amber-500', bg: 'bg-amber-500', label: 'Hypothesis' },
        'insight': { icon: Sparkles, color: 'text-violet-500', bg: 'bg-violet-500', label: 'Insight' },
        'correlation': { icon: Target, color: 'text-cyan-500', bg: 'bg-cyan-500', label: 'Correlation' },
    }
    return configs[type] || configs['pattern']
}

export default function InsightFeed() {
    const { data: feed, isLoading } = useQuery({
        queryKey: ['dashboard-intelligence'],
        queryFn: async () => {
            const res = await api.get<IntelligenceFeedItem[]>('/api/v1/dashboard/intelligence')
            return res.data
        },
        refetchInterval: 60000 // Refresh every minute
    })

    if (isLoading) {
        return (
            <div className="space-y-3 h-full flex flex-col">
                <div className="h-6 w-32 animate-pulse bg-muted/50 rounded" />
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-20 animate-pulse bg-muted/30 rounded-xl" />
                ))}
            </div>
        )
    }

    const items = feed || []

    return (
        <div className="space-y-4 h-full flex flex-col relative z-10">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-emerald-500/10">
                        <BrainCircuit className="w-4 h-4 text-emerald-500" />
                    </div>
                    <h3 className="text-sm font-bold tracking-tight text-foreground">
                        System Intelligence
                    </h3>
                </div>
                {items.length > 0 && (
                    <motion.div 
                        className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-emerald-500/10"
                        animate={{ opacity: [0.5, 1, 0.5] }}
                        transition={{ duration: 2, repeat: Infinity }}
                    >
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        <span className="text-[9px] font-bold uppercase tracking-widest text-emerald-600">
                            {items.length} Active
                        </span>
                    </motion.div>
                )}
            </div>

            <ScrollArea className="flex-1 -mx-2 px-2">
                <div className="space-y-3 pb-4">
                    <AnimatePresence mode="popLayout">
                        {items.length === 0 ? (
                            <motion.div 
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="flex flex-col items-center justify-center py-12 text-center"
                            >
                                <motion.div
                                    className="p-4 rounded-2xl bg-muted/30 mb-4"
                                    animate={{ scale: [1, 1.05, 1] }}
                                    transition={{ duration: 3, repeat: Infinity }}
                                >
                                    <BrainCircuit className="w-8 h-8 text-muted-foreground/40" />
                                </motion.div>
                                <p className="text-sm text-muted-foreground font-medium">
                                    System is observing...
                                </p>
                                <p className="text-xs text-muted-foreground/60 mt-1">
                                    Patterns will appear as data accumulates
                                </p>
                            </motion.div>
                        ) : (
                            items.map((item, index) => {
                                const config = getTypeConfig(item.type)
                                const Icon = config.icon

                                return (
                                    <motion.div
                                        key={item.id}
                                        layout
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        transition={{ delay: index * 0.05 }}
                                        className="group relative overflow-hidden rounded-xl border border-border/30 bg-white/60 p-4 hover:bg-white/80 hover:border-border/50 transition-all cursor-pointer"
                                    >
                                        {/* Subtle animated gradient on hover */}
                                        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <div className={cn(
                                                "absolute -top-10 -left-10 w-20 h-20 rounded-full blur-2xl opacity-20",
                                                config.bg
                                            )} />
                                        </div>

                                        <div className="flex gap-3 relative z-10">
                                            {/* Type Icon */}
                                            <div className={cn(
                                                "p-2 rounded-lg shrink-0",
                                                config.bg + '/10'
                                            )}>
                                                <Icon className={cn("w-4 h-4", config.color)} />
                                            </div>

                                            <div className="flex-1 min-w-0 space-y-1.5">
                                                {/* Header Row */}
                                                <div className="flex items-center justify-between gap-2">
                                                    <span className={cn(
                                                        "text-[10px] font-bold uppercase tracking-widest",
                                                        config.color
                                                    )}>
                                                        {config.label}
                                                    </span>
                                                    
                                                    {/* Confidence Badge */}
                                                    <div className="flex items-center gap-1">
                                                        <div className="w-12 h-1 bg-muted/30 rounded-full overflow-hidden">
                                                            <motion.div 
                                                                className={cn("h-full rounded-full", config.bg)}
                                                                initial={{ width: 0 }}
                                                                animate={{ width: `${item.confidence * 100}%` }}
                                                                transition={{ duration: 0.5, delay: 0.2 }}
                                                            />
                                                        </div>
                                                        <span className="text-[10px] font-mono-data text-muted-foreground">
                                                            {Math.round(item.confidence * 100)}%
                                                        </span>
                                                    </div>
                                                </div>

                                                {/* Title */}
                                                <p className="text-sm font-semibold text-foreground leading-snug">
                                                    {item.title.replace('Pattern: ', '').replace('Theory: ', '')}
                                                </p>

                                                {/* Description */}
                                                <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                                                    {item.description}
                                                </p>
                                            </div>
                                        </div>

                                        {/* Hover Arrow */}
                                        <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <ChevronRight className="w-4 h-4 text-muted-foreground/50" />
                                        </div>
                                    </motion.div>
                                )
                            })
                        )}
                    </AnimatePresence>
                </div>
            </ScrollArea>
        </div>
    )
}
