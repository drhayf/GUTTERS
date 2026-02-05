import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
    Sun, Moon, Orbit, Sparkles,
    ChevronDown, ChevronUp, Activity, RefreshCcw
} from "lucide-react";
import { cn } from '@/lib/utils';
import api from '@/lib/api';

interface CosmicContextData {
    timestamp: string;
    user_id: number;
    solar: {
        kp_index: number;
        kp_status: string;
        geomagnetic_storm: boolean;
        bz: number;
        shield_integrity: string;
    };
    lunar: {
        phase_name: string;
        sign: string;
        is_voc: boolean;
        is_full_moon: boolean;
        is_new_moon: boolean;
        illumination: number;
    };
    transits: {
        retrogrades: string[];
        retrograde_count: number;
        exact_aspects: Array<{
            transit: string;
            natal: string;
            aspect: string;
            orb: number;
        }>;
    };
    tags: string[];
    intensity_score: number;
}

interface Props {
    compact?: boolean;
    className?: string;
}

export const CosmicContextWidget: React.FC<Props> = ({ compact = false, className }) => {
    const [expanded, setExpanded] = React.useState(false);

    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ['cosmic-context'],
        queryFn: async () => {
            const res = await api.get<CosmicContextData>('/api/v1/insights/cosmic-context');
            return res.data;
        },
        refetchInterval: 300000, // 5 minutes
        staleTime: 60000, // 1 minute
    });

    if (isLoading) {
        return (
            <div className={cn(
                "animate-pulse rounded-xl border border-border/50 p-3",
                compact ? "h-12" : "h-24",
                className
            )} />
        );
    }

    if (error || !data) {
        return null;
    }

    const getIntensityConfig = (score: number) => {
        if (score >= 7) return { color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'High' };
        if (score >= 4) return { color: 'text-amber-500', bg: 'bg-amber-500/10', border: 'border-amber-500/30', label: 'Moderate' };
        return { color: 'text-emerald-500', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', label: 'Calm' };
    };

    const intensityConfig = getIntensityConfig(data.intensity_score);

    if (compact) {
        return (
            <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-xl border backdrop-blur-sm",
                    intensityConfig.bg, intensityConfig.border,
                    className
                )}
            >
                <Activity className={cn("w-4 h-4", intensityConfig.color)} />
                <div className="flex items-center gap-2 text-xs">
                    <span className={cn("font-bold", intensityConfig.color)}>
                        {data.intensity_score.toFixed(1)}/10
                    </span>
                    <span className="text-muted-foreground">|</span>
                    <span className="text-muted-foreground">
                        {data.lunar.phase_name} in {data.lunar.sign}
                    </span>
                    {data.lunar.is_voc && (
                        <span className="text-amber-500 font-medium">VoC</span>
                    )}
                    {data.transits.retrograde_count > 0 && (
                        <span className="text-muted-foreground">
                            {data.transits.retrograde_count}Rx
                        </span>
                    )}
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "rounded-2xl border backdrop-blur-sm overflow-hidden",
                intensityConfig.bg, intensityConfig.border,
                className
            )}
        >
            {/* Header */}
            <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                        <div className={cn(
                            "p-2 rounded-lg border",
                            intensityConfig.bg, intensityConfig.border
                        )}>
                            <Sparkles className={cn("w-4 h-4", intensityConfig.color)} />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                                Cosmic Context
                            </p>
                            <div className="flex items-center gap-2">
                                <span className={cn("text-lg font-bold", intensityConfig.color)}>
                                    {intensityConfig.label}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                    ({data.intensity_score.toFixed(1)}/10)
                                </span>
                            </div>
                        </div>
                    </div>
                    <button
                        onClick={() => refetch()}
                        className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                        aria-label="Refresh"
                    >
                        <RefreshCcw className="w-4 h-4 text-muted-foreground" />
                    </button>
                </div>

                {/* Quick Status Row */}
                <div className="grid grid-cols-3 gap-2">
                    {/* Solar */}
                    <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10">
                        <Sun className="w-3.5 h-3.5 text-amber-500" />
                        <div className="text-xs">
                            <span className="font-medium">Kp {data.solar.kp_index}</span>
                        </div>
                    </div>

                    {/* Lunar */}
                    <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10">
                        <Moon className="w-3.5 h-3.5 text-slate-400" />
                        <div className="text-xs truncate">
                            <span className="font-medium">{data.lunar.sign}</span>
                            {data.lunar.is_voc && <span className="text-amber-500 ml-1">VoC</span>}
                        </div>
                    </div>

                    {/* Transits */}
                    <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-white/5 border border-white/10">
                        <Orbit className="w-3.5 h-3.5 text-violet-500" />
                        <div className="text-xs">
                            <span className="font-medium">{data.transits.retrograde_count}Rx</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Expandable Details */}
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-center gap-1 py-2 px-4 text-xs text-muted-foreground hover:text-foreground transition-colors border-t border-white/10 bg-white/5"
            >
                {expanded ? 'Less' : 'More'} Details
                {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="p-4 pt-0 space-y-4">
                            {/* Solar Details */}
                            <div>
                                <h4 className="text-[10px] font-bold uppercase tracking-widest text-amber-500/80 mb-2 flex items-center gap-1">
                                    <Sun className="w-3 h-3" /> Solar Conditions
                                </h4>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div className="flex justify-between">
                                        <span className="text-muted-foreground">Status</span>
                                        <span className="font-medium">{data.solar.kp_status}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-muted-foreground">Shield</span>
                                        <span className="font-medium">{data.solar.shield_integrity}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-muted-foreground">Bz</span>
                                        <span className={cn(
                                            "font-medium",
                                            (data.solar.bz ?? 0) < -5 ? "text-red-400" : 
                                            (data.solar.bz ?? 0) < 0 ? "text-amber-400" : "text-emerald-400"
                                        )}>
                                            {(data.solar.bz ?? 0).toFixed(1)} nT
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Lunar Details */}
                            <div>
                                <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-400/80 mb-2 flex items-center gap-1">
                                    <Moon className="w-3 h-3" /> Lunar Position
                                </h4>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <div className="flex justify-between">
                                        <span className="text-muted-foreground">Phase</span>
                                        <span className="font-medium">{data.lunar.phase_name}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-muted-foreground">Sign</span>
                                        <span className="font-medium">{data.lunar.sign}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-muted-foreground">Illumination</span>
                                        <span className="font-medium">
                                            {Math.round(data.lunar.illumination * 100)}%
                                        </span>
                                    </div>
                                    {data.lunar.is_voc && (
                                        <div className="flex justify-between col-span-2">
                                            <span className="text-amber-500">⚠️ Void of Course</span>
                                            <span className="text-amber-500 font-medium">Active</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Transit Details */}
                            {(data.transits.retrogrades.length > 0 || data.transits.exact_aspects.length > 0) && (
                                <div>
                                    <h4 className="text-[10px] font-bold uppercase tracking-widest text-violet-400/80 mb-2 flex items-center gap-1">
                                        <Orbit className="w-3 h-3" /> Active Transits
                                    </h4>
                                    
                                    {data.transits.retrogrades.length > 0 && (
                                        <div className="flex flex-wrap gap-1 mb-2">
                                            {data.transits.retrogrades.map(planet => (
                                                <span 
                                                    key={planet}
                                                    className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-orange-500/20 text-orange-500"
                                                >
                                                    {planet} Rx
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    {data.transits.exact_aspects.slice(0, 2).map((aspect, i) => (
                                        <div key={i} className="text-xs text-muted-foreground">
                                            {aspect.transit} {aspect.aspect} natal {aspect.natal}
                                            <span className="text-[10px] ml-1">({aspect.orb?.toFixed(1)}° orb)</span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Cosmic Tags */}
                            {data.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1 pt-2 border-t border-white/10">
                                    {data.tags.slice(0, 6).map(tag => (
                                        <span 
                                            key={tag}
                                            className="text-[9px] font-medium px-1.5 py-0.5 rounded bg-white/10 text-muted-foreground"
                                        >
                                            #{tag.replace(/_/g, '-')}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default CosmicContextWidget;
