import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Check, BookOpen, Loader2 } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import api from '@/lib/api'

interface OracleReading {
    id: number
    card: {
        rank: number
        suit: string
        name: string
    }
    hexagram: {
        number: number
        line: number
    }
    synthesis: string
    diagnostic_question: string
    accepted: boolean
    reflected: boolean
    created_at: string
}

interface DrawResponse {
    status: string
    reading: OracleReading
}

interface ActionResponse {
    status: string
    message: string
    quest?: any
    prompt?: any
}

export default function OraclePage() {
    const [reading, setReading] = useState<OracleReading | null>(null)
    const [isRevealing, setIsRevealing] = useState(false)
    const [showSynthesis, setShowSynthesis] = useState(false)
    const [displayedText, setDisplayedText] = useState('')

    // Draw mutation
    const drawMutation = useMutation({
        mutationFn: async () => {
            const response = await api.post<DrawResponse>('/intelligence/oracle/draw')
            return response.data.reading
        },
        onSuccess: (data) => {
            setReading(data)
            setIsRevealing(true)
            setTimeout(() => {
                setIsRevealing(false)
                setShowSynthesis(true)
                typewriterEffect(data.synthesis)
            }, 2000)
        },
        onError: (error: any) => {
            console.error('Oracle draw error:', error)
            console.error('Error response:', error.response?.data)
            alert(`Error performing Oracle draw: ${error.response?.data?.detail || error.message}`)
        }
    })

    // Accept mutation
    const acceptMutation = useMutation({
        mutationFn: async (readingId: number) => {
            const response = await api.post<ActionResponse>(`/intelligence/oracle/${readingId}/accept`)
            return response.data
        },
        onSuccess: () => {
            if (reading) {
                setReading({ ...reading, accepted: true })
            }
        }
    })

    // Reflect mutation
    const reflectMutation = useMutation({
        mutationFn: async (readingId: number) => {
            const response = await api.post<ActionResponse>(`/intelligence/oracle/${readingId}/reflect`)
            return response.data
        },
        onSuccess: () => {
            if (reading) {
                setReading({ ...reading, reflected: true })
            }
        }
    })

    const typewriterEffect = (text: string) => {
        let i = 0
        const speed = 15 // ms per character
        const timer = setInterval(() => {
            if (i < text.length) {
                setDisplayedText(text.slice(0, i + 1))
                i++
            } else {
                clearInterval(timer)
            }
        }, speed)
    }

    const handleDraw = () => {
        setReading(null)
        setShowSynthesis(false)
        setDisplayedText('')
        drawMutation.mutate()
    }

    const getSuitSymbol = (suit: string) => {
        const symbols: { [key: string]: string } = {
            'Hearts': '♥',
            'Clubs': '♣',
            'Diamonds': '♦',
            'Spades': '♠'
        }
        return symbols[suit] || ''
    }

    const getSuitColor = (suit: string) => {
        return suit === 'Hearts' || suit === 'Diamonds' ? 'text-red-500' : 'text-gray-900 dark:text-white'
    }

    return (
        <div className="min-h-screen w-full overflow-y-auto bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-purple-950 dark:to-indigo-950">
            <div className="max-w-6xl mx-auto px-4 py-12 space-y-12">
                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center space-y-4"
                >
                    <div className="flex items-center justify-center gap-3">
                        <Sparkles className="w-10 h-10 text-purple-600 dark:text-purple-400" />
                        <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600 bg-clip-text text-transparent">
                            The Oracle
                        </h1>
                        <Sparkles className="w-10 h-10 text-purple-600 dark:text-purple-400" />
                    </div>
                    <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
                        Draw from the sacred deck. The cards will speak. The hexagram will reveal.
                        What you seek is seeking you.
                    </p>
                </motion.div>

                {/* Draw Button / Card Display */}
                <div className="flex flex-col items-center gap-8">
                    {!reading && !drawMutation.isPending && (
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            transition={{ delay: 0.2 }}
                        >
                            <Button
                                onClick={handleDraw}
                                size="lg"
                                className="relative overflow-hidden bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-12 py-6 text-xl font-semibold shadow-2xl"
                            >
                                <motion.div
                                    animate={{
                                        scale: [1, 1.2, 1],
                                        rotate: [0, 180, 360]
                                    }}
                                    transition={{
                                        duration: 2,
                                        repeat: Infinity,
                                        ease: "easeInOut"
                                    }}
                                    className="absolute inset-0 bg-gradient-to-r from-yellow-400/20 to-pink-400/20"
                                />
                                <Sparkles className="w-6 h-6 mr-3" />
                                Initialize Query
                            </Button>
                        </motion.div>
                    )}

                    {drawMutation.isPending && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex flex-col items-center gap-6"
                        >
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                            >
                                <Loader2 className="w-16 h-16 text-purple-600" />
                            </motion.div>
                            <p className="text-xl text-purple-600 dark:text-purple-400 font-medium">
                                Shuffling the cosmic deck...
                            </p>
                        </motion.div>
                    )}

                    {/* Card Reveal */}
                    <AnimatePresence mode="wait">
                        {reading && (
                            <motion.div
                                initial={{ rotateY: -90, opacity: 0, scale: 0.8 }}
                                animate={{
                                    rotateY: isRevealing ? [0, 180, 360] : 0,
                                    opacity: 1,
                                    scale: 1
                                }}
                                transition={{
                                    rotateY: { duration: 2, ease: "easeInOut" },
                                    opacity: { duration: 0.3 },
                                    scale: { duration: 0.3 }
                                }}
                                style={{ perspective: 1000 }}
                                className="relative"
                            >
                                <Card className="w-[400px] h-[600px] bg-gradient-to-br from-purple-100 via-pink-100 to-indigo-100 dark:from-purple-900 dark:via-pink-900 dark:to-indigo-900 border-4 border-purple-400 shadow-2xl overflow-hidden">
                                    <div className="w-full h-full flex flex-col items-center justify-center p-8 relative">
                                        {/* Card Symbol */}
                                        <motion.div
                                            initial={{ scale: 0 }}
                                            animate={{ scale: 1 }}
                                            transition={{ delay: 0.5, type: "spring" }}
                                            className={`text-9xl font-bold ${getSuitColor(reading.card.suit)}`}
                                        >
                                            {getSuitSymbol(reading.card.suit)}
                                        </motion.div>

                                        {/* Card Name */}
                                        <motion.div
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: 0.8 }}
                                            className="text-3xl font-bold text-gray-800 dark:text-white mt-4"
                                        >
                                            {reading.card.name}
                                        </motion.div>

                                        {/* Hexagram Overlay */}
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.5 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            transition={{ delay: 1.2 }}
                                            className="mt-8 p-6 bg-white/60 dark:bg-black/40 backdrop-blur-md rounded-2xl border-2 border-purple-300 dark:border-purple-600"
                                        >
                                            <div className="text-center space-y-2">
                                                <p className="text-sm text-purple-600 dark:text-purple-300 font-semibold">
                                                    I-CHING HEXAGRAM
                                                </p>
                                                <p className="text-5xl font-bold text-purple-800 dark:text-purple-200">
                                                    {reading.hexagram.number}
                                                </p>
                                                <div className="flex items-center justify-center gap-2">
                                                    <div className="h-1 w-1 rounded-full bg-purple-600" />
                                                    <p className="text-lg text-purple-700 dark:text-purple-300 font-medium">
                                                        Line {reading.hexagram.line}
                                                    </p>
                                                    <div className="h-1 w-1 rounded-full bg-purple-600" />
                                                </div>
                                            </div>
                                        </motion.div>

                                        {/* Sacred Geometry Background */}
                                        <div className="absolute inset-0 opacity-10 pointer-events-none">
                                            <svg viewBox="0 0 400 600" className="w-full h-full">
                                                <circle cx="200" cy="300" r="150" stroke="currentColor" fill="none" strokeWidth="2" />
                                                <circle cx="200" cy="300" r="120" stroke="currentColor" fill="none" strokeWidth="1" />
                                                <circle cx="200" cy="300" r="90" stroke="currentColor" fill="none" strokeWidth="1" />
                                            </svg>
                                        </div>
                                    </div>
                                </Card>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Synthesis & Question */}
                {showSynthesis && reading && (
                    <motion.div
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                        className="space-y-8 max-w-4xl mx-auto"
                    >
                        {/* Synthesis */}
                        <Card className="p-8 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md border-2 border-purple-200 dark:border-purple-800 shadow-xl">
                            <h3 className="text-2xl font-bold text-purple-800 dark:text-purple-300 mb-4 flex items-center gap-2">
                                <Sparkles className="w-6 h-6" />
                                The Synthesis
                            </h3>
                            <p className="text-lg text-gray-700 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">
                                {displayedText}
                            </p>
                        </Card>

                        {/* Diagnostic Question */}
                        {displayedText === reading.synthesis && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: 0.5 }}
                            >
                                <Card className="p-8 bg-gradient-to-r from-pink-100 to-purple-100 dark:from-pink-900/40 dark:to-purple-900/40 border-2 border-pink-300 dark:border-pink-700 shadow-xl">
                                    <h3 className="text-xl font-bold text-pink-800 dark:text-pink-300 mb-4">
                                        The Question
                                    </h3>
                                    <p className="text-lg text-gray-800 dark:text-gray-200 italic leading-relaxed">
                                        "{reading.diagnostic_question}"
                                    </p>
                                </Card>
                            </motion.div>
                        )}

                        {/* Action Buttons */}
                        {displayedText === reading.synthesis && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 1 }}
                                className="flex flex-col sm:flex-row gap-4 justify-center"
                            >
                                <Button
                                    onClick={() => acceptMutation.mutate(reading.id)}
                                    disabled={reading.accepted || acceptMutation.isPending}
                                    size="lg"
                                    className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-8 py-6 text-lg font-semibold shadow-lg"
                                >
                                    {acceptMutation.isPending ? (
                                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                    ) : (
                                        <Check className="w-5 h-5 mr-2" />
                                    )}
                                    {reading.accepted ? 'Mission Accepted' : 'Accept Mission'}
                                </Button>

                                <Button
                                    onClick={() => reflectMutation.mutate(reading.id)}
                                    disabled={reading.reflected || reflectMutation.isPending}
                                    size="lg"
                                    variant="outline"
                                    className="border-2 border-purple-400 text-purple-700 dark:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 px-8 py-6 text-lg font-semibold shadow-lg"
                                >
                                    {reflectMutation.isPending ? (
                                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                    ) : (
                                        <BookOpen className="w-5 h-5 mr-2" />
                                    )}
                                    {reading.reflected ? 'Reflection Created' : 'Reflect'}
                                </Button>
                            </motion.div>
                        )}

                        {/* Draw Again */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 1.5 }}
                            className="text-center"
                        >
                            <Button
                                onClick={handleDraw}
                                variant="ghost"
                                className="text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20"
                            >
                                <Sparkles className="w-4 h-4 mr-2" />
                                Draw Again
                            </Button>
                        </motion.div>
                    </motion.div>
                )}
            </div>
        </div>
    )
}
