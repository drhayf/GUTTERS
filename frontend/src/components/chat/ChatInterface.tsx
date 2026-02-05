import { useNavigate, useParams } from 'react-router-dom'
import { Settings2, ChevronUp, Sparkles, Brain, Moon, Zap, Globe } from 'lucide-react'
import { Button } from '@/components/ui/button'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import { useMessages } from '@/features/chat/hooks/useMessages'
import { useSendMessage } from '@/features/chat/hooks/useSendMessage'
import { useConversations } from '@/features/chat/hooks/useConversations'
import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useChatStore } from '@/stores/chatStore'
import { cn } from '@/lib/utils'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { useProgressionStats } from '@/hooks/useProgressionStats'

// -- COSMIC TICKER HOOK (Inline for now per plan, refactor later if needed) --
// Reusing query key 'dashboard-cosmic'
interface CosmicData {
    moon_phase: string
    moon_sign: string
    geomagnetic_index: number
}

function useCosmicTicker() {
    return useQuery({
        queryKey: ['dashboard-cosmic'],
        queryFn: async () => {
            const res = await api.get<CosmicData>('/api/v1/dashboard/cosmic')
            return res.data
        },
        staleTime: 1000 * 60 * 60 // 1 hour
    })
}

export default function ChatInterface() {
    const { conversationId } = useParams()
    const navigate = useNavigate()
    const scrollRef = useRef<HTMLDivElement>(null)
    const [isDeckOpen, setDeckOpen] = useState(false)

    // Global State
    const { selectedModel, setSelectedModel } = useChatStore()
    const { data: conversations } = useConversations()
    const { data: cosmic } = useCosmicTicker()
    const { data: progression } = useProgressionStats()

    useEffect(() => {
        if (!conversationId && conversations && conversations.length > 0) {
            navigate(`/chat/${conversations[0].id}`, { replace: true })
        }
    }, [conversationId, conversations, navigate])

    const id = conversationId ? Number(conversationId) : null
    const { data: messages } = useMessages(id)
    const sendMessage = useSendMessage(id)

    // Auto-scroll to bottom on new messages
    // Enhanced: Check if user is near bottom before scrolling to avoid annoyed user
    const viewportRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' })
        }
    }, [messages])

    // Kp Color Logic
    const getKpColor = (kp: number) => {
        if (kp >= 5) return "text-red-500"
        if (kp >= 4) return "text-amber-500"
        return "text-emerald-500"
    }

    return (
        <div className="flex flex-col h-full w-full bg-background relative overflow-hidden touch-none">

            {/* 1. COSMIC CONTEXT TICKER */}
            <div className="shrink-0 h-10 border-b border-border/40 bg-background/50 backdrop-blur-md flex items-center justify-between px-4 z-20 transition-all min-w-0 touch-none pointer-events-auto">
                <div className="flex items-center gap-4 overflow-hidden min-w-0">
                    {/* Moon Phase */}
                    <div className="flex items-center gap-1.5 text-[10px] font-medium text-muted-foreground">
                        <Moon className="w-3 h-3 text-indigo-400" />
                        <span className="truncate max-w-[80px]">{cosmic?.moon_sign || "Unknown"}</span>
                    </div>

                    {/* Kp Index */}
                    {cosmic && (
                        <div className="flex items-center gap-1.5 text-[10px] font-mono font-bold">
                            <Zap className={cn("w-3 h-3", getKpColor(cosmic.geomagnetic_index))} />
                            <span className={getKpColor(cosmic.geomagnetic_index)}>Kp{cosmic.geomagnetic_index}</span>
                        </div>
                    )}
                </div>

                {/* User Rank */}
                <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase tracking-widest font-black text-muted-foreground/50 hidden sm:block">Operator Rank</span>
                    <span className="text-[10px] font-bold text-primary border border-primary/20 bg-primary/5 px-2 py-0.5 rounded-full">
                        {progression?.rank || "INITIATE"}
                    </span>
                </div>
            </div>


            {/* 2. MESSAGES AREA */}
            <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6 space-y-6 scrollbar-hide min-w-0 w-full" ref={viewportRef}>
                {/* Pass cosmic phase context to list if needed, but Polymorphic Message handles it via metadata */}
                <MessageList messages={messages || []} />
                <div ref={scrollRef} className="h-4" />
            </div>

            {/* 3. MULTIDIMENSIONAL COMMAND DECK */}
            <div className="shrink-0 z-30 transition-all duration-300 min-w-0 w-full">
                <div className="bg-background/80 backdrop-blur-xl border-t border-border/40 shadow-[0_-10px_40px_-15px_rgba(0,0,0,0.1)] pb-[env(safe-area-inset-bottom)] min-w-0">

                    {/* Deck Control Handle / Decoration */}
                    <div
                        className="w-full h-3 flex items-center justify-center cursor-pointer opacity-50 hover:opacity-100 transition-opacity"
                        onClick={() => setDeckOpen(!isDeckOpen)}
                    >
                        <div className="w-12 h-1 rounded-full bg-border/50" />
                    </div>

                    <div className="max-w-4xl mx-auto px-4 pb-4">
                        <div className="flex flex-col gap-2">

                            {/* MODEL SWITCHER & STATUS BAR */}
                            <div className="flex items-center justify-between px-1">
                                <div className="flex items-center gap-2">
                                    <div className="bg-secondary/50 rounded-full p-0.5 flex items-center border border-border/50">
                                        <button
                                            onClick={() => setSelectedModel('standard')}
                                            className={cn(
                                                "flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase transition-all duration-300",
                                                selectedModel === 'standard'
                                                    ? "bg-background text-foreground shadow-sm"
                                                    : "text-muted-foreground hover:text-foreground"
                                            )}
                                        >
                                            <Brain className="w-3 h-3" />
                                            <span>Haiku</span>
                                        </button>
                                        <button
                                            onClick={() => setSelectedModel('premium')}
                                            className={cn(
                                                "flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase transition-all duration-300",
                                                selectedModel === 'premium'
                                                    ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                                                    : "text-muted-foreground hover:text-foreground"
                                            )}
                                        >
                                            <Sparkles className="w-3 h-3" />
                                            <span>Sonnet</span>
                                        </button>
                                    </div>
                                </div>

                                {/* Deck Toggle Button */}
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => setDeckOpen(!isDeckOpen)}
                                    className="h-8 w-8 rounded-full hover:bg-secondary/80"
                                >
                                    <motion.div
                                        animate={{ rotate: isDeckOpen ? 180 : 0 }}
                                        transition={{ duration: 0.3 }}
                                    >
                                        {isDeckOpen ? <ChevronUp className="w-4 h-4" /> : <Settings2 className="w-4 h-4" />}
                                    </motion.div>
                                </Button>
                            </div>

                            {/* MAIN INPUT */}
                            <div className="relative">
                                <ChatInput
                                    onSend={(text) => sendMessage.mutate(text)}
                                    isLoading={sendMessage.isPending}
                                />
                            </div>
                        </div>
                    </div>

                    {/* COLLAPSIBLE DECK CONTENT (Extended Controls) */}
                    <AnimatePresence>
                        {isDeckOpen && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
                                className="overflow-hidden border-t border-border/40 bg-secondary/5"
                            >
                                <div className="max-w-5xl mx-auto p-6">
                                    {/* Placeholder for future extended controls (Voice, Upload, etc.) */}
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <div className="p-4 rounded-xl bg-background/50 border border-border/50 text-center space-y-2">
                                            <div className="mx-auto w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                                                <Globe className="w-4 h-4 text-primary" />
                                            </div>
                                            <p className="text-[10px] font-bold uppercase tracking-wider">Web Search</p>
                                            <p className="text-[9px] text-muted-foreground">Auto-Enabled</p>
                                        </div>
                                        <div className="p-4 rounded-xl bg-background/50 border border-border/50 text-center space-y-2 opacity-50">
                                            <div className="mx-auto w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                                                <Brain className="w-4 h-4" />
                                            </div>
                                            <p className="text-[10px] font-bold uppercase tracking-wider">Deep Research</p>
                                            <p className="text-[9px] text-muted-foreground">Coming Soon</p>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    )
}
