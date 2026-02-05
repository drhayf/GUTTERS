import { motion, AnimatePresence } from 'framer-motion'
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area'
import { Sparkles, X } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

interface ReflectionPrompt {
    id: number
    prompt_text: string
    topic: string
    status: string
    created_at: string
}

interface ActiveReflectionsProps {
    onSelectPrompt: (prompt: ReflectionPrompt | null) => void
    selectedPrompt: ReflectionPrompt | null
}

export function ActiveReflections({ onSelectPrompt, selectedPrompt }: ActiveReflectionsProps) {
    const queryClient = useQueryClient()

    const { data: prompts = [] } = useQuery({
        queryKey: ['reflection-prompts'],
        queryFn: async () => {
            const res = await api.get<ReflectionPrompt[]>('/api/v1/insights/prompts')
            return res.data
        }
    })

    const dismissMutation = useMutation({
        mutationFn: async (id: number) => {
            await api.patch(`/api/v1/insights/prompts/${id}/dismiss`)
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['reflection-prompts'] })
            if (selectedPrompt) onSelectPrompt(null)
        }
    })

    if (prompts.length === 0) return null

    return (
        <div className="w-full mb-6">
            <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-purple-500" />
                <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
                    Active Reflections
                </h3>
            </div>

            <ScrollArea className="w-full whitespace-nowrap rounded-md">
                <div className="flex space-x-4 p-1">
                    <AnimatePresence>
                        {prompts.map((prompt) => (
                            <motion.div
                                key={prompt.id}
                                layout
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, scale: 0.9 }}
                                className={`
                                    relative flex-none w-[280px] h-[140px] p-5 rounded-xl border transition-all cursor-pointer
                                    backdrop-blur-sm group
                                    ${selectedPrompt?.id === prompt.id
                                        ? 'bg-purple-500/10 border-purple-500/50 ring-2 ring-purple-500/20'
                                        : 'bg-white/40 dark:bg-zinc-900/40 border-white/50 dark:border-zinc-800 hover:border-purple-500/30 hover:shadow-lg'
                                    }
                                `}
                                onClick={() => onSelectPrompt(prompt)}
                            >
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        dismissMutation.mutate(prompt.id)
                                    }}
                                    className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 p-1 hover:bg-black/5 rounded-full transition-all"
                                >
                                    <X className="w-3 h-3 text-muted-foreground" />
                                </button>

                                <div className="h-full flex flex-col justify-between">
                                    <p className="text-base font-medium leading-snug whitespace-normal line-clamp-3 text-foreground/90">
                                        {prompt.prompt_text}
                                    </p>
                                    <div className="flex items-center justify-between mt-2">
                                        <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-300 font-medium">
                                            {prompt.topic}
                                        </span>
                                        <span className="text-[10px] text-muted-foreground">
                                            {new Date(prompt.created_at).toLocaleDateString()}
                                        </span>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
                <ScrollBar orientation="horizontal" />
            </ScrollArea>
        </div>
    )
}
