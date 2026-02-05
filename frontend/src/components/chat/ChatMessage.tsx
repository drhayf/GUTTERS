import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ChevronDown, Brain, Sparkles, User, Cpu, Zap, Database } from 'lucide-react'
import { useState } from 'react'
import { motion } from 'framer-motion'
import QuestItem from '@/features/quests/components/QuestItem'

interface ChatMessageProps {
    message: {
        role: 'user' | 'assistant' | 'system' | 'system_event'
        content: string
        metadata?: {
            modules_consulted?: string[]
            confidence?: number
            type?: string // 'system_event' | 'system_log'
            component?: {
                component_type: string
                data: any
            }
            trace?: {
                thinking_steps?: Array<{ step: number; description: string }>
                tools_used?: Array<{ tool: string; operation: string; result_summary: string; latency_ms: number }>
                model_info?: {
                    provider: string;
                    model: string;
                    tokens_in: number;
                    tokens_out: number;
                    latency_ms: number;
                    cost_estimate_usd?: number;
                }
            }
            event_phase?: string
            event_type?: string
            model_tier?: string

            // System Event Payload
            title?: string
            amount?: number
            icon?: string
            flavor_text?: string
        }
    }
}

export default function ChatMessage({ message }: ChatMessageProps) {
    const [showTrace, setShowTrace] = useState(false)
    const isUser = message.role === 'user'
    const hasTrace = message.metadata?.trace || message.metadata?.modules_consulted

    // -- POLYMORPHIC TYPE 1: SYSTEM EVENT (GAME LOG) --
    if (message.role === 'system_event' || message.metadata?.type === 'system_event') {
        const meta = message.metadata || {}
        const iconName = meta.icon || 'zap'
        const IconComponent = iconName === 'star' ? Sparkles : Zap

        return (
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex justify-center my-4 opacity-90 transition-opacity"
            >
                <div className="bg-secondary/30 border border-border/60 rounded-lg px-4 py-2 flex items-center gap-4 backdrop-blur-sm max-w-lg shadow-sm">
                    {/* Icon Box */}
                    <div className={`p-2 rounded-full ${meta.event_type === 'level_up' ? 'bg-amber-500/10 text-amber-500' : 'bg-primary/10 text-primary'}`}>
                        <IconComponent className="w-4 h-4" />
                    </div>

                    <div className="flex flex-col min-w-0">
                        <div className="flex items-baseline gap-2">
                            <span className="text-[13px] font-semibold text-foreground/90 tracking-wide">
                                {meta.title || message.content.replace("SYSTEM EVENT:", "").trim()}
                            </span>
                            {(meta.amount ?? 0) > 0 && (
                                <span className="text-[11px] font-mono font-bold text-emerald-500/90">
                                    +{meta.amount} XP
                                </span>
                            )}
                        </div>

                        {/* LLM Flavor Text */}
                        {meta.flavor_text && (
                            <span className="text-[11px] text-muted-foreground/80 italic line-clamp-1" title={meta.flavor_text}>
                                {meta.flavor_text}
                            </span>
                        )}
                    </div>
                </div>
            </motion.div>
        )
    }

    // -- POLYMORPHIC TYPE 2: STANDARD CHAT --
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="group max-w-3xl mx-auto w-full min-w-0"
        >
            <div className={`flex gap-4 min-w-0 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Avatar */}
                <Avatar className="w-8 h-8 mt-1 border border-border shrink-0">
                    <AvatarFallback className={isUser ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}>
                        {isUser ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
                    </AvatarFallback>
                </Avatar>

                {/* Message Bubble + Extras */}
                <div className={`flex flex-col gap-1 min-w-0 max-w-[85%] md:max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>

                    {/* The Bubble Itself */}
                    <div className={`
                        relative px-4 py-3 rounded-2xl text-[15px] leading-relaxed shadow-sm
                        max-w-full min-w-0 break-words overflow-wrap-anywhere word-break-break-word
                        ${isUser
                            ? 'bg-primary text-white rounded-tr-sm'
                            : 'bg-white/60 backdrop-blur-md border border-white/40 text-foreground/90 rounded-tl-sm'
                        }
                    `}>
                        {/* Phase Badge (Inside Bubble for Context) */}
                        {message.metadata?.event_phase && (
                            <div className="mb-2 flex items-center gap-1.5">
                                <Badge variant="outline" className={`
                                    text-[10px] h-5 px-1.5 border-primary/20 bg-primary/5 text-primary
                                    ${message.metadata.event_phase === 'peak' ? 'animate-pulse border-amber-500/50 text-amber-600 bg-amber-50' : ''}
                                `}>
                                    {message.metadata.event_phase === 'peak' ? '⚡ ' : '🌊 '}
                                    {message.metadata.event_phase.toUpperCase()} PHASE
                                </Badge>
                            </div>
                        )}

                        <div className="whitespace-pre-wrap break-words overflow-wrap-anywhere max-w-full min-w-0">
                            {message.content}
                        </div>
                    </div>

                    {/* -- COMPONENT INJECTION: QUEST ITEMS -- */}
                    {/* Rendered OUTSIDE the bubble for full width fidelity */}
                    {message.metadata?.component?.component_type === 'QUEST_ITEM' && (
                        <div className="w-full mt-2 transform transition-all hover:scale-[1.01]">
                            <QuestItem
                                quest={message.metadata.component.data}
                                onEdit={() => { }} // Read-only in chat for now or wire up later
                            />
                        </div>
                    )}

                    {/* Observable AI trace (subtle, outside bubble) */}
                    {!isUser && hasTrace && (
                        <Collapsible open={showTrace} onOpenChange={setShowTrace} className="mt-1 w-full max-w-lg min-w-0">
                            <CollapsibleTrigger className="flex items-center gap-1.5 text-[10px] font-medium text-muted-foreground/60 hover:text-primary transition-colors pl-1">
                                <Brain className="w-3 h-3" />
                                <span>Thinking Process</span>
                                <ChevronDown className={`w-3 h-3 transition-transform duration-200 ${showTrace ? 'rotate-180' : ''}`} />
                                {message.metadata?.model_tier && (
                                    <span className="ml-auto text-[9px] uppercase tracking-widest opacity-50">
                                        {message.metadata.model_tier}
                                    </span>
                                )}
                            </CollapsibleTrigger>


                            <CollapsibleContent>
                                <div className="mt-2.5 space-y-3">

                                    {/* 1. THOUGHT PROCESS (High Fidelity) */}
                                    {message.metadata?.trace?.thinking_steps && (
                                        <div className="bg-card/50 backdrop-blur-sm border border-primary/20 rounded-lg overflow-hidden shadow-sm">
                                            <div className="bg-primary/5 px-3 py-2 border-b border-primary/10 flex items-center gap-2">
                                                <Sparkles className="w-3.5 h-3.5 text-primary" />
                                                <span className="text-xs font-semibold text-primary/90 tracking-wide uppercase">Reasoning Chain</span>
                                            </div>
                                            <div className="p-3 relative">
                                                {/* Vertical line connecting steps */}
                                                <div className="absolute left-[19px] top-4 bottom-4 w-px bg-border/60" />

                                                <div className="space-y-3">
                                                    {message.metadata.trace.thinking_steps.map((step, i) => (
                                                        <div key={i} className="relative flex gap-3 text-xs leading-relaxed group/step">
                                                            {/* Step Number Bubble */}
                                                            <div className="relative z-10 flex-none w-5 h-5 rounded-full bg-background border border-border flex items-center justify-center text-[9px] font-mono text-muted-foreground group-hover/step:border-primary/50 group-hover/step:text-primary transition-colors">
                                                                {step.step}
                                                            </div>
                                                            {/* Step Content */}
                                                            <div className="py-0.5 text-muted-foreground group-hover/step:text-foreground transition-colors">
                                                                {step.description}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* 2. TECHNICAL METADATA (Grouped) */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">

                                        {/* Sources & Tools */}
                                        <div className="bg-muted/30 rounded-lg p-3 border border-border/50 space-y-3">
                                            {/* Sources */}
                                            {message.metadata?.modules_consulted && (
                                                <div>
                                                    <p className="text-[10px] uppercase tracking-wider font-bold text-foreground/40 mb-1.5 flex items-center gap-1.5">
                                                        <Database className="w-3 h-3" />
                                                        Sources
                                                    </p>
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {message.metadata.modules_consulted.map((module, i) => (
                                                            <Badge key={i} variant="secondary" className="text-[10px] h-5 px-1.5 bg-background border-border/60 text-foreground/70">
                                                                {module}
                                                            </Badge>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Tools */}
                                            {message.metadata?.trace?.tools_used && message.metadata.trace.tools_used.length > 0 && (
                                                <div>
                                                    <p className="text-[10px] uppercase tracking-wider font-bold text-foreground/40 mb-1.5 flex items-center gap-1.5 pt-1">
                                                        <Cpu className="w-3 h-3" />
                                                        System Tools
                                                    </p>
                                                    <div className="space-y-1.5">
                                                        {message.metadata.trace.tools_used.map((tool, i) => (
                                                            <div key={i} className="flex items-center justify-between text-[10px] bg-background/40 px-2 py-1 rounded border border-border/30">
                                                                <span className="font-medium text-foreground/70 truncate max-w-[120px]" title={`${tool.tool}.${tool.operation}`}>
                                                                    {tool.tool}.{tool.operation}
                                                                </span>
                                                                <span className="font-mono text-muted-foreground">{tool.latency_ms}ms</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Model Telemetry */}
                                        {message.metadata?.trace?.model_info && (
                                            <div className="bg-muted/30 rounded-lg p-3 border border-border/50">
                                                <p className="text-[10px] uppercase tracking-wider font-bold text-foreground/40 mb-2 flex items-center gap-1.5">
                                                    <Zap className="w-3 h-3" />
                                                    Model Performance
                                                </p>
                                                <div className="grid grid-cols-2 gap-x-2 gap-y-3">
                                                    <div>
                                                        <div className="text-[9px] text-muted-foreground uppercase">Model</div>
                                                        <div className="text-[11px] font-medium text-foreground truncate" title={message.metadata.trace.model_info.model}>
                                                            {message.metadata.trace.model_info.model.split('/').pop()}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <div className="text-[9px] text-muted-foreground uppercase">Latency</div>
                                                        <div className="text-[11px] font-mono text-foreground">{message.metadata.trace.model_info.latency_ms}ms</div>
                                                    </div>
                                                    <div>
                                                        <div className="text-[9px] text-muted-foreground uppercase">Tokens</div>
                                                        <div className="text-[10px] font-mono text-muted-foreground">
                                                            {message.metadata.trace.model_info.tokens_in} in / {message.metadata.trace.model_info.tokens_out} out
                                                        </div>
                                                    </div>
                                                    {message.metadata.trace.model_info.cost_estimate_usd !== undefined && (
                                                        <div>
                                                            <div className="text-[9px] text-muted-foreground uppercase">Cost (USD)</div>
                                                            <div className="text-[11px] font-mono text-primary/80">
                                                                ${message.metadata.trace.model_info.cost_estimate_usd.toFixed(6)}
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Confidence Footer */}
                                    {message.metadata?.confidence !== undefined && (
                                        <div className="text-[10px] text-muted-foreground/60 flex items-center justify-end gap-1.5 pt-1">
                                            <span>Confidence Score</span>
                                            <div className="h-1 w-1 rounded-full bg-primary/40" />
                                            <span className="font-mono font-bold text-foreground/70">
                                                {(message.metadata.confidence * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </CollapsibleContent>
                        </Collapsible>
                    )}
                </div>
            </div>
        </motion.div>
    )
}
