/**
 * useCyclicalPatterns Hook
 * 
 * Fetches and manages cyclical pattern data from the Observer module.
 * Provides access to detected patterns, confidence levels, and evolution tracking.
 * 
 * Features:
 * - Real-time pattern fetching with caching
 * - Pattern filtering by type, period, and confidence
 * - Summary statistics computation
 * - Integration with chronos state
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

// =============================================================================
// TYPES
// =============================================================================

export interface CyclicalPattern {
    id: string
    pattern_type: 'period_symptom' | 'variance' | 'theme_alignment' | 'evolution'
    period_card: string
    planetary_ruler: string
    confidence: number
    observation_count: number
    description: string
    symptoms?: string[]
    mood_average?: number
    mood_variance?: number
    first_detected: string
    last_updated: string
    evidence_summary?: string[]
    variance_analysis?: {
        highest_period?: string
        lowest_period?: string
        variance_score?: number
    }
    theme_alignment?: {
        period_theme?: string
        journal_themes?: string[]
        alignment_score?: number
    }
    evolution?: {
        years_analyzed?: number[]
        mood_trajectory?: 'improving' | 'declining' | 'stable' | 'volatile'
        theme_evolution?: Record<string, string>
    }
}

export interface CyclicalPatternSummary {
    total_patterns: number
    confirmed_patterns: number
    average_confidence: number
    patterns_by_type: Record<string, number>
    patterns_by_period: Record<string, number>
    strongest_pattern?: CyclicalPattern
    most_recent_pattern?: CyclicalPattern
}

export interface CyclicalPatternsResponse {
    patterns: CyclicalPattern[]
    summary: CyclicalPatternSummary
}

export interface PatternFilter {
    pattern_type?: string
    planetary_ruler?: string
    min_confidence?: number
    period_card?: string
}

// =============================================================================
// API FUNCTIONS
// =============================================================================

async function fetchCyclicalPatterns(filter?: PatternFilter): Promise<CyclicalPatternsResponse> {
    const params = new URLSearchParams()
    
    if (filter?.pattern_type) params.append('pattern_type', filter.pattern_type)
    if (filter?.planetary_ruler) params.append('planetary_ruler', filter.planetary_ruler)
    if (filter?.min_confidence) params.append('min_confidence', filter.min_confidence.toString())
    if (filter?.period_card) params.append('period_card', filter.period_card)
    
    const queryString = params.toString()
    const url = `/api/v1/observer/cyclical${queryString ? `?${queryString}` : ''}`
    
    const response = await api.get(url)
    return response.data
}

async function fetchPatternSummary(): Promise<CyclicalPatternSummary> {
    const response = await api.get('/api/v1/observer/cyclical/summary')
    return response.data
}

async function triggerPatternAnalysis(): Promise<{ patterns_detected: number; message: string }> {
    const response = await api.post('/api/v1/observer/cyclical/analyze')
    return response.data
}

// =============================================================================
// HOOKS
// =============================================================================

/**
 * Main hook for fetching cyclical patterns with optional filtering.
 */
export function useCyclicalPatterns(filter?: PatternFilter) {
    return useQuery({
        queryKey: ['cyclical-patterns', filter],
        queryFn: () => fetchCyclicalPatterns(filter),
        staleTime: 1000 * 60 * 5, // 5 minutes
        refetchOnWindowFocus: false,
    })
}

/**
 * Hook for fetching pattern summary statistics.
 */
export function useCyclicalPatternSummary() {
    return useQuery({
        queryKey: ['cyclical-patterns-summary'],
        queryFn: fetchPatternSummary,
        staleTime: 1000 * 60 * 5,
        refetchOnWindowFocus: false,
    })
}

/**
 * Hook for triggering pattern analysis.
 */
export function useTriggerPatternAnalysis() {
    const queryClient = useQueryClient()
    
    return useMutation({
        mutationFn: triggerPatternAnalysis,
        onSuccess: () => {
            // Invalidate pattern queries to refetch fresh data
            queryClient.invalidateQueries({ queryKey: ['cyclical-patterns'] })
            queryClient.invalidateQueries({ queryKey: ['cyclical-patterns-summary'] })
        },
    })
}

/**
 * Computed hook for patterns grouped by planetary ruler.
 */
export function usePatternsByPlanet() {
    const { data, ...rest } = useCyclicalPatterns()
    
    const patternsByPlanet = data?.patterns.reduce((acc, pattern) => {
        const planet = pattern.planetary_ruler
        if (!acc[planet]) acc[planet] = []
        acc[planet].push(pattern)
        return acc
    }, {} as Record<string, CyclicalPattern[]>) ?? {}
    
    return {
        ...rest,
        data: patternsByPlanet,
        patterns: data?.patterns ?? [],
        summary: data?.summary,
    }
}

/**
 * Hook for patterns related to a specific period card.
 */
export function usePeriodPatterns(periodCard: string) {
    return useCyclicalPatterns({ period_card: periodCard })
}

/**
 * Hook for high-confidence (confirmed) patterns only.
 */
export function useConfirmedPatterns() {
    return useCyclicalPatterns({ min_confidence: 0.85 })
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Get display color for confidence level.
 */
export function getConfidenceColor(confidence: number): string {
    if (confidence >= 0.85) return 'text-emerald-400'
    if (confidence >= 0.7) return 'text-amber-400'
    if (confidence >= 0.5) return 'text-orange-400'
    return 'text-zinc-400'
}

/**
 * Get background color for confidence level.
 */
export function getConfidenceBgColor(confidence: number): string {
    if (confidence >= 0.85) return 'bg-emerald-500/20 border-emerald-500/30'
    if (confidence >= 0.7) return 'bg-amber-500/20 border-amber-500/30'
    if (confidence >= 0.5) return 'bg-orange-500/20 border-orange-500/30'
    return 'bg-zinc-500/20 border-zinc-500/30'
}

/**
 * Get icon/emoji for pattern type.
 */
export function getPatternTypeIcon(patternType: string): string {
    switch (patternType) {
        case 'period_symptom': return '🎯'
        case 'variance': return '📊'
        case 'theme_alignment': return '✨'
        case 'evolution': return '🌱'
        default: return '🔮'
    }
}

/**
 * Get human-readable label for pattern type.
 */
export function getPatternTypeLabel(patternType: string): string {
    switch (patternType) {
        case 'period_symptom': return 'Recurring Experience'
        case 'variance': return 'Period Variance'
        case 'theme_alignment': return 'Theme Alignment'
        case 'evolution': return 'Long-term Evolution'
        default: return 'Pattern'
    }
}

/**
 * Get trajectory icon for evolution patterns.
 */
export function getTrajectoryIcon(trajectory?: string): string {
    switch (trajectory) {
        case 'improving': return '📈'
        case 'declining': return '📉'
        case 'stable': return '➡️'
        case 'volatile': return '🎢'
        default: return '❓'
    }
}

/**
 * Format confidence as percentage.
 */
export function formatConfidence(confidence: number): string {
    return `${Math.round(confidence * 100)}%`
}
