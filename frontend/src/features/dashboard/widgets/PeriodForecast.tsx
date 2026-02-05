import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Calendar, ChevronRight, Sparkles } from 'lucide-react'
import { useChronosState, getPlanetEmoji } from '@/hooks/useChronosState'
import { motion } from 'framer-motion'

interface ForecastDay {
    date: Date
    dayOfPeriod: number
    periodCard: string
    planet: string
    isTransition: boolean
    daysRemaining?: number
}

/**
 * PeriodForecast Widget
 * 
 * Displays a 7-day forecast of the user's magi chronos progression.
 * Shows upcoming period transitions and planetary ruler changes.
 * 
 * Features:
 * - Next 7 days of period progression
 * - Highlights period transition days
 * - Shows planetary rulers and card names
 * - Animated transitions with Framer Motion
 * - Glass morphism styling matching Cosmic Brutalist theme
 */
export default function PeriodForecast() {
    const { data: chronos, isLoading } = useChronosState()

    if (isLoading || !chronos) {
        return (
            <Card className="h-full animate-pulse">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                        <Calendar className="h-5 w-5" />
                        Next 7 Days
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        {[...Array(7)].map((_, i) => (
                            <div key={i} className="h-12 bg-muted/50 rounded-lg" />
                        ))}
                    </div>
                </CardContent>
            </Card>
        )
    }

    const forecast = generateForecast(chronos)

    return (
        <Card className="h-full border-zinc-800/50 bg-zinc-950/80 backdrop-blur-sm">
            <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg text-zinc-100">
                    <Calendar className="h-5 w-5 text-purple-400" />
                    Next 7 Days
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
                {forecast.map((day, index) => (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className={`
                            relative p-3 rounded-lg border transition-all duration-200
                            ${day.isTransition 
                                ? 'border-purple-500/50 bg-purple-950/30 shadow-lg shadow-purple-500/20' 
                                : 'border-zinc-800/50 bg-zinc-900/50 hover:bg-zinc-800/50'
                            }
                        `}
                    >
                        <div className="flex items-center justify-between">
                            {/* Left: Date and Day of Week */}
                            <div className="flex-shrink-0">
                                <p className="text-sm font-medium text-zinc-200">
                                    {formatDate(day.date)}
                                </p>
                                <p className="text-xs text-zinc-500">
                                    {day.date.toLocaleDateString('en-US', { weekday: 'short' })}
                                </p>
                            </div>

                            {/* Center: Period Card */}
                            <div className="flex items-center gap-2 flex-1 mx-4">
                                <span className="text-lg" title={day.planet}>
                                    {getPlanetEmoji(day.planet)}
                                </span>
                                <div className="flex-1">
                                    <p className="text-sm font-medium text-zinc-300">
                                        {day.periodCard}
                                    </p>
                                    <p className="text-xs text-zinc-500">
                                        Day {day.dayOfPeriod}/52
                                    </p>
                                </div>
                            </div>

                            {/* Right: Transition Indicator */}
                            {day.isTransition ? (
                                <div className="flex items-center gap-1 text-purple-400">
                                    <Sparkles className="h-4 w-4 animate-pulse" />
                                    <span className="text-xs font-medium">New Period</span>
                                </div>
                            ) : (
                                <ChevronRight className="h-4 w-4 text-zinc-600" />
                            )}
                        </div>

                        {/* Transition Details */}
                        {day.isTransition && day.daysRemaining !== undefined && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                className="mt-2 pt-2 border-t border-purple-500/30"
                            >
                                <p className="text-xs text-purple-300">
                                    🌟 Transitioning in {day.daysRemaining} day{day.daysRemaining !== 1 ? 's' : ''}
                                </p>
                            </motion.div>
                        )}
                    </motion.div>
                ))}
            </CardContent>
        </Card>
    )
}

/**
 * Generate 7-day forecast from current chronos state
 */
function generateForecast(chronos: any): ForecastDay[] {
    const forecast: ForecastDay[] = []
    const today = new Date()
    
    // Current period info
    let currentDayOfPeriod = chronos.period_total - (chronos.days_remaining || 0)
    let currentCard = chronos.current_card?.name || 'Unknown'
    let currentPlanet = chronos.current_planet || 'Unknown'
    let daysUntilTransition = chronos.days_remaining || 0

    // Birth cards rotation (7 cards x 52 days = 364 days, then reset)
    const birthCards = chronos.birth_cards || []
    const currentCardIndex = birthCards.findIndex((card: any) => card.name === currentCard)

    for (let i = 0; i < 7; i++) {
        const forecastDate = new Date(today)
        forecastDate.setDate(today.getDate() + i)

        // Calculate day within current or next period
        const effectiveDayOffset = i
        const isTransitionDay = effectiveDayOffset === daysUntilTransition
        
        let dayOfPeriod = currentDayOfPeriod + effectiveDayOffset
        let periodCard = currentCard
        let planet = currentPlanet

        // Handle period transition
        if (effectiveDayOffset >= daysUntilTransition) {
            // We've transitioned to next period
            const daysIntoPeriod = effectiveDayOffset - daysUntilTransition
            dayOfPeriod = daysIntoPeriod + 1 // Days are 1-indexed
            
            // Get next card in cycle
            if (birthCards.length > 0) {
                const nextCardIndex = (currentCardIndex + 1) % birthCards.length
                const nextCard = birthCards[nextCardIndex]
                periodCard = nextCard.name
                planet = nextCard.ruling_planet || 'Unknown'
            }
        }

        // Cap at 52 days (edge case for last days of cycle)
        if (dayOfPeriod > 52) {
            dayOfPeriod = dayOfPeriod % 52 || 52
        }

        forecast.push({
            date: forecastDate,
            dayOfPeriod,
            periodCard,
            planet,
            isTransition: isTransitionDay,
            daysRemaining: isTransitionDay ? daysUntilTransition : undefined
        })
    }

    return forecast
}

/**
 * Format date for display (MM/DD)
 */
function formatDate(date: Date): string {
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${month}/${day}`
}
