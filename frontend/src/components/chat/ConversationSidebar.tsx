import { Plus, MessageSquare, Search, MoreVertical, Trash2, Sparkles, LayoutDashboard, Terminal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useConversations } from '@/features/chat/hooks/useConversations'
import { useChatStore } from '@/stores/chatStore'
import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'

export default function ConversationSidebar() {
    const [searchQuery, setSearchQuery] = useState('')
    const navigate = useNavigate()
    const location = useLocation()
    const { currentConversationId } = useChatStore()

    const { data: conversations, createConversation, deleteConversation } = useConversations()

    const mainChat = conversations?.find((c: any) => c.name === 'General' || c.name === 'Master Chat')
    const otherConversations = conversations?.filter((c: any) => c.id !== mainChat?.id)

    const filteredConversations = otherConversations?.filter((conv: any) =>
        conv.name.toLowerCase().includes(searchQuery.toLowerCase())
    )

    const handleCreate = () => {
        const name = prompt('Enter a name for your conversation:')
        if (name) {
            createConversation.mutate(name, {
                onSuccess: (data) => {
                    navigate(`/chat/${data.id}`)
                }
            })
        }
    }

    return (
        <div className="flex flex-col h-full bg-secondary/30 border-r border-border">
            {/* Primary Navigation */}
            <div className="p-4 space-y-1">
                <div
                    onClick={() => navigate('/dashboard')}
                    className={`
                        flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-all duration-200
                        ${location.pathname === '/dashboard'
                            ? 'bg-background shadow-sm border border-border text-foreground font-semibold'
                            : 'hover:bg-background/60 text-muted-foreground hover:text-foreground font-medium'
                        }
                    `}
                >
                    <LayoutDashboard className={`w-4 h-4 ${location.pathname === '/dashboard' ? 'text-primary' : 'text-foreground/20'}`} />
                    <span className="text-sm">Dashboard</span>
                </div>

                <div
                    onClick={() => navigate('/chat')}
                    className={`
                        flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-all duration-200
                        ${location.pathname.startsWith('/chat')
                            ? 'bg-background shadow-sm border border-border text-foreground font-semibold'
                            : 'hover:bg-background/60 text-muted-foreground hover:text-foreground font-medium'
                        }
                    `}
                >
                    <MessageSquare className={`w-4 h-4 ${location.pathname.startsWith('/chat') ? 'text-primary' : 'text-foreground/20'}`} />
                    <span className="text-sm">Master Chat</span>
                </div>

                <div
                    onClick={() => navigate('/control-room')}
                    className={`
                        flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-all duration-200
                        ${location.pathname === '/control-room'
                            ? 'bg-background shadow-sm border border-border text-foreground font-semibold'
                            : 'hover:bg-background/60 text-muted-foreground hover:text-foreground font-medium'
                        }
                    `}
                >
                    <Terminal className={`w-4 h-4 ${location.pathname === '/control-room' ? 'text-primary' : 'text-foreground/20'}`} />
                    <span className="text-sm">Control Room</span>
                </div>
            </div>

            <Separator className="opacity-50" />

            {/* Header */}
            <div className="p-4 space-y-4">
                <div className="flex items-center justify-between px-1">
                    <span className="text-[11px] font-bold uppercase tracking-widest text-foreground/40">Conversations</span>
                    <Button
                        onClick={handleCreate}
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 text-foreground/50 hover:text-primary transition-colors"
                    >
                        <Plus className="w-4 h-4" />
                    </Button>
                </div>

                {/* Main Chat Pin */}
                {mainChat && (
                    <div
                        onClick={() => navigate(`/chat/${mainChat.id}`)}
                        className={`
                            group relative flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer
                            transition-all duration-200 border border-transparent mb-2
                            ${currentConversationId === mainChat.id
                                ? 'bg-background shadow-sm border-border text-foreground'
                                : 'hover:bg-background/60 text-muted-foreground hover:text-foreground'
                            }
                        `}
                    >
                        <div className="relative">
                            <Sparkles className={`w-4 h-4 shrink-0 transition-colors ${currentConversationId === mainChat.id ? 'text-primary' : 'text-foreground/20'}`} />
                            {currentConversationId === mainChat.id && (
                                <motion.div
                                    layoutId="active-origin-glow"
                                    className="absolute inset-0 bg-primary/20 blur-md rounded-full -z-10"
                                />
                            )}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className={`text-sm truncate transition-colors ${currentConversationId === mainChat.id ? 'font-semibold' : 'font-medium'}`}>
                                Main Chat
                            </p>
                            <p className="text-[10px] text-muted-foreground/60 mt-0.5">
                                Primary Master Interface
                            </p>
                        </div>
                        {currentConversationId === mainChat.id && (
                            <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                        )}
                    </div>
                )}

                <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground/60" />
                    <Input
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search history..."
                        className="pl-9 h-8.5 bg-background/50 border-border/50 text-sm focus-visible:ring-primary/20"
                    />
                </div>
            </div>

            <Separator className="opacity-50" />

            {/* Conversation list */}
            <ScrollArea className="flex-1 px-3 py-4 custom-scrollbar">
                <div className="space-y-1">
                    <AnimatePresence initial={false}>
                        {filteredConversations?.map((conv: any) => (
                            <motion.div
                                key={conv.id}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -10 }}
                                transition={{ duration: 0.2 }}
                            >
                                <div
                                    onClick={() => navigate(`/chat/${conv.id}`)}
                                    className={`
                    group relative flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer
                    transition-all duration-200 border border-transparent
                    ${currentConversationId === conv.id
                                            ? 'bg-background shadow-sm border-border text-foreground'
                                            : 'hover:bg-background/60 text-muted-foreground hover:text-foreground'
                                        }
                  `}
                                >
                                    <MessageSquare className={`w-4 h-4 shrink-0 transition-colors ${currentConversationId === conv.id ? 'text-primary' : 'text-foreground/20'}`} />

                                    <div className="flex-1 min-w-0">
                                        <p className={`text-sm truncate transition-colors ${currentConversationId === conv.id ? 'font-semibold' : 'font-medium'}`}>
                                            {conv.name}
                                        </p>
                                        <p className="text-[10px] text-muted-foreground/60 mt-0.5">
                                            {conv.message_count} messages
                                        </p>
                                    </div>

                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className={`h-7 w-7 transition-opacity ${currentConversationId === conv.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
                                                onClick={(e) => e.stopPropagation()}
                                            >
                                                <MoreVertical className="w-3.5 h-3.5" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end" className="w-40">
                                            <DropdownMenuItem
                                                onClick={(e) => {
                                                    e.stopPropagation()
                                                    if (confirm('Delete this conversation forever?')) {
                                                        deleteConversation.mutate(conv.id)
                                                    }
                                                }}
                                                className="text-destructive focus:text-destructive focus:bg-destructive/5"
                                            >
                                                <Trash2 className="w-3.5 h-3.5 mr-2" />
                                                <span className="text-xs font-medium">Delete Chat</span>
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {filteredConversations?.length === 0 && (
                        <div className="text-center py-8 text-xs text-muted-foreground/50 italic">
                            No conversations found
                        </div>
                    )}
                </div>
            </ScrollArea>
        </div>
    )
}
