import React from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Sparkles, Compass, Layers } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import api from '@/lib/api';
import HexagramWidget from './HexagramWidget';
import GuidancePanel from './GuidancePanel';

// ============================================================================
// TYPES
// ============================================================================

interface HexagramData {
    sun_gate: number;
    sun_line: number;
    sun_gate_name: string;
    sun_gate_keynote: string;
    sun_gene_key_gift: string;
    sun_gene_key_shadow: string;
    sun_gene_key_siddhi: string;
    earth_gate: number;
    earth_line: number;
    earth_gate_name: string;
    earth_gate_keynote: string;
    earth_gene_key_gift: string;
    polarity_theme: string;
}

interface CouncilSynthesis {
    resonance_score: number;
    resonance_type: string;
    resonance_description: string;
    macro_symbol: string;
    macro_archetype: string;
    macro_keynote: string;
    micro_symbol: string;
    micro_archetype: string;
    micro_keynote: string;
    unified_gift: string;
    unified_shadow: string;
    unified_siddhi: string;
    element_profile: Record<string, string>;
}

// ============================================================================
// GENE KEY SPECTRUM
// ============================================================================

interface GeneKeySpectrumProps {
    shadow: string;
    gift: string;
    siddhi: string;
}

const GeneKeySpectrum: React.FC<GeneKeySpectrumProps> = ({ shadow, gift, siddhi }) => {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative overflow-hidden rounded-2xl p-6 border border-purple-500/20 bg-gradient-to-br from-purple-500/5 to-pink-500/5 backdrop-blur-sm"
        >
            <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20">
                    <Sparkles className="w-6 h-6 text-purple-400" />
                </div>
                <div>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                        Gene Key Spectrum
                    </p>
                    <h3 className="text-lg font-bold text-foreground">Frequency Profile</h3>
                </div>
            </div>
            
            {/* Spectrum visualization */}
            <div className="relative">
                {/* Connection line */}
                <div className="absolute left-[11px] top-3 bottom-3 w-0.5 bg-gradient-to-b from-red-500/50 via-emerald-500/50 to-violet-500/50" />
                
                <div className="space-y-4">
                    {/* Shadow */}
                    <div className="flex items-start gap-3">
                        <div className="w-6 h-6 rounded-full bg-red-500/20 border border-red-500/30 flex items-center justify-center">
                            <div className="w-2 h-2 rounded-full bg-red-500" />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-red-400">Shadow</p>
                            <p className="text-sm font-medium text-foreground">{shadow}</p>
                        </div>
                    </div>
                    
                    {/* Gift */}
                    <div className="flex items-start gap-3">
                        <div className="w-6 h-6 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center">
                            <div className="w-2 h-2 rounded-full bg-emerald-500" />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-400">Gift</p>
                            <p className="text-sm font-medium text-foreground">{gift}</p>
                        </div>
                    </div>
                    
                    {/* Siddhi */}
                    <div className="flex items-start gap-3">
                        <div className="w-6 h-6 rounded-full bg-violet-500/20 border border-violet-500/30 flex items-center justify-center">
                            <div className="w-2 h-2 rounded-full bg-violet-500" />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-violet-400">Siddhi</p>
                            <p className="text-sm font-medium text-foreground">{siddhi}</p>
                        </div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

// ============================================================================
// RESONANCE INDICATOR
// ============================================================================

interface ResonanceIndicatorProps {
    score: number;
    type: string;
    description: string;
}

const ResonanceIndicator: React.FC<ResonanceIndicatorProps> = ({ score, type, description }) => {
    const getResonanceConfig = (resonanceType: string) => {
        const configs: Record<string, { color: string; bg: string; border: string; emoji: string }> = {
            harmonic: { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', emoji: '✨' },
            supportive: { color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20', emoji: '🌿' },
            neutral: { color: 'text-slate-400', bg: 'bg-slate-500/10', border: 'border-slate-500/20', emoji: '⚖️' },
            challenging: { color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', emoji: '🔥' },
            dissonant: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', emoji: '🌊' },
        };
        return configs[resonanceType] || configs.neutral;
    };
    
    const config = getResonanceConfig(type);
    const percentage = Math.round(score * 100);
    
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "relative overflow-hidden rounded-2xl p-6 border backdrop-blur-sm",
                config.bg, config.border
            )}
        >
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className={cn("p-2 rounded-xl border", config.bg, config.border)}>
                        <Layers className={cn("w-6 h-6", config.color)} />
                    </div>
                    <div>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                            Cross-System Resonance
                        </p>
                        <h3 className={cn("text-2xl font-black", config.color)}>
                            {config.emoji} {type.charAt(0).toUpperCase() + type.slice(1)}
                        </h3>
                    </div>
                </div>
                
                {/* Score circle */}
                <div className={cn(
                    "w-16 h-16 rounded-full border-4 flex items-center justify-center",
                    config.border
                )}>
                    <span className={cn("text-xl font-mono font-black", config.color)}>
                        {percentage}%
                    </span>
                </div>
            </div>
            
            {/* Progress bar */}
            <div className="h-2 bg-background/50 rounded-full overflow-hidden mb-3">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percentage}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                    className={cn("h-full rounded-full", config.color.replace('text-', 'bg-'))}
                />
            </div>
            
            <p className="text-sm text-muted-foreground">{description}</p>
        </motion.div>
    );
};

// ============================================================================
// CARDOLOGY CARD
// ============================================================================

interface CardologyCardProps {
    symbol: string;
    archetype: string;
    keynote: string;
}

const CardologyCard: React.FC<CardologyCardProps> = ({ symbol, archetype, keynote }) => {
    // Parse card symbol (e.g., "J♦" -> Jack of Diamonds)
    const getSuitColor = (symbol: string) => {
        if (symbol.includes('♦') || symbol.includes('♥')) return 'text-red-500';
        return 'text-slate-700';
    };
    
    return (
        <motion.div
            initial={{ opacity: 0, rotateY: -10 }}
            animate={{ opacity: 1, rotateY: 0 }}
            className="relative overflow-hidden rounded-2xl p-6 border border-amber-500/20 bg-gradient-to-br from-amber-500/5 to-orange-500/5 backdrop-blur-sm"
        >
            <div className="flex items-start gap-4">
                {/* Card visual */}
                <div className="relative w-20 h-28 rounded-lg bg-white shadow-lg border border-slate-200 flex items-center justify-center">
                    <span className={cn("text-4xl font-bold", getSuitColor(symbol))}>
                        {symbol}
                    </span>
                </div>
                
                <div className="flex-1 space-y-2">
                    <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                        Cardology (52-Day Cycle)
                    </p>
                    <h3 className="text-lg font-bold text-foreground">{archetype}</h3>
                    <p className="text-sm text-muted-foreground">{keynote}</p>
                </div>
            </div>
        </motion.div>
    );
};

// ============================================================================
// MAIN COUNCIL DASHBOARD
// ============================================================================

export const CouncilDashboard: React.FC = () => {
    // Fetch hexagram data
    const { data: hexagramData, isLoading: hexagramLoading } = useQuery({
        queryKey: ['council-hexagram'],
        queryFn: async () => {
            const res = await api.get<{ hexagram: HexagramData }>('/api/v1/intelligence/council/hexagram');
            return res.data.hexagram;
        },
        refetchInterval: 60000, // Refresh every minute
    });
    
    // Fetch synthesis data
    const { data: synthesisData, isLoading: synthesisLoading } = useQuery({
        queryKey: ['council-synthesis'],
        queryFn: async () => {
            const res = await api.get<{ council: CouncilSynthesis }>('/api/v1/intelligence/council/synthesis');
            return res.data.council;
        },
        refetchInterval: 60000,
    });
    
    const isLoading = hexagramLoading || synthesisLoading;
    
    if (isLoading) {
        return (
            <div className="space-y-4">
                {[1, 2, 3, 4].map(i => (
                    <div key={i} className="h-40 animate-pulse bg-white/40 rounded-2xl" />
                ))}
            </div>
        );
    }
    
    return (
        <div className="space-y-6">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center"
            >
                <h1 className="text-2xl font-black text-foreground mb-2">
                    Council of Systems
                </h1>
                <p className="text-sm text-muted-foreground">
                    Multi-paradigm synthesis of I-Ching & Cardology
                </p>
            </motion.div>
            
            {/* Resonance Indicator (Hero) */}
            {synthesisData && (
                <ResonanceIndicator
                    score={synthesisData.resonance_score}
                    type={synthesisData.resonance_type}
                    description={synthesisData.resonance_description}
                />
            )}
            
            {/* Two column grid */}
            <div className="grid md:grid-cols-2 gap-4">
                {/* I-Ching Hexagram with Line Visualization */}
                {hexagramData && (
                    <HexagramWidget
                        gateNumber={hexagramData.sun_gate}
                        gateName={hexagramData.sun_gate_name}
                        currentLine={hexagramData.sun_line}
                        sunActivation={true}
                    />
                )}
                
                {/* Cardology Card */}
                {synthesisData && (
                    <CardologyCard
                        symbol={synthesisData.macro_symbol}
                        archetype={synthesisData.macro_archetype}
                        keynote={synthesisData.macro_keynote}
                    />
                )}
            </div>
            
            {/* Contextual Guidance Panel */}
            <GuidancePanel />
            
            {/* Gene Key Spectrum */}
            {synthesisData && (
                <GeneKeySpectrum
                    shadow={synthesisData.unified_shadow}
                    gift={synthesisData.unified_gift}
                    siddhi={synthesisData.unified_siddhi}
                />
            )}
            
            {/* Element Profile */}
            {synthesisData?.element_profile && (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-2xl p-6 border border-border/50 bg-background/50 backdrop-blur-sm"
                >
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 rounded-xl bg-teal-500/10 border border-teal-500/20">
                            <Compass className="w-6 h-6 text-teal-400" />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                                Elemental Profile
                            </p>
                            <h3 className="text-lg font-bold text-foreground">Current Alignment</h3>
                        </div>
                    </div>
                    
                    <div className="flex flex-wrap gap-2">
                        {Object.entries(synthesisData.element_profile).map(([system, element]) => {
                            const elementEmoji: Record<string, string> = {
                                fire: '🔥',
                                water: '💧',
                                air: '💨',
                                earth: '🌍',
                                ether: '✨'
                            };
                            return (
                                <Badge key={system} variant="outline" className="px-3 py-1">
                                    {elementEmoji[element.toLowerCase()] || '⭐'} {system}: {element}
                                </Badge>
                            );
                        })}
                    </div>
                </motion.div>
            )}
        </div>
    );
};

export default CouncilDashboard;
