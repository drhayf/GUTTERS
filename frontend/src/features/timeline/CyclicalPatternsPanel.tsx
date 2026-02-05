/**
 * CyclicalPatternsPanel Component
 * 
 * High-fidelity visualization of detected cyclical patterns from the Observer module.
 * Displays recurring experiences, period variances, theme alignments, and evolution insights.
 * 
 * Design: Cosmic Brutalist with glass morphism
 * Features:
 * - Pattern cards with confidence indicators
 * - Filtering by pattern type and period
 * - Visual confidence rings
 * - Expandable pattern details
 * - Pattern analysis trigger
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
    Sparkles, 
    TrendingUp, 
    TrendingDown, 
    Minus, 
    Activity,
    RefreshCw,
    ChevronDown,
    ChevronUp,
    Zap,
    Eye,
    BarChart3,
} from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
    useCyclicalPatterns,
    useCyclicalPatternSummary,
    useTriggerPatternAnalysis,
    type CyclicalPattern,
    getConfidenceColor,
    getConfidenceBgColor,
    getPatternTypeIcon,
    getPatternTypeLabel,
    formatConfidence,
} from '@/hooks/useCyclicalPatterns'
import { getPlanetEmoji } from '@/hooks/useChronosState'

// =============================================================================
// TYPES
// =============================================================================

interface CyclicalPatternsPanelProps {
    className?: string
    compact?: boolean
}

type FilterType = 'all' | 'period_symptom' | 'variance' | 'theme_alignment' | 'evolution'

// =============================================================================
// COMPONENTS
// =============================================================================

/**
 * Confidence Ring - Visual confidence indicator
 */
function ConfidenceRing({ confidence, size = 48 }: { confidence: number; size?: number }) {
    const circumference = 2 * Math.PI * (size / 2 - 4)
    const strokeDashoffset = circumference * (1 - confidence)
    
    const color = confidence >= 0.85 
        ? '#10b981' 
        : confidence >= 0.7 
            ? '#f59e0b' 
            : confidence >= 0.5 
                ? '#f97316' 
                : '#71717a'
    
    return (
        <div className="relative" style={{ width: size, height: size }}>
            {/* Background ring */}
            <svg className="absolute inset-0 -rotate-90" viewBox={`0 0 ${size} ${size}`}>
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={size / 2 - 4}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3"
                    className="text-zinc-800"
                />
                <motion.circle
                    cx={size / 2}
                    cy={size / 2}
                    r={size / 2 - 4}
                    fill="none"
                    stroke={color}
                    strokeWidth="3"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    initial={{ strokeDashoffset: circumference }}
                    animate={{ strokeDashoffset }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                />
            </svg>
            {/* Center text */}
            <div className="absolute inset-0 flex items-center justify-center">
                <span className={`text-xs font-bold ${getConfidenceColor(confidence)}`}>
                    {Math.round(confidence * 100)}
                </span>
            </div>
        </div>
    )
}

/**
 * Pattern Card - Individual pattern display
 */
function PatternCard({ pattern, expanded, onToggle }: { 
    pattern: CyclicalPattern
    expanded: boolean
    onToggle: () => void 
}) {
    const TrajectoryIcon = pattern.evolution?.mood_trajectory === 'improving' 
        ? TrendingUp 
        : pattern.evolution?.mood_trajectory === 'declining'
            ? TrendingDown
            : Minus

    return (
        <motion.div
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`
                rounded-xl border transition-all duration-300
                ${getConfidenceBgColor(pattern.confidence)}
                hover:scale-[1.01] cursor-pointer
            `}
            onClick={onToggle}
        >
            <div className="p-4">
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                        <ConfidenceRing confidence={pattern.confidence} size={44} />
                        
                        <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2 mb-1">
                                <span className="text-lg">{getPatternTypeIcon(pattern.pattern_type)}</span>
                                <span className="text-sm font-semibold text-zinc-200 truncate">
                                    {getPatternTypeLabel(pattern.pattern_type)}
                                </span>
                            </div>
                            <div className="flex items-center gap-2 text-xs text-zinc-400">
                                <span>{getPlanetEmoji(pattern.planetary_ruler)}</span>
                                <span className="font-medium">{pattern.period_card}</span>
                                <span className="text-zinc-600">•</span>
                                <span>{pattern.observation_count} observations</span>
                            </div>
                        </div>
                    </div>
                    
                    <button className="p-1 rounded-lg hover:bg-white/10 transition-colors shrink-0">
                        {expanded ? (
                            <ChevronUp className="h-4 w-4 text-zinc-400" />
                        ) : (
                            <ChevronDown className="h-4 w-4 text-zinc-400" />
                        )}
                    </button>
                </div>
                
                {/* Description */}
                <p className="mt-3 text-sm text-zinc-300 leading-relaxed line-clamp-2">
                    {pattern.description}
                </p>
                
                {/* Symptoms (if present) */}
                {pattern.symptoms && pattern.symptoms.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3">
                        {pattern.symptoms.slice(0, 3).map((symptom, i) => (
                            <Badge 
                                key={i} 
                                variant="outline" 
                                className="text-[10px] border-zinc-700 text-zinc-400"
                            >
                                {symptom}
                            </Badge>
                        ))}
                        {pattern.symptoms.length > 3 && (
                            <Badge 
                                variant="outline" 
                                className="text-[10px] border-zinc-700 text-zinc-500"
                            >
                                +{pattern.symptoms.length - 3} more
                            </Badge>
                        )}
                    </div>
                )}
                
                {/* Evolution Trajectory (if present) */}
                {pattern.evolution && (
                    <div className="flex items-center gap-2 mt-3 p-2 rounded-lg bg-zinc-900/50">
                        <TrajectoryIcon className={`h-4 w-4 ${
                            pattern.evolution.mood_trajectory === 'improving' ? 'text-emerald-400' :
                            pattern.evolution.mood_trajectory === 'declining' ? 'text-red-400' :
                            'text-zinc-400'
                        }`} />
                        <span className="text-xs text-zinc-400">
                            {pattern.evolution.mood_trajectory?.charAt(0).toUpperCase()}
                            {pattern.evolution.mood_trajectory?.slice(1)} over {pattern.evolution.years_analyzed?.length || 0} years
                        </span>
                    </div>
                )}
            </div>
            
            {/* Expanded Details */}
            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        <div className="px-4 pb-4 pt-2 border-t border-zinc-800/50 space-y-4">
                            {/* Variance Analysis */}
                            {pattern.variance_analysis && (
                                <div className="space-y-2">
                                    <h4 className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                                        Period Variance
                                    </h4>
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        <div className="p-2 rounded-lg bg-emerald-950/30 border border-emerald-800/30">
                                            <span className="text-emerald-400">Best:</span>
                                            <span className="ml-1 text-zinc-300">
                                                {pattern.variance_analysis.highest_period}
                                            </span>
                                        </div>
                                        <div className="p-2 rounded-lg bg-red-950/30 border border-red-800/30">
                                            <span className="text-red-400">Challenging:</span>
                                            <span className="ml-1 text-zinc-300">
                                                {pattern.variance_analysis.lowest_period}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}
                            
                            {/* Theme Alignment */}
                            {pattern.theme_alignment && (
                                <div className="space-y-2">
                                    <h4 className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                                        Theme Alignment
                                    </h4>
                                    <div className="p-2 rounded-lg bg-purple-950/30 border border-purple-800/30">
                                        <p className="text-xs text-purple-300 mb-1">
                                            Period Theme: {pattern.theme_alignment.period_theme}
                                        </p>
                                        <p className="text-xs text-zinc-400">
                                            Your themes: {pattern.theme_alignment.journal_themes?.join(', ')}
                                        </p>
                                        <p className="text-xs text-purple-400 mt-1">
                                            Alignment: {formatConfidence(pattern.theme_alignment.alignment_score || 0)}
                                        </p>
                                    </div>
                                </div>
                            )}
                            
                            {/* Evidence Summary */}
                            {pattern.evidence_summary && pattern.evidence_summary.length > 0 && (
                                <div className="space-y-2">
                                    <h4 className="text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                                        Evidence
                                    </h4>
                                    <ul className="space-y-1">
                                        {pattern.evidence_summary.slice(0, 3).map((evidence, i) => (
                                            <li key={i} className="text-xs text-zinc-400 flex items-start gap-2">
                                                <span className="text-zinc-600">•</span>
                                                <span>{evidence}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                            
                            {/* Metadata */}
                            <div className="flex items-center justify-between text-[10px] text-zinc-600 pt-2 border-t border-zinc-800/50">
                                <span>First detected: {new Date(pattern.first_detected).toLocaleDateString()}</span>
                                <span>Updated: {new Date(pattern.last_updated).toLocaleDateString()}</span>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    )
}

/**
 * Summary Stats Card
 */
function SummaryStats({ className }: { className?: string }) {
    const { data: summary, isLoading } = useCyclicalPatternSummary()
    
    if (isLoading || !summary) {
        return (
            <div className={`grid grid-cols-4 gap-3 ${className}`}>
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-16 bg-zinc-900/50 rounded-lg animate-pulse" />
                ))}
            </div>
        )
    }
    
    const stats = [
        {
            label: 'Total Patterns',
            value: summary.total_patterns,
            icon: Eye,
            color: 'text-purple-400',
        },
        {
            label: 'Confirmed',
            value: summary.confirmed_patterns,
            icon: Sparkles,
            color: 'text-emerald-400',
        },
        {
            label: 'Avg Confidence',
            value: `${Math.round(summary.average_confidence * 100)}%`,
            icon: BarChart3,
            color: 'text-amber-400',
        },
        {
            label: 'Pattern Types',
            value: Object.keys(summary.patterns_by_type).length,
            icon: Activity,
            color: 'text-blue-400',
        },
    ]
    
    return (
        <div className={`grid grid-cols-2 md:grid-cols-4 gap-3 ${className}`}>
            {stats.map((stat, i) => (
                <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="p-3 rounded-xl border border-zinc-800/50 bg-zinc-900/50 backdrop-blur-sm"
                >
                    <div className="flex items-center gap-2 mb-1">
                        <stat.icon className={`h-3.5 w-3.5 ${stat.color}`} />
                        <span className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">
                            {stat.label}
                        </span>
                    </div>
                    <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
                </motion.div>
            ))}
        </div>
    )
}

/**
 * Filter Tabs
 */
function FilterTabs({ 
    selected, 
    onChange 
}: { 
    selected: FilterType
    onChange: (filter: FilterType) => void 
}) {
    const filters: { value: FilterType; label: string; icon: string }[] = [
        { value: 'all', label: 'All', icon: '🔮' },
        { value: 'period_symptom', label: 'Symptoms', icon: '🎯' },
        { value: 'variance', label: 'Variance', icon: '📊' },
        { value: 'theme_alignment', label: 'Themes', icon: '✨' },
        { value: 'evolution', label: 'Evolution', icon: '🌱' },
    ]
    
    return (
        <div className="flex items-center gap-1 p-1 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
            {filters.map((filter) => (
                <button
                    key={filter.value}
                    onClick={() => onChange(filter.value)}
                    className={`
                        px-3 py-1.5 rounded-lg text-xs font-medium transition-all
                        flex items-center gap-1.5
                        ${selected === filter.value
                            ? 'bg-purple-950/50 text-purple-300 border border-purple-500/30'
                            : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
                        }
                    `}
                >
                    <span>{filter.icon}</span>
                    <span className="hidden md:inline">{filter.label}</span>
                </button>
            ))}
        </div>
    )
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function CyclicalPatternsPanel({ className, compact = false }: CyclicalPatternsPanelProps) {
    const [filter, setFilter] = useState<FilterType>('all')
    const [expandedPatternId, setExpandedPatternId] = useState<string | null>(null)
    
    const patternFilter = filter === 'all' ? undefined : { pattern_type: filter }
    const { data, isLoading, error } = useCyclicalPatterns(patternFilter)
    const { mutate: triggerAnalysis, isPending: isAnalyzing } = useTriggerPatternAnalysis()
    
    const patterns = data?.patterns ?? []
    
    const handleTogglePattern = (patternId: string) => {
        setExpandedPatternId(prev => prev === patternId ? null : patternId)
    }
    
    if (error) {
        return (
            <Card className={`border-red-800/50 bg-red-950/20 ${className}`}>
                <CardContent className="p-6 text-center">
                    <p className="text-red-400">Failed to load cyclical patterns</p>
                </CardContent>
            </Card>
        )
    }
    
    return (
        <div className={`space-y-4 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-purple-950/30 border border-purple-500/30">
                        <Activity className="h-5 w-5 text-purple-400" />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold text-zinc-100">Cyclical Patterns</h2>
                        <p className="text-xs text-zinc-500">
                            Recurring experiences across your 52-day periods
                        </p>
                    </div>
                </div>
                
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => triggerAnalysis()}
                    disabled={isAnalyzing}
                    className="border-purple-500/30 text-purple-400 hover:bg-purple-950/30"
                >
                    {isAnalyzing ? (
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                        <Zap className="h-4 w-4 mr-2" />
                    )}
                    Analyze
                </Button>
            </div>
            
            {/* Summary Stats */}
            {!compact && <SummaryStats />}
            
            {/* Filter Tabs */}
            <FilterTabs selected={filter} onChange={setFilter} />
            
            {/* Patterns List */}
            <div className="space-y-3">
                {isLoading ? (
                    [...Array(3)].map((_, i) => (
                        <div key={i} className="h-32 bg-zinc-900/50 rounded-xl animate-pulse" />
                    ))
                ) : patterns.length === 0 ? (
                    <Card className="border-zinc-800/50 bg-zinc-950/80">
                        <CardContent className="p-8 text-center">
                            <Activity className="h-12 w-12 text-zinc-700 mx-auto mb-3" />
                            <p className="text-zinc-500 mb-2">No patterns detected yet</p>
                            <p className="text-xs text-zinc-600">
                                Continue journaling to discover cyclical patterns in your experience
                            </p>
                        </CardContent>
                    </Card>
                ) : (
                    <AnimatePresence mode="popLayout">
                        {patterns.map((pattern) => (
                            <PatternCard
                                key={pattern.id}
                                pattern={pattern}
                                expanded={expandedPatternId === pattern.id}
                                onToggle={() => handleTogglePattern(pattern.id)}
                            />
                        ))}
                    </AnimatePresence>
                )}
            </div>
            
            {/* Footer info */}
            {patterns.length > 0 && (
                <p className="text-[10px] text-zinc-600 text-center">
                    Patterns are detected by analyzing journal entries across multiple 52-day periods
                </p>
            )}
        </div>
    )
}
