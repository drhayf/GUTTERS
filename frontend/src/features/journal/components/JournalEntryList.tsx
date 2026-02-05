import { motion } from 'framer-motion'
import { Calendar, Moon, Tag, Zap } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'
import { format } from 'date-fns'

interface JournalEntry {
    id: number
    content: string
    mood_score: number | null
    tags: string[]
    context_snapshot: {
        moon?: string
        kp?: number
        client_time?: string
    } | null
    created_at: string
    source?: 'USER' | 'SYSTEM'
}

export function JournalEntryList() {
    const { data: entries = [], isLoading } = useQuery({
        queryKey: ['journal-entries'],
        queryFn: async () => {
            const res = await api.get<JournalEntry[]>('/api/v1/insights/journal')
            return res.data
        }
    })

    if (isLoading) {
        return <div className="space-y-4">
            {[1, 2, 3].map(i => (
                <div key={i} className="h-32 rounded-xl bg-muted/20 animate-pulse" />
            ))}
        </div>
    }

    if (entries.length === 0) {
        return (
            <div className="text-center py-12 text-muted-foreground">
                <p>No entries yet. Start writing above.</p>
            </div>
        )
    }

    return (
        <div className="space-y-4 pb-24">
            {entries.map((entry, index) => (
                <motion.div
                    key={entry.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className={`group relative backdrop-blur-sm border p-5 rounded-2xl transition-all ${entry.source === 'SYSTEM'
                            ? 'bg-violet-50/40 dark:bg-violet-900/10 border-violet-200 dark:border-violet-800'
                            : 'bg-white/40 dark:bg-zinc-900/40 border-white/20 dark:border-zinc-800 hover:shadow-lg hover:border-purple-500/20'
                        }`}
                >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                            {entry.source === 'SYSTEM' ? (
                                <>
                                    <div className="flex items-center gap-1.5 text-violet-600 dark:text-violet-400 font-mono tracking-wider">
                                        <Zap className="w-3.5 h-3.5" />
                                        <span>SYSTEM LOG</span>
                                    </div>
                                    <span className="text-violet-300 dark:text-violet-700">•</span>
                                </>
                            ) : (
                                <Calendar className="w-3.5 h-3.5" />
                            )}
                            <span className={entry.source === 'SYSTEM' ? 'font-mono text-[10px] opacity-70' : ''}>
                                {format(new Date(entry.created_at), 'PPP p')}
                            </span>
                        </div>

                        {/* Context Icons */}
                        {entry.context_snapshot && (
                            <div className="flex items-center gap-2">
                                {entry.context_snapshot.moon && (
                                    <div className="p-1 rounded-full bg-indigo-50 dark:bg-indigo-900/20 text-indigo-500" title={entry.context_snapshot.moon}>
                                        <Moon className="w-3 h-3" />
                                    </div>
                                )}
                                {entry.context_snapshot.kp !== undefined && (
                                    <div className="p-1 rounded-full bg-amber-50 dark:bg-amber-900/20 text-amber-500" title={`Kp ${entry.context_snapshot.kp}`}>
                                        <Zap className="w-3 h-3" />
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Content */}
                    <p className={`text-foreground/90 leading-relaxed whitespace-pre-wrap ${entry.source === 'SYSTEM'
                            ? 'font-mono text-sm text-violet-900 dark:text-violet-100'
                            : 'font-serif text-[1.05rem]'
                        }`}>
                        {entry.content}
                    </p>

                    {/* Footer / Tags */}
                    {entry.tags && entry.tags.length > 0 && (
                        <div className={`flex flex-wrap gap-2 mt-4 pt-3 border-t ${entry.source === 'SYSTEM'
                                ? 'border-violet-200/50 dark:border-violet-700/30'
                                : 'border-black/5 dark:border-white/5'
                            }`}>
                            {entry.tags.map(tag => (
                                <span key={tag} className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider ${entry.source === 'SYSTEM'
                                        ? 'bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300'
                                        : 'bg-secondary text-secondary-foreground'
                                    }`}>
                                    <Tag className="w-2.5 h-2.5 mr-1" />
                                    {tag}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Visual flourish for refined entries (mock logic until backend flag exists) */}
                    {entry.tags.includes('refined') && (
                        <div className="absolute -right-1 -top-1 w-3 h-3 bg-purple-500 rounded-full animate-pulse" title="Triggered Refinement" />
                    )}
                </motion.div>
            ))}
        </div>
    )
}
