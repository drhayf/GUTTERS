import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { MapPin, Timer, Gauge, Sparkles, AlertTriangle } from "lucide-react";
import { cn } from '@/lib/utils';
import api from '@/lib/api';

interface LunarData {
    phase_angle: number;
    illumination: number;
    phase_name: string;
    sign: string;
    longitude: number;
    distance_km: number;
    supermoon_score: number;
    is_voc: boolean;
    time_until_voc_minutes: number | null;
    next_ingress: string | null;
    is_new_moon: boolean;
    is_full_moon: boolean;
}

export const LunarObservatory = () => {
    const { data: lunarData, isLoading, error } = useQuery({
        queryKey: ['tracking-lunar'],
        queryFn: async () => {
            const res = await api.get<{ current_data: LunarData }>('/api/v1/tracking/lunar');
            console.log('[LunarObservatory] API Response:', res.data);
            return res.data.current_data;
        },
        refetchInterval: 60000, // 1 minute for more live feel
        retry: 3,
        retryDelay: 1000
    });

    // Debug logging
    if (error) {
        console.error('[LunarObservatory] Query error:', error);
    }

    // Pre-generate star positions to avoid impure function calls during render
    // Must be before any conditional returns to follow React hooks rules
    const stars = useMemo(() => 
        [...Array(30)].map((_, i) => ({
            id: i,
            left: (i * 17 + 3) % 100,
            top: (i * 23 + 7) % 100,
            duration: 2 + (i % 5) * 0.5,
            delay: (i % 7) * 0.3,
        })), 
    []);

    if (isLoading || !lunarData) {
        return (
            <div className="space-y-4">
                {[1, 2].map(i => (
                    <div key={i} className="h-40 animate-pulse bg-white/40 rounded-2xl" />
                ))}
                {error && (
                    <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                        Failed to load lunar data. Retrying...
                    </div>
                )}
            </div>
        );
    }

    const illumination = Math.round((lunarData.illumination ?? 0) * 100);
    const distance = Math.round(lunarData.distance_km ?? 0);
    const supermoonPercent = Math.round((lunarData.supermoon_score ?? 0) * 100);
    
    const formatVocTime = (minutes: number | null) => {
        if (!minutes) return 'N/A';
        const h = Math.floor(minutes / 60);
        const m = minutes % 60;
        return `${h}h ${m}m`;
    };

    // Moon phase visual - calculate shadow position
    const phaseVisual = lunarData.phase_angle ?? 0;
    const shadowDirection = phaseVisual > 180 ? 'left' : 'right';
    const shadowPercent = Math.abs(((phaseVisual % 180) / 180) * 100);

    return (
        <div className="space-y-4">
            {/* MOON VISUALIZER - Hero Card */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative overflow-hidden rounded-2xl p-6 bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 border border-indigo-500/20"
            >
                {/* Starfield Background */}
                <div className="absolute inset-0 overflow-hidden">
                    {stars.map((star) => (
                        <motion.div
                            key={star.id}
                            className="absolute w-0.5 h-0.5 rounded-full bg-white/40"
                            style={{
                                left: `${star.left}%`,
                                top: `${star.top}%`,
                            }}
                            animate={{ opacity: [0.2, 0.8, 0.2] }}
                            transition={{
                                duration: star.duration,
                                repeat: Infinity,
                                delay: star.delay,
                            }}
                        />
                    ))}
                </div>

                <div className="flex items-center gap-8 relative z-10">
                    {/* Moon Circle */}
                    <div className="relative">
                        {/* Glow Effect */}
                        <div className="absolute inset-0 rounded-full bg-slate-200/20 blur-xl scale-125" />
                        
                        {/* Moon Body */}
                        <div className="relative w-32 h-32 rounded-full bg-gradient-to-br from-slate-100 via-slate-200 to-slate-300 shadow-[0_0_60px_rgba(255,255,255,0.2)] overflow-hidden">
                            {/* Phase Shadow Overlay */}
                            <motion.div
                                className="absolute inset-0 bg-slate-900/90"
                                initial={false}
                                animate={{
                                    clipPath: shadowDirection === 'right' 
                                        ? `inset(0 0 0 ${100 - shadowPercent}%)`
                                        : `inset(0 ${100 - shadowPercent}% 0 0)`
                                }}
                                transition={{ duration: 1 }}
                            />
                            
                            {/* Crater texture hints */}
                            <div className="absolute top-1/4 left-1/4 w-4 h-4 rounded-full bg-slate-300/30" />
                            <div className="absolute top-1/2 right-1/3 w-6 h-6 rounded-full bg-slate-400/20" />
                            <div className="absolute bottom-1/4 left-1/2 w-3 h-3 rounded-full bg-slate-300/20" />
                        </div>
                    </div>

                    {/* Moon Info */}
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                            {(lunarData.is_new_moon || lunarData.is_full_moon) && (
                                <span className="px-2 py-0.5 rounded-full bg-indigo-500/30 text-indigo-300 text-[10px] font-bold uppercase tracking-widest animate-pulse">
                                    {lunarData.is_new_moon ? 'New Moon' : 'Full Moon'}
                                </span>
                            )}
                        </div>
                        <h2 className="text-3xl font-black text-white tracking-tight">
                            {lunarData.phase_name}
                        </h2>
                        <p className="text-indigo-300/80 font-mono-data text-lg mt-1">
                            {illumination}% Illuminated
                        </p>

                        {/* Sign Badge */}
                        <div className="flex items-center gap-2 mt-4">
                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/10">
                                <MapPin className="w-3.5 h-3.5 text-indigo-400" />
                                <span className="text-white font-medium">{lunarData.sign}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </motion.div>

            {/* VOID OF COURSE ALERT */}
            {lunarData.is_voc && (
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="rounded-2xl p-4 bg-amber-500/10 border border-amber-500/30 flex items-center gap-4"
                >
                    <div className="p-3 rounded-xl bg-amber-500/20">
                        <AlertTriangle className="w-6 h-6 text-amber-500 animate-pulse" />
                    </div>
                    <div className="flex-1">
                        <h3 className="text-sm font-bold text-amber-600">Void of Course Active</h3>
                        <p className="text-xs text-amber-600/80">
                            Avoid starting new projects. Use this time for reflection and completion.
                        </p>
                    </div>
                </motion.div>
            )}

            {/* METRICS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* VoC Timer */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className={cn(
                        "rounded-2xl p-5 border backdrop-blur-sm",
                        lunarData.is_voc 
                            ? "bg-amber-500/10 border-amber-500/20" 
                            : "glass border-white/20"
                    )}
                >
                    <div className="flex items-center gap-2 mb-3">
                        <div className={cn(
                            "p-2 rounded-lg",
                            lunarData.is_voc ? "bg-amber-500/20" : "bg-indigo-500/10"
                        )}>
                            <Timer className={cn(
                                "w-5 h-5",
                                lunarData.is_voc ? "text-amber-500" : "text-indigo-500"
                            )} />
                        </div>
                        <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                            Void of Course
                        </span>
                    </div>
                    
                    {lunarData.is_voc ? (
                        <div>
                            <span className="text-2xl font-black text-amber-500">ACTIVE</span>
                            <p className="text-[10px] text-muted-foreground mt-1">
                                Ends at next sign ingress
                            </p>
                        </div>
                    ) : (
                        <div>
                            <span className="text-2xl font-mono-data font-black text-foreground">
                                {formatVocTime(lunarData.time_until_voc_minutes)}
                            </span>
                            <p className="text-[10px] text-muted-foreground mt-1">
                                Until next window
                            </p>
                        </div>
                    )}
                </motion.div>

                {/* Distance / Proximity */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="glass rounded-2xl p-5 border border-white/20"
                >
                    <div className="flex items-center gap-2 mb-3">
                        <div className="p-2 rounded-lg bg-cyan-500/10">
                            <Gauge className="w-5 h-5 text-cyan-500" />
                        </div>
                        <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                            Distance
                        </span>
                    </div>
                    
                    <span className="text-2xl font-mono-data font-black text-foreground">
                        {distance.toLocaleString()}
                    </span>
                    <span className="text-sm text-muted-foreground ml-1">km</span>

                    {/* Supermoon Indicator */}
                    <div className="mt-3">
                        <div className="flex items-center justify-between text-[10px] text-muted-foreground mb-1">
                            <span>Supermoon Factor</span>
                            <span>{supermoonPercent}%</span>
                        </div>
                        <div className="h-1.5 bg-muted/30 rounded-full overflow-hidden">
                            <motion.div
                                className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 rounded-full"
                                initial={{ width: 0 }}
                                animate={{ width: `${supermoonPercent}%` }}
                                transition={{ duration: 1, delay: 0.5 }}
                            />
                        </div>
                    </div>
                </motion.div>

                {/* Insight Card */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="rounded-2xl p-5 bg-gradient-to-br from-indigo-500/10 to-violet-500/10 border border-indigo-500/20"
                >
                    <div className="flex items-center gap-2 mb-3">
                        <div className="p-2 rounded-lg bg-indigo-500/20">
                            <Sparkles className="w-5 h-5 text-indigo-500" />
                        </div>
                        <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                            Observer Insight
                        </span>
                    </div>
                    
                    <p className="text-sm text-foreground/80 leading-relaxed italic">
                        "The Moon in {lunarData.sign} influences collective emotional frequency. 
                        {lunarData.is_voc 
                            ? ' The Void is active—use this time for internal reflection rather than new external initiatives.' 
                            : ' Lunar energy is stable. Optimal for execution and alignment.'}
                        "
                    </p>
                </motion.div>
            </div>

            {/* ADDITIONAL METRICS */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="grid grid-cols-2 md:grid-cols-4 gap-3"
            >
                <SmallMetric label="Phase Angle" value={`${Math.round(lunarData.phase_angle ?? 0)}°`} />
                <SmallMetric label="Longitude" value={`${(lunarData.longitude ?? 0).toFixed(1)}°`} />
                <SmallMetric label="Sign Position" value={`${((lunarData.longitude ?? 0) % 30).toFixed(1)}°`} />
                <SmallMetric 
                    label="Next Ingress" 
                    value={lunarData.next_ingress 
                        ? new Date(lunarData.next_ingress).toLocaleDateString([], { month: 'short', day: 'numeric' })
                        : 'N/A'
                    } 
                />
            </motion.div>
        </div>
    );
};

const SmallMetric = ({ label, value }: { label: string; value: string }) => (
    <div className="glass rounded-xl p-3 border border-white/20">
        <p className="text-[9px] font-bold uppercase tracking-widest text-muted-foreground mb-1">{label}</p>
        <span className="text-lg font-mono-data font-bold text-foreground">{value}</span>
    </div>
);
