import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Trophy, Activity, Flame, Target, Sparkles } from 'lucide-react'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

interface ProgressionStats {
    level: number
    rank: string
    experience_points: number
    xp_to_next_level: number
    xp_current_level?: number
    xp_required_level?: number
    level_progress_percent?: number
    sync_rate: number
    sync_rate_momentum: number
    streak_count: number
}

export default function PlayerStatus() {
    const { data: stats, isLoading } = useQuery({
        queryKey: ['progression-stats'],
        queryFn: async () => {
            const res = await api.get<ProgressionStats>('/api/v1/progression/stats')
            return res.data
        },
        refetchInterval: 30000 // Refresh every 30s for live feel
    })

    if (isLoading) {
        return (
            <div className="space-y-4">
                <div className="h-44 animate-pulse bg-white/40 rounded-2xl" />
            </div>
        )
    }

    if (!stats) return null

    const xpPercentage = stats.level_progress_percent ?? Math.min((stats.experience_points / stats.xp_to_next_level) * 100, 100)
    const fmt = (n: number) => new Intl.NumberFormat('en-US').format(n)

    // Sync color based on rate
    const getSyncConfig = (rate: number) => {
        if (rate >= 0.8) return { color: 'text-emerald-500', bg: 'bg-emerald-500', label: 'OPTIMAL', glow: 'shadow-emerald-500/50' }
        if (rate >= 0.5) return { color: 'text-amber-500', bg: 'bg-amber-500', label: 'MODERATE', glow: 'shadow-amber-500/50' }
        return { color: 'text-red-500', bg: 'bg-red-500', label: 'LOW', glow: 'shadow-red-500/50' }
    }
    const syncConfig = getSyncConfig(stats.sync_rate)

    return (
        <div className="space-y-4">
            {/* MAIN HUD CARD */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative overflow-hidden rounded-2xl border border-white/20 bg-gradient-to-br from-white/80 via-white/60 to-white/40 backdrop-blur-xl shadow-xl"
            >
                {/* Animated Background Gradient */}
                <div className="absolute inset-0 opacity-30">
                    <motion.div
                        className="absolute -top-20 -right-20 w-64 h-64 rounded-full bg-gradient-to-br from-primary/30 to-violet-500/20 blur-3xl"
                        animate={{ 
                            scale: [1, 1.2, 1],
                            rotate: [0, 90, 0],
                        }}
                        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                    />
                </div>

                {/* Background Decoration */}
                <div className="absolute top-0 right-0 p-6 opacity-5">
                    <Trophy className="w-40 h-40" />
                </div>

                <div className="p-6 relative z-10">
                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            {/* Rank Label */}
                            <div className="flex items-center gap-2 mb-2">
                                <Sparkles className="w-4 h-4 text-primary animate-pulse" />
                                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">
                                    Current Rank
                                </span>
                            </div>
                            
                            {/* RANK DISPLAY */}
                            <div className="flex items-baseline gap-3 mb-1">
                                <motion.h2 
                                    className="text-4xl font-black tracking-tight text-foreground"
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.1 }}
                                >
                                    {stats.rank}
                                </motion.h2>
                                <motion.span 
                                    className="text-lg font-medium text-muted-foreground"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ delay: 0.2 }}
                                >
                                    Lvl. {stats.level}
                                </motion.span>
                            </div>

                            {/* Streak Badge */}
                            {stats.streak_count > 0 && (
                                <motion.div 
                                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-orange-500/10 border border-orange-500/20 mt-2"
                                    initial={{ opacity: 0, scale: 0.8 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: 0.3 }}
                                >
                                    <Flame className="w-3.5 h-3.5 text-orange-500" />
                                    <span className="text-xs font-bold text-orange-600">
                                        {stats.streak_count} Day Streak
                                    </span>
                                </motion.div>
                            )}
                        </div>

                        {/* SYNC RATE WIDGET */}
                        <motion.div 
                            className="flex flex-col items-end"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.2 }}
                        >
                            <div className="flex items-center gap-2 mb-2">
                                <Activity className={cn("w-4 h-4", syncConfig.color)} />
                                <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                                    Sync Rate
                                </span>
                            </div>
                            
                            {/* Sync Percentage with Animated Glow */}
                            <div className="relative">
                                <motion.div
                                    className={cn(
                                        "text-3xl font-mono-data font-black",
                                        syncConfig.color
                                    )}
                                    animate={{ opacity: [0.8, 1, 0.8] }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                >
                                    {Math.round(stats.sync_rate * 100)}%
                                </motion.div>
                                
                                {/* Pulse ring behind percentage */}
                                <motion.div
                                    className={cn(
                                        "absolute -inset-2 rounded-lg opacity-20",
                                        syncConfig.bg
                                    )}
                                    animate={{ scale: [1, 1.1, 1], opacity: [0.1, 0.2, 0.1] }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                />
                            </div>

                            {/* Momentum Indicator */}
                            {stats.sync_rate_momentum !== 0 && (
                                <motion.div 
                                    className={cn(
                                        "flex items-center gap-1 text-[11px] font-bold mt-1",
                                        stats.sync_rate_momentum > 0 ? "text-emerald-500" : "text-amber-500"
                                    )}
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ delay: 0.4 }}
                                >
                                    <Target className="w-3 h-3" />
                                    {stats.sync_rate_momentum > 0 ? "+" : ""}{Math.round(stats.sync_rate_momentum * 100)}%
                                </motion.div>
                            )}

                            {/* Status Label */}
                            <span className={cn(
                                "text-[9px] font-bold uppercase tracking-widest mt-1 px-2 py-0.5 rounded",
                                syncConfig.bg + '/10',
                                syncConfig.color.replace('text-', 'text-')
                            )}>
                                {syncConfig.label}
                            </span>
                        </motion.div>
                    </div>

                    {/* XP BAR */}
                    <motion.div 
                        className="mt-6 pt-4 border-t border-border/20"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                    >
                        <div className="flex justify-between text-[10px] font-medium text-muted-foreground mb-2">
                            <div className="flex items-center gap-2">
                                <span className="uppercase tracking-wider">Experience</span>
                                {stats.xp_current_level !== undefined && (
                                    <span className="font-mono-data text-foreground">
                                        {fmt(stats.xp_current_level)}
                                    </span>
                                )}
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="font-mono-data text-primary font-bold">
                                    {Math.round(xpPercentage)}%
                                </span>
                                {stats.xp_required_level !== undefined && (
                                    <span className="text-muted-foreground/60">
                                        / {fmt(stats.xp_required_level)} XP
                                    </span>
                                )}
                            </div>
                        </div>
                        
                        {/* Enhanced Progress Bar */}
                        <div className="relative h-2.5 bg-muted/30 rounded-full overflow-hidden">
                            <motion.div 
                                className="absolute inset-y-0 left-0 bg-gradient-to-r from-primary via-violet-500 to-primary rounded-full"
                                initial={{ width: 0 }}
                                animate={{ width: `${xpPercentage}%` }}
                                transition={{ duration: 1, delay: 0.5, ease: "easeOut" }}
                            />
                            {/* Shimmer effect */}
                            <motion.div
                                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                                animate={{ x: ['-100%', '200%'] }}
                                transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
                            />
                        </div>
                    </motion.div>
                </div>
            </motion.div>
        </div>
    )
}
