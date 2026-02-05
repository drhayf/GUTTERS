import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';

// ============================================================================
// TYPES
// ============================================================================

interface LineArchetype {
    number: number;
    name: string;
    theme: string;
    description: string;
}

const LINE_ARCHETYPES: Record<number, LineArchetype> = {
    1: { number: 1, name: 'Investigator', theme: 'Foundation / Introspection', description: 'Seeks security through knowledge' },
    2: { number: 2, name: 'Hermit', theme: 'Projection / Natural Talent', description: 'Possesses natural gifts, waits to be called' },
    3: { number: 3, name: 'Martyr', theme: 'Adaptation / Trial and Error', description: 'Learns through experience and mistakes' },
    4: { number: 4, name: 'Opportunist', theme: 'Externalization / Network', description: 'Influences through relationships' },
    5: { number: 5, name: 'Heretic', theme: 'Universalization / Practical', description: 'Practical solutions for all' },
    6: { number: 6, name: 'Role Model', theme: 'Transition / Wisdom', description: 'Wisdom gained through experience' },
};

interface HexagramWidgetProps {
    gateNumber: number;
    gateName: string;
    currentLine: number;
    sunActivation: boolean; // true for Sun (Yang/Solid), false for Earth (Yin/Broken)
    className?: string;
    showLabels?: boolean;
}

// ============================================================================
// LINE COMPONENT
// ============================================================================

interface HexagramLineProps {
    lineNumber: number;
    isActive: boolean;
    isYang: boolean;
    archetype: LineArchetype;
}

const HexagramLine: React.FC<HexagramLineProps> = ({ lineNumber, isActive, isYang, archetype }) => {
    return (
        <TooltipProvider>
            <Tooltip delayDuration={200}>
                <TooltipTrigger asChild>
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: lineNumber * 0.05 }}
                        className={cn(
                            "relative h-8 flex items-center gap-2 group cursor-pointer transition-all",
                            isActive ? "scale-110" : "scale-100"
                        )}
                    >
                        {/* Line Number */}
                        <span className={cn(
                            "text-xs font-mono font-bold w-6 text-right transition-colors",
                            isActive ? "text-indigo-400" : "text-zinc-600"
                        )}>
                            {lineNumber}
                        </span>
                        
                        {/* The Line Itself */}
                        <div className="flex-1 relative h-3">
                            {isYang ? (
                                // Yang line (solid)
                                <motion.div
                                    className={cn(
                                        "absolute inset-0 rounded-full transition-all",
                                        isActive
                                            ? "bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 shadow-lg shadow-indigo-500/50"
                                            : "bg-zinc-700 group-hover:bg-zinc-600"
                                    )}
                                    animate={isActive ? {
                                        boxShadow: [
                                            "0 0 20px rgba(129, 140, 248, 0.5)",
                                            "0 0 40px rgba(167, 139, 250, 0.7)",
                                            "0 0 20px rgba(129, 140, 248, 0.5)",
                                        ]
                                    } : {}}
                                    transition={{ duration: 2, repeat: Infinity }}
                                />
                            ) : (
                                // Yin line (broken)
                                <>
                                    <motion.div
                                        className={cn(
                                            "absolute left-0 top-0 bottom-0 rounded-full transition-all",
                                            isActive
                                                ? "bg-gradient-to-r from-indigo-500 to-purple-500 shadow-lg shadow-indigo-500/50"
                                                : "bg-zinc-700 group-hover:bg-zinc-600"
                                        )}
                                        style={{ width: '45%' }}
                                        animate={isActive ? {
                                            boxShadow: [
                                                "0 0 20px rgba(129, 140, 248, 0.5)",
                                                "0 0 40px rgba(167, 139, 250, 0.7)",
                                                "0 0 20px rgba(129, 140, 248, 0.5)",
                                            ]
                                        } : {}}
                                        transition={{ duration: 2, repeat: Infinity }}
                                    />
                                    <motion.div
                                        className={cn(
                                            "absolute right-0 top-0 bottom-0 rounded-full transition-all",
                                            isActive
                                                ? "bg-gradient-to-r from-purple-500 to-pink-500 shadow-lg shadow-purple-500/50"
                                                : "bg-zinc-700 group-hover:bg-zinc-600"
                                        )}
                                        style={{ width: '45%' }}
                                        animate={isActive ? {
                                            boxShadow: [
                                                "0 0 20px rgba(167, 139, 250, 0.5)",
                                                "0 0 40px rgba(236, 72, 153, 0.7)",
                                                "0 0 20px rgba(167, 139, 250, 0.5)",
                                            ]
                                        } : {}}
                                        transition={{ duration: 2, repeat: Infinity, delay: 0.5 }}
                                    />
                                </>
                            )}
                            
                            {/* Glow effect for active line */}
                            {isActive && (
                                <motion.div
                                    className="absolute inset-0 rounded-full bg-gradient-to-r from-indigo-400/20 via-purple-400/20 to-pink-400/20 blur-xl"
                                    animate={{
                                        opacity: [0.5, 1, 0.5],
                                        scale: [1, 1.2, 1],
                                    }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                />
                            )}
                        </div>
                        
                        {/* Active indicator */}
                        {isActive && (
                            <motion.div
                                initial={{ scale: 0 }}
                                animate={{ scale: 1 }}
                                className="w-2 h-2 rounded-full bg-indigo-400 shadow-lg shadow-indigo-400/50"
                            />
                        )}
                    </motion.div>
                </TooltipTrigger>
                <TooltipContent
                    side="right"
                    className={cn(
                        "max-w-xs p-4 border bg-zinc-950/95 backdrop-blur-xl",
                        isActive ? "border-indigo-500/30" : "border-zinc-800"
                    )}
                >
                    <div className="space-y-2">
                        <div className="flex items-center gap-2">
                            <div className={cn(
                                "w-1.5 h-1.5 rounded-full",
                                isActive ? "bg-indigo-400" : "bg-zinc-600"
                            )} />
                            <p className={cn(
                                "text-xs font-bold uppercase tracking-wider",
                                isActive ? "text-indigo-400" : "text-zinc-500"
                            )}>
                                Line {lineNumber}
                            </p>
                        </div>
                        <p className="text-sm font-bold text-zinc-100">
                            {archetype.name}
                        </p>
                        <p className="text-xs text-indigo-400/80 font-medium">
                            {archetype.theme}
                        </p>
                        <p className="text-xs text-zinc-400 leading-relaxed">
                            {archetype.description}
                        </p>
                        {isActive && (
                            <div className="pt-2 mt-2 border-t border-zinc-800">
                                <p className="text-[10px] font-bold uppercase tracking-widest text-indigo-400/60">
                                    ⚡ Currently Active
                                </p>
                            </div>
                        )}
                    </div>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
};

// ============================================================================
// HEXAGRAM WIDGET
// ============================================================================

export const HexagramWidget: React.FC<HexagramWidgetProps> = ({
    gateNumber,
    gateName,
    currentLine,
    sunActivation = true,
    className,
    showLabels = true,
}) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "relative overflow-hidden rounded-2xl p-6 border border-indigo-500/20 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 backdrop-blur-sm",
                className
            )}
        >
            {/* Background decoration */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-3xl" />
            
            <div className="relative z-10 space-y-6">
                {/* Header */}
                {showLabels && (
                    <div className="space-y-1">
                        <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                            I-Ching Hexagram
                        </p>
                        <div className="flex items-baseline gap-2">
                            <h3 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
                                Gate {gateNumber}
                            </h3>
                            <span className="text-sm text-zinc-500">•</span>
                            <span className="text-sm font-semibold text-zinc-400">
                                Line {currentLine}
                            </span>
                        </div>
                        <p className="text-sm text-zinc-400 font-medium">
                            {gateName}
                        </p>
                    </div>
                )}
                
                {/* The Six Lines */}
                <div className="space-y-2">
                    {/* Lines drawn top-to-bottom (6 to 1), traditional I-Ching style */}
                    {[6, 5, 4, 3, 2, 1].map((lineNumber) => (
                        <HexagramLine
                            key={lineNumber}
                            lineNumber={lineNumber}
                            isActive={lineNumber === currentLine}
                            isYang={sunActivation} // Could be made dynamic per line
                            archetype={LINE_ARCHETYPES[lineNumber]}
                        />
                    ))}
                </div>
                
                {/* Current Line Info */}
                <div className="pt-4 border-t border-zinc-800/50">
                    <div className="flex items-center gap-2 mb-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                        <p className="text-[10px] font-bold uppercase tracking-widest text-indigo-400/60">
                            Active Archetype
                        </p>
                    </div>
                    <p className="text-lg font-bold text-zinc-100">
                        {LINE_ARCHETYPES[currentLine]?.name}
                    </p>
                    <p className="text-xs text-indigo-400/80 font-medium mt-1">
                        {LINE_ARCHETYPES[currentLine]?.theme}
                    </p>
                </div>
            </div>
        </motion.div>
    );
};

export default HexagramWidget;
