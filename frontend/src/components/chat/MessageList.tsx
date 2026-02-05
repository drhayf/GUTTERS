import { ScrollArea } from '@/components/ui/scroll-area'
import ChatMessage from './ChatMessage'
import { ComponentRenderer } from '@/components/generative/ComponentRenderer'
import { useEffect, useRef } from 'react'

interface Message {
    id: number
    role: 'user' | 'assistant' | 'system'
    content: string
    created_at: string
    metadata?: {
        modules_consulted?: string[]
        confidence?: number
        component?: any
        trace?: any
    }
}

interface MessageListProps {
    messages: Message[]
}

export default function MessageList({ messages }: MessageListProps) {
    const scrollRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' })
        }
    }, [messages])

    return (
        <ScrollArea className="flex-1 px-4 md:px-6 custom-scrollbar min-w-0 w-full">
            <div className="max-w-4xl mx-auto py-10 space-y-10 min-w-0 w-full">
                {messages.map((message, i) => (
                    <div key={message.id || i} className="space-y-6 min-w-0 w-full">
                        <ChatMessage message={message} />

                        {/* Render generative UI component if present */}
                        {message.metadata?.component && (
                            <div className="pl-0 md:pl-12 w-full max-w-full overflow-hidden min-w-0">
                                <ComponentRenderer component={message.metadata.component} />
                            </div>
                        )}
                    </div>
                ))}

                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
                        <div className="w-12 h-12 rounded-full bg-primary/5 flex items-center justify-center">
                            <Sparkles className="w-6 h-6 text-primary/40" />
                        </div>
                        <div className="space-y-1">
                            <h2 className="text-lg font-medium text-foreground/80">How can I assist you today?</h2>
                            <p className="text-sm text-muted-foreground/70 max-w-sm mx-auto">
                                Ask me about your astrological transits, human design, or start a new journal entry.
                            </p>
                        </div>
                    </div>
                )}
                <div ref={scrollRef} className="h-4" />
            </div>
        </ScrollArea>
    )
}

import { Sparkles } from 'lucide-react'
