import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

/**
 * Chronos/MAGI state from the backend.
 * Represents the user's current 52-day planetary period.
 */
export interface ChronosState {
    // Birth card (core identity)
    birth_card: {
        rank: number
        rank_name: string
        suit: string
        name: string
    } | null

    // Current period
    current_planet: string | null
    current_card: {
        card: string
        name: string
    } | null

    // Period timing
    period_start: string | null
    period_end: string | null
    days_remaining: number | null
    days_elapsed: number | null
    period_total: number
    progress_percent: number | null

    // Theme and guidance
    theme: string | null
    guidance: string | null

    // Additional context
    planetary_ruling_card: {
        rank: number
        suit: string
        name: string
    } | null
    year: number | null
    age: number | null

    // Karma cards (for birth card widget back)
    karma_cards: {
        debt: { card: string; name: string } | null
        gift: { card: string; name: string } | null
    } | null

    // Cache metadata
    cached_at: string | null
}

/**
 * Hook for fetching user's Chronos/MAGI state.
 * 
 * Powers the TimelineScrubber and BirthCardWidget components.
 * 
 * @example
 * ```tsx
 * const { data: chronos, isLoading } = useChronosState()
 * 
 * if (chronos) {
 *   console.log(`Day ${chronos.days_elapsed} of 52 (${chronos.current_planet})`)
 * }
 * ```
 */
export function useChronosState() {
    return useQuery({
        queryKey: ['chronos-state'],
        queryFn: async () => {
            const res = await api.get<ChronosState>('/api/v1/profile/chronos')
            return res.data
        },
        staleTime: 1000 * 60 * 5, // 5 minutes - periods change slowly
        refetchInterval: 1000 * 60 * 15, // 15 minutes background refresh
        retry: 1, // Don't retry excessively if user hasn't onboarded
    })
}

/**
 * Helper to format a card for display (e.g., "K♥" or "7♠")
 */
export function formatCardSymbol(card: { rank?: number; rank_name?: string; suit?: string } | null): string {
    if (!card) return '?'
    
    const suitSymbols: Record<string, string> = {
        'HEARTS': '♥',
        'DIAMONDS': '♦',
        'CLUBS': '♣',
        'SPADES': '♠',
        'Hearts': '♥',
        'Diamonds': '♦',
        'Clubs': '♣',
        'Spades': '♠',
    }
    
    const rankSymbols: Record<number, string> = {
        1: 'A',
        11: 'J',
        12: 'Q',
        13: 'K',
    }
    
    const rank = card.rank ? (rankSymbols[card.rank] || card.rank.toString()) : '?'
    const suit = card.suit ? (suitSymbols[card.suit] || card.suit[0]) : '?'
    
    return `${rank}${suit}`
}

/**
 * Helper to get suit color class
 */
export function getSuitColor(suit: string | undefined): string {
    if (!suit) return 'text-zinc-400'
    const normalizedSuit = suit.toLowerCase()
    if (normalizedSuit === 'hearts' || normalizedSuit === 'diamonds') {
        return 'text-red-500'
    }
    return 'text-zinc-900'
}

/**
 * Get planet emoji/icon
 */
export function getPlanetEmoji(planet: string | null): string {
    const planetEmojis: Record<string, string> = {
        'Mercury': '☿',
        'Venus': '♀',
        'Mars': '♂',
        'Jupiter': '♃',
        'Saturn': '♄',
        'Uranus': '⛢',
        'Neptune': '♆',
        'Pluto': '♇',
        'Long Range': '∞',
        'Result': '☉',
    }
    return planet ? planetEmojis[planet] || '●' : '●'
}
