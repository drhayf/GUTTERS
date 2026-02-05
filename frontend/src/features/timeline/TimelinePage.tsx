import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Calendar, Book, Sparkles, ChevronLeft, ChevronRight, Filter, Activity, Clock } from 'lucide-react'
import { useChronosState, formatCardSymbol, getPlanetEmoji } from '@/hooks/useChronosState'
import { motion, AnimatePresence } from 'framer-motion'
import api from '@/lib/api'
import { useQuery } from '@tanstack/react-query'
import CyclicalPatternsPanel from './CyclicalPatternsPanel'

type ViewMode = 'periods' | 'patterns'

interface JournalEntry {
    id: number
    content: string
    mood_score?: number
    tags?: string[]
    context_snapshot?: {
        magi?: {
            period_card?: string
            period_day?: number
            planetary_ruler?: string
            theme?: string
            guidance?: string
            period_start?: string
            period_end?: string
        }
        solar?: any
        lunar?: any
        transits?: any
    }
    created_at: string
}

interface PeriodGroup {
    periodCard: { rank?: number; rank_name?: string; suit?: string } | null
    planet: string
    startDate: string
    endDate: string
    dayStart: number
    dayEnd: number
    entries: JournalEntry[]
    theme?: string
    guidance?: string
}

/**
 * TimelinePage
 * 
 * Dedicated page for visualizing the user's chronos history.
 * Groups journal entries by 52-day magi periods.
 * 
 * Features:
 * - Full timeline of all magi periods
 * - Journal entries grouped by period
 * - Period navigation (previous/next)
 * - Period card visualization
 * - Cosmic Brutalist design with glass morphism
 * - Responsive layout with animations
 */
export default function TimelinePage() {
    const { data: chronos, isLoading: chronosLoading } = useChronosState()
    const [selectedPeriodIndex, setSelectedPeriodIndex] = useState<number | null>(null)
    const [filterMode, setFilterMode] = useState<'all' | 'with-entries'>('all')
    const [viewMode, setViewMode] = useState<ViewMode>('periods')

    // Fetch journal entries
    const { data: journalEntries, isLoading: journalLoading } = useQuery<JournalEntry[]>({
        queryKey: ['journal-entries'],
        queryFn: async () => {
            const res = await api.get('/api/v1/insights/journal')
            return res.data
        },
        staleTime: 1000 * 60 * 2 // 2 minutes
    })

    // Group entries by period
    const periodGroups = groupEntriesByPeriod(journalEntries || [], chronos)

    // Filter periods
    const filteredGroups = filterMode === 'with-entries' 
        ? periodGroups.filter(g => g.entries.length > 0)
        : periodGroups

    // Auto-select current period on load
    useEffect(() => {
        if (filteredGroups.length > 0 && selectedPeriodIndex === null) {
            setSelectedPeriodIndex(0) // Current period is first
        }
    }, [filteredGroups, selectedPeriodIndex])

    if (chronosLoading || journalLoading) {
        return (
            <div className="container max-w-7xl mx-auto p-6 space-y-6">
                <div className="h-12 bg-zinc-900/50 rounded-lg animate-pulse" />
                <div className="grid gap-6 lg:grid-cols-3">
                    <div className="lg:col-span-1 h-[600px] bg-zinc-900/50 rounded-lg animate-pulse" />
                    <div className="lg:col-span-2 h-[600px] bg-zinc-900/50 rounded-lg animate-pulse" />
                </div>
            </div>
        )
    }

    const selectedGroup = selectedPeriodIndex !== null ? filteredGroups[selectedPeriodIndex] : null

    return (
        <div className="container max-w-7xl mx-auto p-6 space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                    <Calendar className="h-8 w-8 text-purple-400" />
                    <div>
                        <h1 className="text-3xl font-bold text-zinc-100">Chronos Timeline</h1>
                        <p className="text-sm text-zinc-500">
                            52-day periods, journal history, and pattern discovery
                        </p>
                    </div>
                </div>

                {/* View Mode Toggle */}
                <div className="flex items-center gap-3">
                    <div className="flex items-center p-1 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
                        <button
                            onClick={() => setViewMode('periods')}
                            className={`
                                flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                                ${viewMode === 'periods' 
                                    ? 'bg-purple-950/50 text-purple-300 border border-purple-500/30' 
                                    : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
                                }
                            `}
                        >
                            <Clock className="h-4 w-4" />
                            Periods
                        </button>
                        <button
                            onClick={() => setViewMode('patterns')}
                            className={`
                                flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                                ${viewMode === 'patterns' 
                                    ? 'bg-purple-950/50 text-purple-300 border border-purple-500/30' 
                                    : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
                                }
                            `}
                        >
                            <Activity className="h-4 w-4" />
                            Patterns
                        </button>
                    </div>

                    {/* Period Filter (only visible in periods view) */}
                    {viewMode === 'periods' && (
                        <button
                            onClick={() => setFilterMode(mode => mode === 'all' ? 'with-entries' : 'all')}
                            className={`
                                flex items-center gap-2 px-4 py-2 rounded-lg border transition-all
                                ${filterMode === 'with-entries' 
                                    ? 'border-purple-500/50 bg-purple-950/30 text-purple-300' 
                                    : 'border-zinc-800/50 bg-zinc-900/50 text-zinc-400 hover:bg-zinc-800/50'
                                }
                            `}
                        >
                            <Filter className="h-4 w-4" />
                            <span className="text-sm font-medium hidden md:inline">
                                {filterMode === 'with-entries' ? 'With Entries' : 'All Periods'}
                            </span>
                        </button>
                    )}
                </div>
            </div>

            {/* Main Content - Conditional based on view mode */}
            <AnimatePresence mode="wait">
                {viewMode === 'patterns' ? (
                    <motion.div
                        key="patterns"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.2 }}
                    >
                        <CyclicalPatternsPanel />
                    </motion.div>
                ) : (
                    <motion.div
                        key="periods"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        transition={{ duration: 0.2 }}
                    >
                        {/* Main Period Layout */}
                        <div className="grid gap-6 lg:grid-cols-3">
                {/* Period List (Left Sidebar) */}
                <Card className="lg:col-span-1 border-zinc-800/50 bg-zinc-950/80 backdrop-blur-sm">
                    <CardHeader>
                        <CardTitle className="text-lg text-zinc-100">Period History</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 max-h-[600px] overflow-y-auto">
                        {filteredGroups.map((group, index) => (
                            <button
                                key={index}
                                onClick={() => setSelectedPeriodIndex(index)}
                                className={`
                                    w-full p-3 rounded-lg border text-left transition-all
                                    ${selectedPeriodIndex === index
                                        ? 'border-purple-500/50 bg-purple-950/30 shadow-lg shadow-purple-500/20'
                                        : 'border-zinc-800/50 bg-zinc-900/50 hover:bg-zinc-800/50'
                                    }
                                `}
                            >
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-lg">{getPlanetEmoji(group.planet)}</span>
                                    <span className="font-medium text-sm text-zinc-200">
                                        {formatCardSymbol(group.periodCard)}
                                    </span>
                                </div>
                                <p className="text-xs text-zinc-500">
                                    {formatDateRange(group.startDate, group.endDate)}
                                </p>
                                {group.entries.length > 0 && (
                                    <div className="flex items-center gap-1 mt-2 text-purple-400">
                                        <Book className="h-3 w-3" />
                                        <span className="text-xs font-medium">
                                            {group.entries.length} entr{group.entries.length === 1 ? 'y' : 'ies'}
                                        </span>
                                    </div>
                                )}
                                {index === 0 && (
                                    <div className="flex items-center gap-1 mt-2 text-green-400">
                                        <Sparkles className="h-3 w-3" />
                                        <span className="text-xs font-medium">Current</span>
                                    </div>
                                )}
                            </button>
                        ))}
                    </CardContent>
                </Card>

                {/* Period Detail (Main Content) */}
                <div className="lg:col-span-2 space-y-4">
                    {selectedGroup ? (
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={selectedPeriodIndex}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="space-y-4"
                            >
                                {/* Period Card */}
                                <Card className="border-zinc-800/50 bg-zinc-950/80 backdrop-blur-sm">
                                    <CardContent className="p-6">
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-center gap-4">
                                                <div className="text-4xl">
                                                    {getPlanetEmoji(selectedGroup.planet)}
                                                </div>
                                                <div>
                                                    <h2 className="text-2xl font-bold text-zinc-100">
                                                        {formatCardSymbol(selectedGroup.periodCard)}
                                                    </h2>
                                                    <p className="text-sm text-zinc-500">
                                                        {selectedGroup.planet} Period
                                                    </p>
                                                    <p className="text-xs text-zinc-600 mt-1">
                                                        {formatDateRange(selectedGroup.startDate, selectedGroup.endDate)}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Navigation */}
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={() => setSelectedPeriodIndex(Math.max(0, selectedPeriodIndex! - 1))}
                                                    disabled={selectedPeriodIndex === 0}
                                                    className="p-2 rounded-lg border border-zinc-800/50 bg-zinc-900/50 hover:bg-zinc-800/50 disabled:opacity-30 disabled:cursor-not-allowed"
                                                >
                                                    <ChevronLeft className="h-4 w-4 text-zinc-400" />
                                                </button>
                                                <button
                                                    onClick={() => setSelectedPeriodIndex(Math.min(filteredGroups.length - 1, selectedPeriodIndex! + 1))}
                                                    disabled={selectedPeriodIndex === filteredGroups.length - 1}
                                                    className="p-2 rounded-lg border border-zinc-800/50 bg-zinc-900/50 hover:bg-zinc-800/50 disabled:opacity-30 disabled:cursor-not-allowed"
                                                >
                                                    <ChevronRight className="h-4 w-4 text-zinc-400" />
                                                </button>
                                            </div>
                                        </div>

                                        {/* Theme & Guidance */}
                                        {(selectedGroup.theme || selectedGroup.guidance) && (
                                            <div className="mt-4 space-y-2">
                                                {selectedGroup.theme && (
                                                    <div className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800/50">
                                                        <p className="text-xs font-medium text-zinc-400 mb-1">THEME</p>
                                                        <p className="text-sm text-zinc-300">{selectedGroup.theme}</p>
                                                    </div>
                                                )}
                                                {selectedGroup.guidance && (
                                                    <div className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800/50">
                                                        <p className="text-xs font-medium text-zinc-400 mb-1">GUIDANCE</p>
                                                        <p className="text-sm text-zinc-300">{selectedGroup.guidance}</p>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </CardContent>
                                </Card>

                                {/* Journal Entries */}
                                <Card className="border-zinc-800/50 bg-zinc-950/80 backdrop-blur-sm">
                                    <CardHeader>
                                        <CardTitle className="flex items-center gap-2 text-lg text-zinc-100">
                                            <Book className="h-5 w-5 text-purple-400" />
                                            Journal Entries ({selectedGroup.entries.length})
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4 max-h-[400px] overflow-y-auto">
                                        {selectedGroup.entries.length === 0 ? (
                                            <p className="text-center text-sm text-zinc-500 py-8">
                                                No journal entries for this period
                                            </p>
                                        ) : (
                                            selectedGroup.entries.map((entry) => (
                                                <motion.div
                                                    key={entry.id}
                                                    initial={{ opacity: 0, scale: 0.95 }}
                                                    animate={{ opacity: 1, scale: 1 }}
                                                    className="p-4 rounded-lg border border-zinc-800/50 bg-zinc-900/50 hover:bg-zinc-800/50 transition-all"
                                                >
                                                    <div className="flex items-start justify-between mb-2">
                                                        <p className="text-xs text-zinc-500">
                                                            {formatEntryDate(entry.created_at)}
                                                        </p>
                                                        {entry.mood_score && (
                                                            <span className="text-xs px-2 py-1 rounded bg-purple-950/30 text-purple-300">
                                                                Mood: {entry.mood_score}/10
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-zinc-300 leading-relaxed">
                                                        {entry.content}
                                                    </p>
                                                    {entry.tags && entry.tags.length > 0 && (
                                                        <div className="flex flex-wrap gap-2 mt-3">
                                                            {entry.tags.map((tag, i) => (
                                                                <span
                                                                    key={i}
                                                                    className="text-xs px-2 py-1 rounded-full bg-zinc-800/50 text-zinc-400"
                                                                >
                                                                    {tag}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    )}
                                                </motion.div>
                                            ))
                                        )}
                                    </CardContent>
                                </Card>
                            </motion.div>
                        </AnimatePresence>
                    ) : (
                        <Card className="border-zinc-800/50 bg-zinc-950/80 backdrop-blur-sm">
                            <CardContent className="p-12 text-center">
                                <Calendar className="h-16 w-16 text-zinc-700 mx-auto mb-4" />
                                <p className="text-zinc-500">Select a period to view details</p>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}

/**
 * Group journal entries by magi period
 */
function groupEntriesByPeriod(entries: JournalEntry[], chronos: any): PeriodGroup[] {
    if (!chronos) return []

    const groups: PeriodGroup[] = []
    const birthCards = chronos.birth_cards || []
    
    // Current period (index 0)
    const currentGroup: PeriodGroup = {
        periodCard: chronos.current_card || null,
        planet: chronos.current_planet || 'Unknown',
        startDate: chronos.period_start || new Date().toISOString(),
        endDate: chronos.period_end || new Date().toISOString(),
        dayStart: 1,
        dayEnd: 52,
        entries: [],
        theme: chronos.theme,
        guidance: chronos.guidance
    }
    
    // Filter entries for current period
    currentGroup.entries = entries.filter(entry => {
        const entryDate = new Date(entry.created_at)
        const periodStart = new Date(chronos.period_start)
        const periodEnd = new Date(chronos.period_end)
        return entryDate >= periodStart && entryDate <= periodEnd
    })
    
    groups.push(currentGroup)

    // Generate past periods (up to 7 previous periods = 1 year)
    for (let i = 1; i <= 7; i++) {
        const periodStartDate = new Date(chronos.period_start)
        periodStartDate.setDate(periodStartDate.getDate() - (i * 52))
        
        const periodEndDate = new Date(periodStartDate)
        periodEndDate.setDate(periodEndDate.getDate() + 51)

        // Get card for this past period (rotate backwards)
        const currentCardIndex = birthCards.findIndex((card: any) => card.name === chronos.current_card?.name)
        const pastCardIndex = (currentCardIndex - i + birthCards.length) % birthCards.length
        const pastCard = birthCards[pastCardIndex] || { name: 'Unknown', ruling_planet: 'Unknown' }

        const pastGroup: PeriodGroup = {
            periodCard: pastCard,
            planet: pastCard.ruling_planet || 'Unknown',
            startDate: periodStartDate.toISOString(),
            endDate: periodEndDate.toISOString(),
            dayStart: 1,
            dayEnd: 52,
            entries: []
        }

        // Filter entries for this past period
        pastGroup.entries = entries.filter(entry => {
            const entryDate = new Date(entry.created_at)
            return entryDate >= periodStartDate && entryDate <= periodEndDate
        })

        groups.push(pastGroup)
    }

    return groups
}

/**
 * Format date range (MM/DD - MM/DD)
 */
function formatDateRange(start: string, end: string): string {
    const startDate = new Date(start)
    const endDate = new Date(end)
    
    const startStr = `${startDate.getMonth() + 1}/${startDate.getDate()}`
    const endStr = `${endDate.getMonth() + 1}/${endDate.getDate()}`
    
    return `${startStr} - ${endStr}`
}

/**
 * Format entry timestamp
 */
function formatEntryDate(timestamp: string): string {
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit'
    })
}
