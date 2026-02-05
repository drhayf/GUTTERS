import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Moon, Orbit, Zap, ArrowRight, Shield, Activity } from 'lucide-react'
import api from '@/lib/api'
import { cn } from '@/lib/utils'

interface CosmicWidgetResponse {
    moon_phase: string
    moon_sign: string
    sun_sign: string
    active_transits_count: number
    geomagnetic_index: number
    // Extended fields (if available)
    bz?: number
    solar_wind_speed?: number
    shield_integrity?: string
    is_voc?: boolean
    retrograde_count?: number
}

export default function CosmicStatus() {
    const navigate = useNavigate()
    const { data: cosmic, isLoading } = useQuery({
        queryKey: ['dashboard-cosmic'],
        queryFn: async () => {
            const res = await api.get<CosmicWidgetResponse>('/api/v1/dashboard/cosmic')
            return res.data
        },
        refetchInterval: 60000 // Refresh every minute for live feel
    })

    if (isLoading) {
        return (
            <div className="space-y-3">
                <div className="h-24 animate-pulse bg-white/40 rounded-xl" />
                <div className="h-20 animate-pulse bg-white/40 rounded-xl" />
            </div>
        )
    }
    if (!cosmic) return null

    // Kp Color Logic
    const getKpColor = (kp: number) => {
        if (kp >= 5) return { text: "text-red-500", bg: "bg-red-500/10", border: "border-red-500/20", glow: "shadow-red-500/20" }
        if (kp >= 4) return { text: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/20", glow: "shadow-amber-500/20" }
        return { text: "text-emerald-500", bg: "bg-emerald-500/10", border: "border-emerald-500/20", glow: "shadow-emerald-500/20" }
    }

    const kpStyle = getKpColor(cosmic.geomagnetic_index)
    const shieldStatus = cosmic.shield_integrity || (cosmic.geomagnetic_index >= 5 ? "STRAINED" : "NOMINAL")

    return (
        <div className="space-y-3">
            {/* COSMIC INTELLIGENCE HEADER */}
            <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2">
                    <Activity className="w-3.5 h-3.5 text-primary animate-pulse" />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                        Cosmic Intelligence
                    </span>
                </div>
                <div className="flex items-center gap-1">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[9px] font-mono-data text-muted-foreground">LIVE</span>
                </div>
            </div>

            {/* MAIN TRACKING CARDS - Each navigates to specific tab */}
            <div className="grid grid-cols-2 gap-3">
                {/* LUNAR CARD - Navigate to Lunar tab */}
                <motion.button
                    onClick={() => navigate('/tracking?tab=lunar')}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="relative overflow-hidden glass rounded-xl p-4 flex flex-col items-start text-left space-y-2 hover:bg-white/70 transition-all group border border-transparent hover:border-indigo-200/50"
                >
                    {/* Background Glow */}
                    <div className="absolute -top-6 -right-6 w-20 h-20 bg-indigo-400/10 rounded-full blur-xl group-hover:bg-indigo-400/20 transition-colors" />
                    
                    <div className="flex items-center justify-between w-full relative z-10">
                        <div className={cn(
                            "p-2 rounded-lg",
                            cosmic.is_voc ? "bg-amber-500/10" : "bg-indigo-500/10"
                        )}>
                            <Moon className={cn(
                                "w-5 h-5",
                                cosmic.is_voc ? "text-amber-500" : "text-indigo-500"
                            )} />
                        </div>
                        <ArrowRight className="w-4 h-4 text-muted-foreground/40 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                    </div>
                    
                    <div className="relative z-10">
                        <h4 className="text-sm font-bold text-foreground">{cosmic.moon_sign}</h4>
                        <p className="text-[10px] text-muted-foreground">{cosmic.moon_phase}</p>
                    </div>

                    {cosmic.is_voc && (
                        <div className="absolute bottom-2 right-2">
                            <span className="text-[8px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-600 animate-pulse">
                                VoC
                            </span>
                        </div>
                    )}
                </motion.button>

                {/* SOLAR CARD - Navigate to Solar tab */}
                <motion.button
                    onClick={() => navigate('/tracking?tab=solar')}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={cn(
                        "relative overflow-hidden glass rounded-xl p-4 flex flex-col items-start text-left space-y-2 hover:bg-white/70 transition-all group border border-transparent",
                        `hover:${kpStyle.border}`
                    )}
                >
                    {/* Background Glow */}
                    <div className={cn(
                        "absolute -top-6 -right-6 w-20 h-20 rounded-full blur-xl transition-colors",
                        kpStyle.bg,
                        "group-hover:opacity-100 opacity-50"
                    )} />
                    
                    <div className="flex items-center justify-between w-full relative z-10">
                        <div className={cn("p-2 rounded-lg", kpStyle.bg)}>
                            <Shield className={cn("w-5 h-5", kpStyle.text)} />
                        </div>
                        <ArrowRight className="w-4 h-4 text-muted-foreground/40 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                    </div>
                    
                    <div className="relative z-10">
                        <div className="flex items-baseline gap-1.5">
                            <span className={cn("text-lg font-mono-data font-black", kpStyle.text)}>
                                Kp{cosmic.geomagnetic_index}
                            </span>
                            <Zap className={cn("w-3 h-3", kpStyle.text, cosmic.geomagnetic_index >= 4 && "animate-pulse")} />
                        </div>
                        <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-wide">
                            {shieldStatus}
                        </p>
                    </div>
                </motion.button>
            </div>

            {/* TRANSITS CARD - Full width, Navigate to Transits tab */}
            <motion.button
                onClick={() => navigate('/tracking?tab=transits')}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                className="w-full relative overflow-hidden glass rounded-xl p-4 flex items-center justify-between hover:bg-white/70 transition-all group border border-transparent hover:border-violet-200/50"
            >
                {/* Background Glow */}
                <div className="absolute -top-10 -left-10 w-32 h-32 bg-violet-400/5 rounded-full blur-2xl group-hover:bg-violet-400/10 transition-colors" />
                
                <div className="flex items-center gap-4 relative z-10">
                    <div className="p-2.5 rounded-lg bg-violet-500/10">
                        <Orbit className="w-5 h-5 text-violet-500" />
                    </div>
                    <div className="text-left">
                        <h4 className="text-sm font-bold text-foreground">Planetary Transits</h4>
                        <div className="flex items-center gap-2">
                            <span className="text-[10px] text-muted-foreground">
                                {cosmic.active_transits_count || 0} Active Aspects
                            </span>
                            {(cosmic.retrograde_count ?? 0) > 0 && (
                                <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-600">
                                    {cosmic.retrograde_count} Rx
                                </span>
                            )}
                        </div>
                    </div>
                </div>
                
                <ArrowRight className="w-5 h-5 text-muted-foreground/40 group-hover:text-primary group-hover:translate-x-1 transition-all relative z-10" />
            </motion.button>
        </div>
    )
}
