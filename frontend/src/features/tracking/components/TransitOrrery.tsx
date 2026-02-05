import React from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Orbit, RotateCcw, ArrowRight, Zap, ChevronRight, Target } from "lucide-react";
import { cn } from '@/lib/utils';
import api from '@/lib/api';

interface PlanetPosition {
    longitude: number;
    sign: string;
    degree: number;
    speed: number;
    is_retrograde: boolean;
    current_house?: number;
}

interface Transit {
    transit_planet: string;
    natal_planet: string;
    aspect: string;
    orb: number;
    exact: boolean;
    interpretation?: string;
    applying: boolean;
}

interface TransitData {
    positions: Record<string, PlanetPosition>;
}

interface TransitComparison {
    total_transits: number;
    exact_transits: Transit[];
    applying_transits: Transit[];
    current_positions: Record<string, PlanetPosition>;
}

interface TrackingResult {
    module: string;
    current_data: { data: TransitData };
    comparison: TransitComparison;
    significant_events: string[];
    updated_at: string;
}

// Planet symbols and colors
const planetConfig: Record<string, { symbol: string; color: string; bgColor: string }> = {
    'Sun': { symbol: '☉', color: 'text-amber-500', bgColor: 'bg-amber-500/10' },
    'Moon': { symbol: '☽', color: 'text-slate-400', bgColor: 'bg-slate-400/10' },
    'Mercury': { symbol: '☿', color: 'text-cyan-500', bgColor: 'bg-cyan-500/10' },
    'Venus': { symbol: '♀', color: 'text-pink-500', bgColor: 'bg-pink-500/10' },
    'Mars': { symbol: '♂', color: 'text-red-500', bgColor: 'bg-red-500/10' },
    'Jupiter': { symbol: '♃', color: 'text-orange-500', bgColor: 'bg-orange-500/10' },
    'Saturn': { symbol: '♄', color: 'text-stone-500', bgColor: 'bg-stone-500/10' },
    'Uranus': { symbol: '♅', color: 'text-sky-500', bgColor: 'bg-sky-500/10' },
    'Neptune': { symbol: '♆', color: 'text-indigo-500', bgColor: 'bg-indigo-500/10' },
    'Pluto': { symbol: '♇', color: 'text-violet-500', bgColor: 'bg-violet-500/10' },
};

// Aspect colors and symbols
const aspectConfig: Record<string, { symbol: string; color: string; bg: string }> = {
    'conjunction': { symbol: '☌', color: 'text-amber-500', bg: 'bg-amber-500/10' },
    'opposition': { symbol: '☍', color: 'text-red-500', bg: 'bg-red-500/10' },
    'square': { symbol: '□', color: 'text-orange-500', bg: 'bg-orange-500/10' },
    'trine': { symbol: '△', color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
    'sextile': { symbol: '⚹', color: 'text-cyan-500', bg: 'bg-cyan-500/10' },
};

export const TransitOrrery = () => {
    const { data: trackingResult, isLoading } = useQuery({
        queryKey: ['tracking-transits'],
        queryFn: async () => {
            const res = await api.get<TrackingResult>('/api/v1/tracking/transits');
            return res.data;
        },
        refetchInterval: 300000 // 5 minutes
    });

    if (isLoading || !trackingResult) {
        return (
            <div className="space-y-4">
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-20 animate-pulse bg-white/40 rounded-2xl" />
                ))}
            </div>
        );
    }

    // Extract positions from current_data (may be nested in 'data' from TrackingData)
    const rawPositions = trackingResult.current_data?.data?.positions || 
                         (trackingResult.current_data as unknown as TransitData)?.positions || {};
    
    const planets = Object.entries(rawPositions).map(([name, data]) => ({
        name,
        ...data,
        config: planetConfig[name] || { symbol: '●', color: 'text-primary', bgColor: 'bg-primary/10' }
    }));

    // Extract aspects from comparison
    const comparison = trackingResult.comparison || {};
    const exactTransits = comparison.exact_transits || [];
    const applyingTransits = comparison.applying_transits || [];
    const totalAspects = comparison.total_transits || 0;

    const retrogradeCount = planets.filter(p => p.is_retrograde).length;
    const retrogradePlanets = planets.filter(p => p.is_retrograde);

    // Determine stationing planets (very slow speed near 0)
    const stationingPlanets = planets.filter(p => 
        p.name !== 'Sun' && p.name !== 'Moon' && Math.abs(p.speed) < 0.02
    );

    return (
        <div className="space-y-4">
            {/* RETROGRADE ALERT */}
            {retrogradeCount > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-2xl p-5 bg-gradient-to-br from-orange-500/10 to-red-500/10 border border-orange-500/20"
                >
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-orange-500/20 border border-orange-500/30">
                                <RotateCcw className="w-6 h-6 text-orange-500 animate-[spin_3s_linear_infinite_reverse]" />
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-foreground">
                                    {retrogradeCount} Planet{retrogradeCount > 1 ? 's' : ''} Retrograde
                                </h2>
                                <p className="text-sm text-muted-foreground">
                                    {retrogradePlanets.map(p => p.name).join(', ')}
                                </p>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            {retrogradePlanets.map(planet => (
                                <div
                                    key={planet.name}
                                    className={cn(
                                        "w-10 h-10 rounded-full flex items-center justify-center text-xl border",
                                        planet.config.bgColor,
                                        `border-${planet.config.color.replace('text-', '')}/30`
                                    )}
                                >
                                    <span className={planet.config.color}>{planet.config.symbol}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </motion.div>
            )}

            {/* STATIONING ALERT */}
            {stationingPlanets.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="rounded-2xl p-4 bg-red-500/10 border border-red-500/20 flex items-center gap-4"
                >
                    <div className="p-2.5 rounded-xl bg-red-500/20">
                        <Zap className="w-5 h-5 text-red-500 animate-pulse" />
                    </div>
                    <div className="flex-1">
                        <h3 className="text-sm font-bold text-red-600">Stationing Detected</h3>
                        <p className="text-xs text-red-600/80">
                            {stationingPlanets.map(p => p.name).join(', ')} near station point - maximum intensity
                        </p>
                    </div>
                </motion.div>
            )}

            {/* ACTIVE ASPECTS - Transit to Natal */}
            {(exactTransits.length > 0 || applyingTransits.length > 0) && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15 }}
                    className="glass rounded-2xl border border-white/20 overflow-hidden"
                >
                    <div className="p-4 border-b border-border/30">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-amber-500/10">
                                    <Target className="w-5 h-5 text-amber-500" />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold">Active Natal Aspects</h2>
                                    <p className="text-[10px] text-muted-foreground">Transits activating your birth chart</p>
                                </div>
                            </div>
                            <span className="text-[10px] font-mono-data px-2 py-1 rounded bg-amber-500/10 text-amber-600">
                                {totalAspects} ACTIVE
                            </span>
                        </div>
                    </div>

                    <div className="divide-y divide-border/20">
                        {/* Exact Transits First */}
                        {exactTransits.slice(0, 3).map((transit, index) => {
                            const aspectStyle = aspectConfig[transit.aspect] || aspectConfig['conjunction'];
                            const transitPlanetConfig = planetConfig[transit.transit_planet] || planetConfig['Sun'];
                            const natalPlanetConfig = planetConfig[transit.natal_planet] || planetConfig['Sun'];

                            return (
                                <motion.div
                                    key={`exact-${index}`}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.05 * index }}
                                    className="p-4 hover:bg-white/30 transition-colors"
                                >
                                    <div className="flex items-center gap-3">
                                        {/* Transit Planet */}
                                        <div className={cn(
                                            "w-10 h-10 rounded-lg flex items-center justify-center text-xl border",
                                            transitPlanetConfig.bgColor
                                        )}>
                                            <span className={transitPlanetConfig.color}>{transitPlanetConfig.symbol}</span>
                                        </div>

                                        {/* Aspect Symbol */}
                                        <div className={cn(
                                            "w-8 h-8 rounded-full flex items-center justify-center text-lg font-bold",
                                            aspectStyle.bg
                                        )}>
                                            <span className={aspectStyle.color}>{aspectStyle.symbol}</span>
                                        </div>

                                        {/* Natal Planet */}
                                        <div className={cn(
                                            "w-10 h-10 rounded-lg flex items-center justify-center text-xl border border-dashed",
                                            natalPlanetConfig.bgColor
                                        )}>
                                            <span className={natalPlanetConfig.color}>{natalPlanetConfig.symbol}</span>
                                        </div>

                                        {/* Info */}
                                        <div className="flex-1 min-w-0 ml-2">
                                            <div className="flex items-center gap-2">
                                                <span className="text-sm font-bold">
                                                    {transit.transit_planet} {transit.aspect} Natal {transit.natal_planet}
                                                </span>
                                                {transit.exact && (
                                                    <span className="text-[8px] font-bold uppercase px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-600 animate-pulse">
                                                        EXACT
                                                    </span>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                                                <span>Orb: {transit.orb.toFixed(1)}°</span>
                                                <span>•</span>
                                                <span className={transit.applying ? "text-emerald-500" : "text-amber-500"}>
                                                    {transit.applying ? "Applying" : "Separating"}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    {transit.interpretation && (
                                        <p className="text-xs text-muted-foreground/80 mt-2 ml-1 italic">
                                            "{transit.interpretation}"
                                        </p>
                                    )}
                                </motion.div>
                            );
                        })}

                        {/* Show remaining applying transits */}
                        {applyingTransits.filter(t => !t.exact).slice(0, 2).map((transit, index) => {
                            const aspectStyle = aspectConfig[transit.aspect] || aspectConfig['conjunction'];
                            
                            return (
                                <div
                                    key={`applying-${index}`}
                                    className="p-3 px-4 flex items-center gap-3 text-muted-foreground/80"
                                >
                                    <span className={cn("text-lg", aspectStyle.color)}>{aspectStyle.symbol}</span>
                                    <span className="text-xs">
                                        {transit.transit_planet} approaching {transit.aspect} to natal {transit.natal_planet}
                                    </span>
                                    <span className="text-[10px] font-mono-data ml-auto">{transit.orb.toFixed(1)}° orb</span>
                                </div>
                            );
                        })}
                    </div>
                </motion.div>
            )}

            {/* PLANETARY POSITIONS */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="glass rounded-2xl border border-white/20 overflow-hidden"
            >
                <div className="p-4 border-b border-border/30">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-violet-500/10">
                                <Orbit className="w-5 h-5 text-violet-500" />
                            </div>
                            <h2 className="text-lg font-bold">Current Planetary Positions</h2>
                        </div>
                        <span className="text-[10px] font-mono-data text-muted-foreground px-2 py-1 rounded bg-muted/50">
                            LIVE
                        </span>
                    </div>
                </div>

                <div className="divide-y divide-border/20">
                    {planets.map((planet, index) => (
                        <motion.div
                            key={planet.name}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.05 * index }}
                            className="flex items-center gap-4 p-4 hover:bg-white/30 transition-colors group"
                        >
                            {/* Planet Symbol */}
                            <div className={cn(
                                "w-12 h-12 rounded-xl flex items-center justify-center text-2xl border",
                                planet.config.bgColor,
                                `border-transparent group-hover:border-${planet.config.color.replace('text-', '')}/30`
                            )}>
                                <span className={planet.config.color}>{planet.config.symbol}</span>
                            </div>

                            {/* Planet Info */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                    <h3 className="text-base font-bold text-foreground">{planet.name}</h3>
                                    {planet.is_retrograde && (
                                        <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-orange-500/20 text-orange-600 flex items-center gap-1">
                                            <RotateCcw className="w-2.5 h-2.5" />
                                            Rx
                                        </span>
                                    )}
                                    {Math.abs(planet.speed) < 0.02 && planet.name !== 'Sun' && planet.name !== 'Moon' && (
                                        <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-red-500/20 text-red-600">
                                            Station
                                        </span>
                                    )}
                                </div>
                                <div className="flex items-center gap-2 mt-0.5">
                                    <span className="text-sm text-muted-foreground">
                                        <span className="font-medium text-foreground">{planet.sign}</span>
                                        {' '}
                                        <span className="font-mono-data">{planet.degree.toFixed(1)}°</span>
                                    </span>
                                </div>
                            </div>

                            {/* Motion Indicator */}
                            <div className="flex items-center gap-3">
                                {planet.current_house && (
                                    <span className="text-[10px] font-bold uppercase px-2 py-1 rounded bg-muted/50 text-muted-foreground">
                                        H{planet.current_house}
                                    </span>
                                )}
                                <div className={cn(
                                    "flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase",
                                    planet.is_retrograde 
                                        ? "bg-orange-500/10 text-orange-500"
                                        : "bg-emerald-500/10 text-emerald-500"
                                )}>
                                    {planet.is_retrograde ? (
                                        <>
                                            <RotateCcw className="w-3 h-3" />
                                            <span>Retrograde</span>
                                        </>
                                    ) : (
                                        <>
                                            <ArrowRight className="w-3 h-3" />
                                            <span>Direct</span>
                                        </>
                                    )}
                                </div>
                            </div>

                            {/* Hover Chevron */}
                            <ChevronRight className="w-4 h-4 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                        </motion.div>
                    ))}
                </div>
            </motion.div>

            {/* SPEED LEGEND */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="grid grid-cols-3 gap-3"
            >
                <LegendCard 
                    icon={<ArrowRight className="w-4 h-4 text-emerald-500" />}
                    label="Direct Motion"
                    description="Moving forward through zodiac"
                    color="emerald"
                />
                <LegendCard 
                    icon={<RotateCcw className="w-4 h-4 text-orange-500" />}
                    label="Retrograde"
                    description="Apparent backward motion"
                    color="orange"
                />
                <LegendCard 
                    icon={<Zap className="w-4 h-4 text-red-500" />}
                    label="Station"
                    description="Near-zero motion - peak intensity"
                    color="red"
                />
            </motion.div>
        </div>
    );
};

const LegendCard = ({ 
    icon, 
    label, 
    description, 
    color 
}: { 
    icon: React.ReactNode; 
    label: string; 
    description: string;
    color: 'emerald' | 'orange' | 'red'
}) => {
    const bgColors = {
        emerald: 'bg-emerald-500/10 border-emerald-500/20',
        orange: 'bg-orange-500/10 border-orange-500/20',
        red: 'bg-red-500/10 border-red-500/20',
    };

    return (
        <div className={cn("rounded-xl p-3 border", bgColors[color])}>
            <div className="flex items-center gap-2 mb-1">
                {icon}
                <span className="text-xs font-bold">{label}</span>
            </div>
            <p className="text-[10px] text-muted-foreground">{description}</p>
        </div>
    );
};
