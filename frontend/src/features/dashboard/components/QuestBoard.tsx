import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Circle, Sparkles, User, Repeat, Zap, CheckCircle2, Target, Scroll } from 'lucide-react'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

interface Quest {
    id: number
    title: string
    description?: string
    recurrence: string
    difficulty: number
    is_active: boolean
    source: 'USER' | 'SYSTEM' | 'AGENT'
    status?: string
}

// Difficulty config for visual hierarchy
const difficultyConfig: Record<number, { label: string; color: string; glow: string }> = {
    1: { label: 'TRIVIAL', color: 'text-zinc-400', glow: '' },
    2: { label: 'EASY', color: 'text-emerald-500', glow: '' },
    3: { label: 'MODERATE', color: 'text-blue-500', glow: '' },
    4: { label: 'HARD', color: 'text-amber-500', glow: 'shadow-amber-500/20' },
    5: { label: 'EPIC', color: 'text-violet-500', glow: 'shadow-violet-500/30' },
}

// Source config for premium styling
const sourceConfig: Record<string, { icon: typeof User; color: string; bg: string; border: string }> = {
    USER: { 
        icon: User, 
        color: 'text-zinc-500', 
        bg: 'bg-white/50',
        border: 'border-zinc-200/60'
    },
    AGENT: { 
        icon: Sparkles, 
        color: 'text-violet-500', 
        bg: 'bg-gradient-to-br from-violet-50/60 to-fuchsia-50/40',
        border: 'border-violet-200/60'
    },
    SYSTEM: { 
        icon: Zap, 
        color: 'text-amber-500', 
        bg: 'bg-gradient-to-br from-amber-50/60 to-orange-50/40',
        border: 'border-amber-200/60'
    },
}

const containerVariants = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: { staggerChildren: 0.08 }
    }
}

const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    show: { opacity: 1, x: 0 }
}

export default function QuestBoard() {
    const { data: quests, isLoading } = useQuery({
        queryKey: ['quests'],
        queryFn: async () => {
            const res = await api.get<Quest[]>('/api/v1/quests?view=tasks')
            return res.data
        }
    })

    if (isLoading) {
        return (
            <div className="space-y-3">
                <div className="h-5 w-32 bg-zinc-200/50 rounded animate-pulse" />
                <div className="space-y-2">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-20 bg-white/40 rounded-xl animate-pulse" />
                    ))}
                </div>
            </div>
        )
    }

    // High fidelity: Filter by status to ensure we only show Pending tasks
    const activeQuests = quests?.filter(q => q.status === 'pending') || []

    return (
        <div className="space-y-4">
            {/* Header with status indicator */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="relative">
                        <Target className="w-4 h-4 text-primary" />
                        {activeQuests.length > 0 && (
                            <motion.div
                                className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-emerald-500 rounded-full"
                                animate={{ scale: [1, 1.2, 1] }}
                                transition={{ duration: 2, repeat: Infinity }}
                            />
                        )}
                    </div>
                    <h3 className="text-sm font-bold tracking-tight text-foreground/90">
                        Quest Log
                    </h3>
                </div>
                <motion.div 
                    className="flex items-center gap-1.5 text-[10px] bg-zinc-900/5 px-2 py-1 rounded-full font-mono-data"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                >
                    <Scroll className="w-3 h-3 text-zinc-400" />
                    <span className="text-zinc-600">{activeQuests.length}</span>
                    <span className="text-zinc-400">ACTIVE</span>
                </motion.div>
            </div>

            {/* Quest list */}
            <motion.div 
                className="space-y-2"
                variants={containerVariants}
                initial="hidden"
                animate="show"
            >
                <AnimatePresence mode="popLayout">
                    {activeQuests.length === 0 ? (
                        <motion.div 
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="text-center py-10 rounded-xl bg-gradient-to-b from-zinc-50/50 to-white/30 border border-dashed border-zinc-200/50"
                        >
                            <motion.div
                                animate={{ y: [0, -3, 0] }}
                                transition={{ duration: 3, repeat: Infinity }}
                            >
                                <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-400/60 mb-3" />
                            </motion.div>
                            <p className="text-sm text-muted-foreground font-medium">All quests complete</p>
                            <p className="text-xs text-zinc-400 mt-1">The log is clear. Rest well, traveler.</p>
                        </motion.div>
                    ) : (
                        activeQuests.map((quest) => {
                            const source = sourceConfig[quest.source] || sourceConfig.USER
                            const difficulty = difficultyConfig[quest.difficulty] || difficultyConfig[3]
                            const SourceIcon = source.icon

                            return (
                                <motion.div
                                    key={quest.id}
                                    variants={itemVariants}
                                    layout
                                    exit={{ opacity: 0, x: -20, height: 0 }}
                                    className={cn(
                                        "group relative overflow-hidden rounded-xl border p-3 transition-all duration-300",
                                        "hover:shadow-lg hover:-translate-y-0.5",
                                        source.bg,
                                        source.border,
                                        difficulty.glow && `hover:shadow-lg ${difficulty.glow}`
                                    )}
                                >
                                    {/* Subtle gradient overlay on hover */}
                                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/0 to-white/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

                                    <div className="relative flex items-start gap-3">
                                        {/* Interactive checkbox */}
                                        <motion.button 
                                            className="mt-0.5 text-zinc-300 hover:text-emerald-500 transition-colors"
                                            whileHover={{ scale: 1.1 }}
                                            whileTap={{ scale: 0.9 }}
                                        >
                                            <Circle className="w-5 h-5 stroke-[1.5]" />
                                        </motion.button>

                                        <div className="flex-1 min-w-0">
                                            {/* Title row with source indicator */}
                                            <div className="flex items-center gap-2 mb-1">
                                                <motion.div
                                                    animate={quest.source === 'AGENT' ? { 
                                                        rotate: [0, 5, -5, 0],
                                                        scale: [1, 1.1, 1]
                                                    } : {}}
                                                    transition={{ duration: 3, repeat: Infinity }}
                                                >
                                                    <SourceIcon className={cn("w-3.5 h-3.5", source.color)} />
                                                </motion.div>

                                                <h4 className={cn(
                                                    "text-sm font-semibold truncate leading-tight",
                                                    quest.source === 'AGENT' && "text-violet-900",
                                                    quest.source === 'SYSTEM' && "text-amber-900"
                                                )}>
                                                    {quest.title}
                                                </h4>
                                            </div>

                                            {/* Description */}
                                            {quest.description && (
                                                <p className="text-xs text-muted-foreground/80 line-clamp-2 leading-relaxed mb-2">
                                                    {quest.description}
                                                </p>
                                            )}

                                            {/* Meta tags row */}
                                            <div className="flex items-center gap-2 flex-wrap">
                                                {/* Recurrence badge */}
                                                {quest.recurrence !== 'ONCE' && (
                                                    <div className="flex items-center gap-1 text-[10px] text-zinc-600 bg-white/60 px-2 py-0.5 rounded-full border border-zinc-100">
                                                        <Repeat className="w-2.5 h-2.5" />
                                                        <span className="font-medium">{quest.recurrence}</span>
                                                    </div>
                                                )}

                                                {/* Difficulty badge */}
                                                <div className={cn(
                                                    "text-[10px] font-mono-data px-2 py-0.5 rounded-full bg-white/60 border border-zinc-100",
                                                    difficulty.color
                                                )}>
                                                    {difficulty.label}
                                                </div>

                                                {/* Priority indicator for high difficulty */}
                                                {quest.difficulty >= 4 && (
                                                    <motion.div
                                                        animate={{ opacity: [0.5, 1, 0.5] }}
                                                        transition={{ duration: 2, repeat: Infinity }}
                                                        className="ml-auto"
                                                    >
                                                        <Zap className={cn("w-3.5 h-3.5", difficulty.color)} />
                                                    </motion.div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            )
                        })
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    )
}
