import { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

interface ChatInputProps {
    onSend: (message: string) => void
    isLoading?: boolean
}

export default function ChatInput({ onSend, isLoading }: ChatInputProps) {
    const [message, setMessage] = useState('')
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto'
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
        }
    }, [message])

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!message.trim() || isLoading) return

        onSend(message)
        setMessage('')
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        // Submit on Enter (not Shift+Enter)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSubmit(e)
        }
    }

    return (
        <div className="bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-t border-border">
            <form onSubmit={handleSubmit} className="max-w-4xl mx-auto p-4 md:p-6">
                <div className="relative flex gap-3 items-end">
                    <Textarea
                        ref={textareaRef}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask anything..."
                        disabled={isLoading}
                        className="min-h-[48px] max-h-[200px] py-3.5 pr-12 resize-none bg-background shadow-sm border-border focus-visible:ring-primary/20 transition-all duration-200"
                        rows={1}
                    />

                    <Button
                        type="submit"
                        disabled={!message.trim() || isLoading}
                        size="icon"
                        className="absolute right-2 bottom-2 h-8 w-8 rounded-md transition-all duration-200"
                    >
                        {isLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                            <Send className="w-4 h-4" />
                        )}
                    </Button>
                </div>

                <div className="flex justify-between items-center mt-3 px-1">
                    <p className="text-[11px] text-muted-foreground/60 font-medium">
                        GUTTERS Intelligence Layer v1.0
                    </p>
                    <p className="text-[11px] text-muted-foreground/50">
                        Shift + Enter for new line
                    </p>
                </div>
            </form>
        </div>
    )
}
