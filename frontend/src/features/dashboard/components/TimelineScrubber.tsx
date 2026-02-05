import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Calendar, ChevronDown, ChevronUp, Sparkles } from 'lucide-react'
import { useChronosState, getPlanetEmoji, formatCardSymbol } from '@/hooks/useChronosState'

/**
 * TimelineScrubber
 * 
 * A linear progress visualization of the current 52-day planetary period.
 * Shows progress, current day, period card, planet, and guidance text.
 * 
 * Design: Cosmic Brutalist aesthetic - glass panels, zinc borders,
 * animated progress fill with framer-motion.
 */
export default function TimelineScrubber() {
    const { data: chronos, isLoading } = useChronosState()
    const [isExpanded, setIsExpanded] = useState(false)

    if (isLoading) {
        return (
            <div className="relative overflow-hidden rounded-2xl border border-white/20 bg-white/40 backdrop-blur-sm p-4">
                <div className="space-y-3">
                    <div className="h-4 w-32 animate-pulse bg-zinc-200/50 rounded" />
                    <div className="h-2 w-full animate-pulse bg-zinc-200/50 rounded-full" />
                    <div className="h-3 w-48 animate-pulse bg-zinc-200/50 rounded" />
                </div>
            </div>
        )
    }

    if (!chronos?.current_planet) {
        return (
            <div className="relative overflow-hidden rounded-2xl border border-white/20 bg-white/40 backdrop-blur-sm p-4">
                <p className="text-sm text-zinc-400 text-center">
                    Complete onboarding to see your timeline
                </p>
            </div>
        )
    }

    const {
        current_planet,
        current_card,
        days_elapsed,
        days_remaining,
        period_total,
        progress_percent,
        period_start,
        period_end,
        theme,
        guidance,
    } = chronos

    const cardDisplay = current_card?.name || formatCardSymbol({ 
        rank: undefined, 
        suit: current_card?.card?.slice(-1) === 'H' ? 'Hearts' : 
              current_card?.card?.slice(-1) === 'D' ? 'Diamonds' :
              current_card?.card?.slice(-1) === 'C' ? 'Clubs' : 'Spades'
    })

    // Format dates for display
    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return '—'
        try {
            const date = new Date(dateStr)
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        } catch {
            return dateStr
        }
    }

    return (
        <motion.div 
            className="relative overflow-hidden rounded-2xl border border-white/20 bg-gradient-to-br from-white/80 via-white/60 to-white/40 backdrop-blur-xl shadow-lg"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
        >
            {/* Background decoration */}
            <div className="absolute -top-10 -right-10 w-32 h-32 bg-gradient-to-br from-violet-500/5 to-transparent rounded-full blur-2xl" />
            
            <div className="relative p-4 space-y-3">
                {/* Header Row - Planet & Card */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        {/* Planet Badge */}
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900/90 text-white">
                            <span className="text-base">{getPlanetEmoji(current_planet)}</span>
                            <span className="text-sm font-bold uppercase tracking-wide">
                                {current_planet}
                            </span>
                        </div>
                        
                        {/* Period Card */}
                        <div className="flex items-center gap-1.5 text-zinc-600">
                            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                            <span className="text-sm font-semibold">
                                {cardDisplay}
                            </span>
                        </div>
                    </div>

                    {/* Day Counter */}
                    <div className="text-right">
                        <div className="flex items-baseline gap-1">
                            <span className="text-2xl font-mono font-black text-zinc-900">
                                {days_elapsed ?? 0}
                            </span>
                            <span className="text-sm font-medium text-zinc-400">
                                / {period_total}
                            </span>
                        </div>
                        <p className="text-[10px] uppercase tracking-wider text-zinc-400 font-medium">
                            days into period
                        </p>
                    </div>
                </div>

                {/* Progress Bar */}
                <div className="relative">
                    {/* Track */}
                    <div className="h-2.5 bg-zinc-200/70 rounded-full overflow-hidden">
                        {/* Fill */}
                        <motion.div
                            className="h-full bg-gradient-to-r from-violet-500 via-purple-500 to-fuchsia-500 rounded-full relative"
                            initial={{ width: 0 }}
                            animate={{ width: `${progress_percent ?? 0}%` }}
                            transition={{ duration: 1, ease: [0.4, 0, 0.2, 1] }}
                        >
                            {/* Glow effect */}
                            <div className="absolute inset-0 bg-white/30 animate-pulse" />
                        </motion.div>
                    </div>

                    {/* "Now" Indicator */}
                    <motion.div
                        className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2"
                        initial={{ left: 0 }}
                        animate={{ left: `${progress_percent ?? 0}%` }}
                        transition={{ duration: 1, ease: [0.4, 0, 0.2, 1] }}
                    >
                        <div className="relative">
                            {/* Outer glow */}
                            <div className="absolute -inset-2 bg-violet-500/30 rounded-full blur-md animate-pulse" />
                            {/* Inner dot */}
                            <div className="relative w-4 h-4 bg-white rounded-full border-2 border-violet-500 shadow-lg" />
                        </div>
                    </motion.div>
                </div>

                {/* Date Labels */}
                <div className="flex items-center justify-between text-[10px] font-medium text-zinc-400 uppercase tracking-wider">
                    <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        <span>{formatDate(period_start)}</span>
                    </div>
                    <span className="text-zinc-300">|</span>
                    <span>{days_remaining} days remaining</span>
                    <span className="text-zinc-300">|</span>
                    <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        <span>{formatDate(period_end)}</span>
                    </div>
                </div>

                {/* Expand/Collapse Button */}
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="w-full flex items-center justify-center gap-1 pt-1 text-zinc-400 hover:text-zinc-600 transition-colors"
                >
                    <span className="text-[10px] font-medium uppercase tracking-wider">
                        {isExpanded ? 'Hide' : 'Show'} Guidance
                    </span>
                    {isExpanded ? (
                        <ChevronUp className="w-3 h-3" />
                    ) : (
                        <ChevronDown className="w-3 h-3" />
                    )}
                </button>

                {/* Expanded Content - Theme & Guidance */}
                <AnimatePresence>
                    {isExpanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                            className="overflow-hidden"
                        >
                            <div className="pt-3 border-t border-zinc-200/50 space-y-3">
                                {/* Theme */}
                                {theme && (
                                    <div>
                                        <p className="text-[10px] font-bold uppercase tracking-widest text-violet-500 mb-1">
                                            Period Theme
                                        </p>
                                        <p className="text-sm font-semibold text-zinc-700">
                                            {theme}
                                        </p>
                                    </div>
                                )}

                                {/* Guidance */}
                                {guidance && (
                                    <div className="p-3 rounded-xl bg-gradient-to-br from-violet-50 to-purple-50 border border-violet-100">
                                        <p className="text-[10px] font-bold uppercase tracking-widest text-violet-500/70 mb-1">
                                            Guidance
                                        </p>
                                        <p className="text-sm text-zinc-600 leading-relaxed">
                                            {guidance}
                                        </p>
                                    </div>
                                )}

                                {/* No guidance fallback */}
                                {!theme && !guidance && (
                                    <p className="text-sm text-zinc-400 italic text-center py-2">
                                        Detailed guidance will appear here
                                    </p>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    )
}
