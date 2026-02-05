import React from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Heart, BookOpen, Target, TrendingUp, Sparkles, Network } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import api from '@/lib/api';

// ============================================================================
// TYPES
// ============================================================================

interface ContextualSynthesis {
    synthesis: any;
    contextual_guidance: string[];
}

interface GuidancePanelProps {
    className?: string;
}

// ============================================================================
// GUIDANCE SOURCE DETECTION
// ============================================================================

const detectGuidanceSource = (guidance: string): {
    icon: React.ComponentType<any>;
    label: string;
    color: string;
    bgColor: string;
    borderColor: string;
} => {
    const lower = guidance.toLowerCase();
    
    if (lower.includes('mood') || lower.includes('feeling') || lower.includes('emotion')) {
        return {
            icon: Heart,
            label: 'Mood-Based',
            color: 'text-rose-400',
            bgColor: 'bg-rose-500/10',
            borderColor: 'border-rose-500/20',
        };
    }
    
    if (lower.includes('quest') || lower.includes('goal') || lower.includes('active')) {
        return {
            icon: Target,
            label: 'Quest-Aligned',
            color: 'text-amber-400',
            bgColor: 'bg-amber-500/10',
            borderColor: 'border-amber-500/20',
        };
    }
    
    if (lower.includes('last time') || lower.includes('previously') || lower.includes('history') || lower.includes('before')) {
        return {
            icon: BookOpen,
            label: 'Historical Pattern',
            color: 'text-blue-400',
            bgColor: 'bg-blue-500/10',
            borderColor: 'border-blue-500/20',
        };
    }
    
    if (lower.includes('line') || lower.includes('archetype') || lower.includes('opportunist') || lower.includes('investigator')) {
        return {
            icon: Sparkles,
            label: 'Line-Specific',
            color: 'text-purple-400',
            bgColor: 'bg-purple-500/10',
            borderColor: 'border-purple-500/20',
        };
    }
    
    if (lower.includes('shadow') || lower.includes('gift') || lower.includes('transform')) {
        return {
            icon: TrendingUp,
            label: 'Transformation',
            color: 'text-emerald-400',
            bgColor: 'bg-emerald-500/10',
            borderColor: 'border-emerald-500/20',
        };
    }
    
    if (lower.includes('harmonize') || lower.includes('gate') || lower.includes('compatible')) {
        return {
            icon: Network,
            label: 'Gate Harmony',
            color: 'text-indigo-400',
            bgColor: 'bg-indigo-500/10',
            borderColor: 'border-indigo-500/20',
        };
    }
    
    // Default
    return {
        icon: Sparkles,
        label: 'Insight',
        color: 'text-zinc-400',
        bgColor: 'bg-zinc-500/10',
        borderColor: 'border-zinc-500/20',
    };
};

// ============================================================================
// WISDOM CARD
// ============================================================================

interface WisdomCardProps {
    guidance: string;
    index: number;
}

const WisdomCard: React.FC<WisdomCardProps> = ({ guidance, index }) => {
    const source = detectGuidanceSource(guidance);
    const Icon = source.icon;
    
    return (
        <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={cn(
                "relative overflow-hidden rounded-xl p-4 border backdrop-blur-sm group hover:scale-[1.02] transition-transform cursor-default",
                source.bgColor,
                source.borderColor
            )}
        >
            {/* Gradient accent */}
            <div className={cn(
                "absolute top-0 left-0 w-1 h-full",
                source.color.replace('text-', 'bg-')
            )} />
            
            <div className="relative pl-3 space-y-3">
                {/* Source badge */}
                <div className="flex items-center gap-2">
                    <div className={cn(
                        "p-1.5 rounded-lg border",
                        source.bgColor,
                        source.borderColor
                    )}>
                        <Icon className={cn("w-3.5 h-3.5", source.color)} />
                    </div>
                    <Badge
                        variant="outline"
                        className={cn(
                            "text-[10px] font-bold uppercase tracking-wider border px-2 py-0.5",
                            source.color,
                            source.borderColor
                        )}
                    >
                        {source.label}
                    </Badge>
                </div>
                
                {/* Guidance text */}
                <p className="text-sm leading-relaxed text-zinc-200 font-medium">
                    {guidance}
                </p>
                
                {/* Hover indicator */}
                <div className={cn(
                    "h-0.5 w-full rounded-full opacity-0 group-hover:opacity-100 transition-opacity",
                    source.color.replace('text-', 'bg-')
                )} />
            </div>
        </motion.div>
    );
};

// ============================================================================
// GUIDANCE PANEL
// ============================================================================

export const GuidancePanel: React.FC<GuidancePanelProps> = ({ className }) => {
    const { data, isLoading, error } = useQuery<ContextualSynthesis>({
        queryKey: ['council-contextual-synthesis'],
        queryFn: async () => {
            const response = await api.get('/intelligence/council/synthesis/contextual');
            return response.data;
        },
        refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
        staleTime: 2 * 60 * 1000, // Consider stale after 2 minutes
    });
    
    if (isLoading) {
        return (
            <div className={cn("space-y-4", className)}>
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20 animate-pulse">
                        <Sparkles className="w-6 h-6 text-purple-400" />
                    </div>
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                            Contextual Wisdom
                        </p>
                        <h3 className="text-lg font-bold text-foreground">Loading guidance...</h3>
                    </div>
                </div>
                <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="h-24 rounded-xl bg-zinc-800/50 animate-pulse" />
                    ))}
                </div>
            </div>
        );
    }
    
    if (error) {
        return (
            <div className={cn("space-y-4", className)}>
                <div className="rounded-xl p-4 border border-red-500/20 bg-red-500/5">
                    <p className="text-sm text-red-400">
                        Unable to load contextual guidance. Please try again later.
                    </p>
                </div>
            </div>
        );
    }
    
    const guidance = data?.contextual_guidance || [];
    
    if (guidance.length === 0) {
        return (
            <div className={cn("space-y-4", className)}>
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20">
                        <Sparkles className="w-6 h-6 text-purple-400" />
                    </div>
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                            Contextual Wisdom
                        </p>
                        <h3 className="text-lg font-bold text-foreground">No guidance available</h3>
                    </div>
                </div>
                <div className="rounded-xl p-6 border border-zinc-800 bg-zinc-900/50 text-center">
                    <p className="text-sm text-zinc-500">
                        Journal more entries to unlock personalized guidance based on your patterns.
                    </p>
                </div>
            </div>
        );
    }
    
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn("space-y-4", className)}
        >
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20">
                    <Sparkles className="w-6 h-6 text-purple-400" />
                </div>
                <div>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                        Contextual Wisdom
                    </p>
                    <h3 className="text-lg font-bold text-foreground">
                        Personalized Guidance
                    </h3>
                </div>
                <div className="ml-auto">
                    <Badge variant="outline" className="text-[10px] font-mono">
                        {guidance.length} {guidance.length === 1 ? 'insight' : 'insights'}
                    </Badge>
                </div>
            </div>
            
            {/* Description */}
            <p className="text-xs text-zinc-500 leading-relaxed">
                These insights are generated by analyzing your journal patterns, active quests, mood history, 
                and current gate energy. They update as you journal and as the cosmic cycles shift.
            </p>
            
            {/* Wisdom cards */}
            <div className="space-y-3">
                {guidance.map((text, index) => (
                    <WisdomCard key={index} guidance={text} index={index} />
                ))}
            </div>
            
            {/* Footer note */}
            <div className="pt-2 text-center">
                <p className="text-[10px] text-zinc-600 font-medium">
                    💫 Guidance refreshes every 5 minutes
                </p>
            </div>
        </motion.div>
    );
};

export default GuidancePanel;
