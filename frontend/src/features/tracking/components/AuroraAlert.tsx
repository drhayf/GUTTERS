import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
    Sparkles, MapPin, Eye, EyeOff, Compass, Clock, AlertTriangle, 
    ChevronDown, ChevronUp, Navigation
} from "lucide-react";
import { cn } from '@/lib/utils';
import api from '@/lib/api';

interface LocalImpact {
    geographic_location: {
        latitude: number;
        longitude: number;
    };
    geomagnetic_latitude: number;
    intensity_factor: number;
    aurora: {
        status: string;
        probability: number;
        min_kp_required: number;
        alert: boolean;
    };
    local_impact: {
        severity: number;
        severity_label: string;
        effects: string[];
        recommendations: string[];
    };
    sensitivity_note: string | null;
    timestamp: string;
}

interface AuroraGuidance {
    hemisphere: string;
    viewing_direction: string;
    best_time: string;
    tips: string[];
}

interface LocationAwareSolarData {
    global_conditions: {
        kp_index: number;
        kp_status: string;
        bz: number;
        shield_integrity: string;
        solar_wind_speed: number;
    };
    local_impact: LocalImpact;
    aurora_guidance: AuroraGuidance;
    timestamp: string;
    source: string;
}

interface Props {
    latitude?: number;
    longitude?: number;
}

export const AuroraAlert: React.FC<Props> = ({ latitude, longitude }) => {
    const [expanded, setExpanded] = React.useState(false);
    
    const { data, isLoading, error } = useQuery({
        queryKey: ['solar-location-aware', latitude, longitude],
        queryFn: async () => {
            const params = new URLSearchParams();
            if (latitude) params.append('latitude', latitude.toString());
            if (longitude) params.append('longitude', longitude.toString());
            
            const res = await api.get<LocationAwareSolarData>(
                `/api/v1/tracking/solar/location?${params.toString()}`
            );
            return res.data;
        },
        refetchInterval: 300000, // 5 minutes
        enabled: true,
    });

    if (isLoading) {
        return (
            <div className="animate-pulse bg-white/40 rounded-2xl h-32" />
        );
    }

    if (error || !data) {
        return null;
    }

    const aurora = data.local_impact.aurora;
    const impact = data.local_impact.local_impact;
    const guidance = data.aurora_guidance;

    // Don't show if no aurora possibility and low impact
    if (aurora.probability === 0 && impact.severity === 0) {
        return null;
    }

    const getAuroraConfig = (status: string) => {
        const configs: Record<string, { 
            color: string; 
            bg: string; 
            border: string; 
            icon: React.ElementType;
            glow: boolean;
        }> = {
            'VISIBLE': { 
                color: 'text-emerald-400', 
                bg: 'bg-gradient-to-br from-emerald-500/20 via-cyan-500/10 to-violet-500/20', 
                border: 'border-emerald-500/40',
                icon: Sparkles,
                glow: true 
            },
            'POSSIBLE': { 
                color: 'text-cyan-400', 
                bg: 'bg-cyan-500/10', 
                border: 'border-cyan-500/30',
                icon: Eye,
                glow: true 
            },
            'UNLIKELY': { 
                color: 'text-slate-400', 
                bg: 'bg-slate-500/10', 
                border: 'border-slate-500/20',
                icon: EyeOff,
                glow: false 
            },
            'NOT VISIBLE': { 
                color: 'text-slate-500', 
                bg: 'bg-slate-500/5', 
                border: 'border-slate-500/10',
                icon: EyeOff,
                glow: false 
            },
        };
        return configs[status] || configs['NOT VISIBLE'];
    };

    const getSeverityConfig = (severity: number) => {
        const configs: Record<number, { color: string; bg: string; border: string }> = {
            0: { color: 'text-emerald-500', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
            1: { color: 'text-yellow-500', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20' },
            2: { color: 'text-amber-500', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
            3: { color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/20' },
        };
        return configs[severity] || configs[0];
    };

    const auroraConfig = getAuroraConfig(aurora.status);
    const severityConfig = getSeverityConfig(impact.severity);
    const AuroraIcon = auroraConfig.icon;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "relative overflow-hidden rounded-2xl border backdrop-blur-sm",
                auroraConfig.bg, auroraConfig.border
            )}
        >
            {/* Aurora glow effect */}
            {auroraConfig.glow && (
                <motion.div
                    className="absolute inset-0 opacity-50"
                    style={{
                        background: 'radial-gradient(ellipse at top, rgba(34, 197, 94, 0.2), transparent 60%), radial-gradient(ellipse at bottom, rgba(139, 92, 246, 0.15), transparent 60%)'
                    }}
                    animate={{ opacity: [0.3, 0.6, 0.3] }}
                    transition={{ duration: 4, repeat: Infinity }}
                />
            )}

            <div className="relative z-10 p-5">
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className={cn(
                            "p-2.5 rounded-xl border",
                            auroraConfig.bg, auroraConfig.border
                        )}>
                            <AuroraIcon className={cn(
                                "w-6 h-6",
                                auroraConfig.color,
                                auroraConfig.glow && "animate-pulse"
                            )} />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                                Location Impact
                            </p>
                            <h3 className={cn("text-xl font-black", auroraConfig.color)}>
                                Aurora: {aurora.status}
                            </h3>
                        </div>
                    </div>

                    {aurora.probability > 0 && (
                        <div className="text-right">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                                Probability
                            </p>
                            <span className={cn("text-2xl font-mono-data font-black", auroraConfig.color)}>
                                {Math.round(aurora.probability * 100)}%
                            </span>
                        </div>
                    )}
                </div>

                {/* Quick Stats Row */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                    <div className="glass rounded-xl p-3 border border-white/10">
                        <div className="flex items-center gap-2 mb-1">
                            <MapPin className="w-3 h-3 text-muted-foreground" />
                            <span className="text-[9px] font-bold uppercase tracking-widest text-muted-foreground">
                                Geomag Lat
                            </span>
                        </div>
                        <span className="text-lg font-mono-data font-bold">
                            {data.local_impact.geomagnetic_latitude.toFixed(1)}°
                        </span>
                    </div>
                    
                    <div className="glass rounded-xl p-3 border border-white/10">
                        <div className="flex items-center gap-2 mb-1">
                            <Compass className="w-3 h-3 text-muted-foreground" />
                            <span className="text-[9px] font-bold uppercase tracking-widest text-muted-foreground">
                                Min Kp
                            </span>
                        </div>
                        <span className="text-lg font-mono-data font-bold">
                            {aurora.min_kp_required > 9 ? '9+' : aurora.min_kp_required}
                        </span>
                    </div>
                    
                    <div className={cn(
                        "rounded-xl p-3 border",
                        severityConfig.bg, severityConfig.border
                    )}>
                        <div className="flex items-center gap-2 mb-1">
                            <AlertTriangle className={cn("w-3 h-3", severityConfig.color)} />
                            <span className="text-[9px] font-bold uppercase tracking-widest text-muted-foreground">
                                Impact
                            </span>
                        </div>
                        <span className={cn("text-sm font-bold", severityConfig.color)}>
                            {impact.severity_label}
                        </span>
                    </div>
                </div>

                {/* Aurora Viewing Guidance */}
                {aurora.probability > 0 && (
                    <div className="mb-4 p-3 rounded-xl bg-white/5 border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                            <Navigation className="w-4 h-4 text-cyan-400" />
                            <span className="text-sm font-bold text-foreground">
                                {guidance.viewing_direction}
                            </span>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                <span>{guidance.best_time}</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <Sparkles className="w-3 h-3" />
                                <span>{guidance.hemisphere} Hemisphere</span>
                            </div>
                        </div>
                    </div>
                )}

                {/* Expandable Details */}
                {(impact.effects.length > 0 || impact.recommendations.length > 0) && (
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="w-full flex items-center justify-between py-2 px-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                    >
                        <span className="font-medium">
                            {expanded ? 'Hide' : 'Show'} Effects & Recommendations
                        </span>
                        {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                )}

                <AnimatePresence>
                    {expanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                        >
                            <div className="space-y-4 pt-3 border-t border-border/30">
                                {/* Effects */}
                                {impact.effects.length > 0 && (
                                    <div>
                                        <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">
                                            Potential Effects
                                        </h4>
                                        <ul className="space-y-1.5">
                                            {impact.effects.map((effect, i) => (
                                                <li key={i} className="flex items-start gap-2 text-xs text-foreground/80">
                                                    <span className="text-amber-400 mt-0.5">•</span>
                                                    {effect}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Recommendations */}
                                {impact.recommendations.length > 0 && (
                                    <div>
                                        <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">
                                            Recommendations
                                        </h4>
                                        <ul className="space-y-1.5">
                                            {impact.recommendations.map((rec, i) => (
                                                <li key={i} className="flex items-start gap-2 text-xs text-foreground/80">
                                                    <span className="text-emerald-400 mt-0.5">✓</span>
                                                    {rec}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Aurora Tips */}
                                {aurora.probability > 0 && guidance.tips.length > 0 && (
                                    <div className="p-3 rounded-xl bg-gradient-to-r from-cyan-500/10 to-violet-500/10 border border-cyan-500/20">
                                        <h4 className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-2">
                                            Aurora Viewing Tips
                                        </h4>
                                        <ul className="space-y-1.5">
                                            {guidance.tips.map((tip, i) => (
                                                <li key={i} className="flex items-start gap-2 text-xs text-foreground/80">
                                                    <Sparkles className="w-3 h-3 text-cyan-400 mt-0.5 shrink-0" />
                                                    {tip}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Sensitivity Note */}
                                {data.local_impact.sensitivity_note && (
                                    <p className="text-[11px] text-muted-foreground/80 italic border-l-2 border-primary/30 pl-3">
                                        {data.local_impact.sensitivity_note}
                                    </p>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
};

export default AuroraAlert;
