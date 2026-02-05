import { useState } from 'react'
import { motion } from 'framer-motion'
import { Heart, Diamond, Club, Spade, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useChronosState, getPlanetEmoji } from '@/hooks/useChronosState'

/**
 * BirthCardWidget
 * 
 * A high-fidelity digital playing card display showing the user's birth card.
 * Flips on hover/tap to reveal Karma Cards (Debts & Gifts).
 * 
 * Design: Cosmic Brutalist aesthetic - clean geometry, heavy serif typography,
 * glass panels with zinc borders.
 */
export default function BirthCardWidget() {
    const { data: chronos, isLoading } = useChronosState()
    const [isFlipped, setIsFlipped] = useState(false)

    if (isLoading) {
        return (
            <div className="w-full aspect-[2.5/3.5] max-w-[180px] mx-auto">
                <div className="w-full h-full animate-pulse bg-white/40 rounded-2xl border border-white/20" />
            </div>
        )
    }

    if (!chronos?.birth_card) {
        return (
            <div className="w-full aspect-[2.5/3.5] max-w-[180px] mx-auto">
                <div className="w-full h-full flex items-center justify-center bg-zinc-100/50 rounded-2xl border border-zinc-200/50 backdrop-blur-sm">
                    <span className="text-xs text-zinc-400">No birth card</span>
                </div>
            </div>
        )
    }

    const { birth_card, karma_cards, current_planet } = chronos

    // Get suit info
    const suitInfo = getSuitInfo(birth_card.suit)
    const rankDisplay = getRankDisplay(birth_card.rank)

    return (
        <div 
            className="w-full aspect-[2.5/3.5] max-w-[180px] mx-auto perspective-1000"
            onMouseEnter={() => setIsFlipped(true)}
            onMouseLeave={() => setIsFlipped(false)}
            onClick={() => setIsFlipped(!isFlipped)}
        >
            <motion.div
                className="relative w-full h-full"
                animate={{ rotateY: isFlipped ? 180 : 0 }}
                transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
                style={{ transformStyle: 'preserve-3d' }}
            >
                {/* FRONT FACE */}
                <div 
                    className={cn(
                        "absolute inset-0 backface-hidden",
                        "rounded-2xl border-2 overflow-hidden",
                        "bg-gradient-to-br from-white via-zinc-50 to-zinc-100",
                        "shadow-xl shadow-black/10",
                        suitInfo.borderColor
                    )}
                >
                    {/* Card Content */}
                    <div className="relative h-full p-3 flex flex-col">
                        {/* Top Left - Rank & Suit */}
                        <div className="flex items-start">
                            <div className={cn("flex flex-col items-center", suitInfo.textColor)}>
                                <span className="text-2xl font-serif font-black leading-none">
                                    {rankDisplay}
                                </span>
                                <suitInfo.Icon className="w-5 h-5 mt-0.5" />
                            </div>
                        </div>

                        {/* Center - Large Suit Symbol */}
                        <div className="flex-1 flex items-center justify-center">
                            <div className="relative">
                                <suitInfo.Icon 
                                    className={cn(
                                        "w-16 h-16 drop-shadow-sm",
                                        suitInfo.textColor
                                    )} 
                                />
                                {/* Planetary ruler indicator */}
                                {current_planet && (
                                    <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-zinc-900/90 flex items-center justify-center">
                                        <span className="text-[10px] text-white">
                                            {getPlanetEmoji(current_planet)}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Bottom Right - Inverted Rank & Suit */}
                        <div className="flex justify-end">
                            <div className={cn("flex flex-col items-center rotate-180", suitInfo.textColor)}>
                                <span className="text-2xl font-serif font-black leading-none">
                                    {rankDisplay}
                                </span>
                                <suitInfo.Icon className="w-5 h-5 mt-0.5" />
                            </div>
                        </div>

                        {/* Card Name Label */}
                        <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-zinc-100/90 to-transparent">
                            <p className="text-[9px] font-semibold text-center text-zinc-500 uppercase tracking-wider">
                                {birth_card.name || `${birth_card.rank_name} of ${birth_card.suit}`}
                            </p>
                        </div>
                    </div>

                    {/* Subtle texture overlay */}
                    <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent pointer-events-none" />
                </div>

                {/* BACK FACE - Karma Cards */}
                <div 
                    className={cn(
                        "absolute inset-0 backface-hidden",
                        "rounded-2xl border-2 overflow-hidden",
                        "bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900",
                        "shadow-xl shadow-black/20",
                        "border-zinc-700"
                    )}
                    style={{ transform: 'rotateY(180deg)' }}
                >
                    <div className="relative h-full p-3 flex flex-col">
                        {/* Header */}
                        <div className="flex items-center justify-center gap-1.5 mb-3">
                            <Sparkles className="w-3 h-3 text-amber-400" />
                            <span className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">
                                Karma Cards
                            </span>
                            <Sparkles className="w-3 h-3 text-amber-400" />
                        </div>

                        {/* Karma Cards Display */}
                        <div className="flex-1 flex flex-col justify-center space-y-3">
                            {/* Debt Card */}
                            <div className="bg-zinc-800/50 rounded-lg p-2 border border-zinc-700/50">
                                <p className="text-[8px] font-bold uppercase tracking-wider text-red-400/80 mb-1">
                                    Karma Debt
                                </p>
                                {karma_cards?.debt ? (
                                    <KarmaCardMini card={karma_cards.debt} />
                                ) : (
                                    <p className="text-xs text-zinc-500 italic">None (Fixed Card)</p>
                                )}
                            </div>

                            {/* Gift Card */}
                            <div className="bg-zinc-800/50 rounded-lg p-2 border border-zinc-700/50">
                                <p className="text-[8px] font-bold uppercase tracking-wider text-emerald-400/80 mb-1">
                                    Karma Gift
                                </p>
                                {karma_cards?.gift ? (
                                    <KarmaCardMini card={karma_cards.gift} />
                                ) : (
                                    <p className="text-xs text-zinc-500 italic">None (Fixed Card)</p>
                                )}
                            </div>
                        </div>

                        {/* Footer hint */}
                        <p className="text-[8px] text-center text-zinc-600 mt-2">
                            Tap to flip back
                        </p>
                    </div>

                    {/* Pattern overlay */}
                    <div className="absolute inset-0 opacity-5 pointer-events-none">
                        <div className="absolute inset-0" style={{
                            backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 10px, white 10px, white 11px)'
                        }} />
                    </div>
                </div>
            </motion.div>
        </div>
    )
}

/**
 * Mini karma card display for the back face
 */
function KarmaCardMini({ card }: { card: { card: string; name: string } }) {
    // Parse card string like "7H" or "KS"
    const suitChar = card.card?.slice(-1) || ''
    const suitMap: Record<string, string> = { 'H': 'Hearts', 'D': 'Diamonds', 'C': 'Clubs', 'S': 'Spades' }
    const suit = suitMap[suitChar] || 'Hearts'
    const suitInfo = getSuitInfo(suit)

    return (
        <div className="flex items-center gap-2">
            <suitInfo.Icon className={cn("w-4 h-4", suitInfo.textColor)} />
            <span className="text-sm font-serif font-bold text-zinc-200">
                {card.name || card.card}
            </span>
        </div>
    )
}

/**
 * Get suit icon and colors
 */
function getSuitInfo(suit: string) {
    const normalized = suit?.toLowerCase() || ''
    
    if (normalized === 'hearts') {
        return {
            Icon: Heart,
            textColor: 'text-red-500',
            borderColor: 'border-red-200',
            bgColor: 'bg-red-50',
        }
    }
    if (normalized === 'diamonds') {
        return {
            Icon: Diamond,
            textColor: 'text-red-500',
            borderColor: 'border-red-200',
            bgColor: 'bg-red-50',
        }
    }
    if (normalized === 'clubs') {
        return {
            Icon: Club,
            textColor: 'text-zinc-800',
            borderColor: 'border-zinc-300',
            bgColor: 'bg-zinc-50',
        }
    }
    // Spades
    return {
        Icon: Spade,
        textColor: 'text-zinc-800',
        borderColor: 'border-zinc-300',
        bgColor: 'bg-zinc-50',
    }
}

/**
 * Get rank display character
 */
function getRankDisplay(rank: number | undefined): string {
    if (!rank) return '?'
    const rankMap: Record<number, string> = {
        1: 'A',
        11: 'J',
        12: 'Q',
        13: 'K',
    }
    return rankMap[rank] || rank.toString()
}
