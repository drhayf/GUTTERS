import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { Send, Moon, Sun, X } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { useKeyboardHeight } from '@/hooks/useKeyboardHeight'
import { useQuery } from '@tanstack/react-query'

interface ReflectionPrompt {
    id: number
    prompt_text: string
    topic: string
}

interface ContextualComposerProps {
    replyingTo: ReflectionPrompt | null
    onCancelReply: () => void
}

export function ContextualComposer({ replyingTo, onCancelReply }: ContextualComposerProps) {
    const [content, setContent] = useState('')
    const [isFocused, setIsFocused] = useState(false)
    const keyboardHeight = useKeyboardHeight()
    const queryClient = useQueryClient()
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    // Cosmic Context Fetching
    const { data: cosmicData } = useQuery({
        queryKey: ['dashboard-cosmic'],
        queryFn: async () => {
            const res = await api.get('/api/v1/dashboard/cosmic')
            return res.data
        },
        staleTime: 1000 * 60 * 5
    })

    // Actually, Phase 16 used /api/v1/dashboard/cosmic or similar. 
    // Let's try to assume we can get it or pass it in. 
    // For fidelity, let's replicate the logic or create a useCosmicStatus hook later.
    // I'll implement a basic one here for now.

    const submitMutation = useMutation({
        mutationFn: async () => {
            const payload = {
                content,
                prompt_id: replyingTo?.id,
                // We could explicitly pass context_snapshot here if the backend didn't auto-capture it.
                // But the backend `JournalEntry` has `context_snapshot` field.
                // We should pass it from the client side "Context" we verify visually.
                context_snapshot: {
                    moon: cosmicData?.moon_phase,
                    kp: cosmicData?.geomagnetic_index,
                    client_time: new Date().toISOString()
                }
            }
            await api.post('/api/v1/insights/journal', payload)
        },
        onSuccess: () => {
            setContent('')
            if (replyingTo) onCancelReply()
            queryClient.invalidateQueries({ queryKey: ['journal-entries'] })
            queryClient.invalidateQueries({ queryKey: ['reflection-prompts'] })
        }
    })

    const handleSubmit = () => {
        if (!content.trim()) return
        submitMutation.mutate()
    }

    return (
        <motion.div
            layout
            className={`
                relative bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md rounded-2xl border
                transition-all duration-300 overflow-hidden
                ${isFocused ? 'shadow-lg border-purple-500/30' : 'border-border'}
            `}
        >
            {/* Context Bar */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-black/5 dark:border-white/5 bg-black/5 dark:bg-white/5">
                <div className="flex items-center gap-3 text-xs font-medium text-muted-foreground">
                    <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-background/50">
                        <Moon className="w-3 h-3" />
                        <span>{cosmicData?.moon_phase || 'Observing...'}</span>
                    </div>
                    <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-background/50">
                        <Sun className="w-3 h-3 text-amber-500" />
                        <span>Kp {cosmicData?.geomagnetic_index || '?'}</span>
                    </div>
                </div>

                {replyingTo && (
                    <div className="flex items-center gap-2">
                        <span className="text-xs text-purple-600 font-medium truncate max-w-[150px]">
                            Replying to: {replyingTo.topic}
                        </span>
                        <button
                            onClick={onCancelReply}
                            className="p-1 hover:bg-black/10 rounded-full"
                        >
                            <X className="w-3 h-3" />
                        </button>
                    </div>
                )}
            </div>

            {/* Editor */}
            <div className="relative">
                <textarea
                    ref={textareaRef}
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                    placeholder={replyingTo ? `Answering: ${replyingTo.prompt_text}...` : "What's on your mind?..."}
                    className="w-full bg-transparent p-4 min-h-[120px] resize-none focus:outline-none text-base leading-relaxed"
                />

                <div className="flex justify-end p-4 pt-0">
                    <button
                        onClick={handleSubmit}
                        disabled={!content.trim() || submitMutation.isPending}
                        className={`
                            flex items-center gap-2 px-4 py-2 rounded-full font-medium transition-all
                            ${content.trim()
                                ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/30 hover:bg-purple-700'
                                : 'bg-muted text-muted-foreground cursor-not-allowed'
                            }
                        `}
                    >
                        {submitMutation.isPending ? (
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <Send className="w-4 h-4" />
                        )}
                        <span>Log Entry</span>
                    </button>
                </div>
            </div>

            {/* Mobile Keyboard Spacer when focused */}
            {isFocused && (keyboardHeight > 0) && (
                <div style={{ height: keyboardHeight }} />
            )}
        </motion.div>
    )
}
