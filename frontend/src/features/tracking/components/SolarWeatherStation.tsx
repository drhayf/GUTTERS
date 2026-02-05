import React from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
    LineChart, Line, XAxis, YAxis, ResponsiveContainer, ReferenceLine, Area, AreaChart, Tooltip
} from 'recharts';
import { Shield, ShieldAlert, Zap, Wind, Activity, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from '@/lib/utils';
import api from '@/lib/api';
import { AuroraAlert } from './AuroraAlert';

interface SolarData {
    kp_index: number;
    kp_status: string;
    bz: number;
    bz_orientation: string;
    solar_wind_speed: number;
    solar_wind_density: number;
    storm_potential: string;
    shield_integrity: string;
}

interface HistoryEntry {
    timestamp: string;
    data: {
        bz: number;
        solar_wind_speed: number;
        solar_wind_density: number;
        kp_index: number;
    };
}

export const SolarWeatherStation = () => {
    const { data: solarData, isLoading: solarLoading, error } = useQuery({
        queryKey: ['tracking-solar'],
        queryFn: async () => {
            const res = await api.get<{ current_data: SolarData }>('/api/v1/tracking/solar');
            console.log('[SolarWeatherStation] API Response:', res.data);
            return res.data.current_data;
        },
        refetchInterval: 30000, // 30 seconds for more live feel
        retry: 3,
        retryDelay: 1000
    });

    // Debug logging
    if (error) {
        console.error('[SolarWeatherStation] Query error:', error);
    }

    const { data: historyData } = useQuery({
        queryKey: ['tracking-solar-history'],
        queryFn: async () => {
            const res = await api.get<HistoryEntry[]>('/api/v1/tracking/history/solar?hours=24');
            return res.data.map((record) => ({
                time: new Date(record.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                bz: record.data.bz,
                speed: record.data.solar_wind_speed,
                density: record.data.solar_wind_density,
                kp: record.data.kp_index
            }));
        }
    });

    if (solarLoading || !solarData) {
        return (
            <div className="space-y-4">
                {[1, 2, 3].map(i => (
                    <div key={i} className="h-32 animate-pulse bg-white/40 rounded-2xl" />
                ))}
                {error && (
                    <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                        Failed to load solar data. Retrying...
                    </div>
                )}
            </div>
        );
    }

    const getShieldConfig = (status: string) => {
        const configs: Record<string, { color: string; bg: string; border: string; icon: React.ElementType; pulse: boolean }> = {
            'CRITICAL FAILURE': { color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/30', icon: ShieldAlert, pulse: true },
            'CRACKED': { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', icon: ShieldAlert, pulse: true },
            'STRAINED': { color: 'text-amber-500', bg: 'bg-amber-500/10', border: 'border-amber-500/20', icon: ShieldAlert, pulse: true },
            'BUFFETED': { color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', icon: Shield, pulse: false },
            'HOLDING': { color: 'text-emerald-500', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', icon: Shield, pulse: false },
        };
        return configs[status] || configs['HOLDING'];
    };

    const shieldConfig = getShieldConfig(solarData.shield_integrity ?? 'HOLDING');
    const ShieldIcon = shieldConfig.icon;

    const getBzColor = (bz: number) => bz < -5 ? 'text-red-400' : bz < 0 ? 'text-amber-400' : 'text-emerald-400';
    const getSpeedColor = (speed: number) => speed > 600 ? 'text-red-400' : speed > 500 ? 'text-amber-400' : 'text-teal-400';

    return (
        <div className="space-y-4">
            {/* LOCATION-AWARE AURORA ALERT */}
            <AuroraAlert />
            
            {/* SHIELD STATUS - Hero Card */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                    "relative overflow-hidden rounded-2xl p-6 border backdrop-blur-sm",
                    shieldConfig.bg, shieldConfig.border
                )}
            >
                {/* Background Pulse Animation */}
                {shieldConfig.pulse && (
                    <motion.div
                        className={cn("absolute inset-0 opacity-30", shieldConfig.bg)}
                        animate={{ opacity: [0.2, 0.4, 0.2] }}
                        transition={{ duration: 2, repeat: Infinity }}
                    />
                )}

                <div className="flex items-center justify-between relative z-10">
                    <div className="flex items-center gap-4">
                        <div className={cn(
                            "p-4 rounded-2xl border",
                            shieldConfig.bg, shieldConfig.border
                        )}>
                            <ShieldIcon className={cn("w-10 h-10", shieldConfig.color, shieldConfig.pulse && "animate-pulse")} />
                        </div>
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1">
                                Magnetosphere Status
                            </p>
                            <h2 className={cn("text-3xl font-black tracking-tight", shieldConfig.color)}>
                                {solarData.shield_integrity}
                            </h2>
                        </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="flex gap-6">
                        <div className="text-right">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Bz (IMF)</p>
                            <div className="flex items-center gap-1 justify-end">
                                {(solarData.bz ?? 0) < 0 ? 
                                    <TrendingDown className={cn("w-4 h-4", getBzColor(solarData.bz ?? 0))} /> :
                                    <TrendingUp className={cn("w-4 h-4", getBzColor(solarData.bz ?? 0))} />
                                }
                                <span className={cn("text-2xl font-mono-data font-black", getBzColor(solarData.bz ?? 0))}>
                                    {(solarData.bz ?? 0).toFixed(1)}
                                </span>
                                <span className="text-sm text-muted-foreground">nT</span>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Solar Wind</p>
                            <div className="flex items-center gap-1 justify-end">
                                <Wind className={cn("w-4 h-4", getSpeedColor(solarData.solar_wind_speed ?? 0))} />
                                <span className={cn("text-2xl font-mono-data font-black", getSpeedColor(solarData.solar_wind_speed ?? 0))}>
                                    {Math.round(solarData.solar_wind_speed ?? 0)}
                                </span>
                                <span className="text-sm text-muted-foreground">km/s</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Storm Potential Bar */}
                <div className="mt-6 pt-4 border-t border-border/30 relative z-10">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Activity className="w-4 h-4 text-muted-foreground" />
                            <span className="text-xs font-medium text-muted-foreground">Storm Potential</span>
                        </div>
                        <span className={cn(
                            "text-xs font-bold uppercase px-2 py-1 rounded-full",
                            solarData.storm_potential === 'Critical' ? 'bg-red-500/20 text-red-500' :
                            solarData.storm_potential === 'High' ? 'bg-amber-500/20 text-amber-500' :
                            'bg-emerald-500/20 text-emerald-500'
                        )}>
                            {solarData.storm_potential}
                        </span>
                    </div>
                </div>
            </motion.div>

            {/* TELEMETRY CHARTS */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Bz Graph */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="glass rounded-2xl p-4 border border-white/20"
                >
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            <div className="p-1.5 rounded-lg bg-amber-500/10">
                                <Zap className="w-4 h-4 text-amber-500" />
                            </div>
                            <div>
                                <h3 className="text-sm font-bold">Interplanetary Magnetic Field</h3>
                                <p className="text-[10px] text-muted-foreground">Bz Component (24h)</p>
                            </div>
                        </div>
                        <span className="text-[9px] font-mono-data text-muted-foreground px-2 py-1 rounded bg-muted/50">
                            nT
                        </span>
                    </div>

                    <div className="h-[180px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={historyData || []}>
                                <defs>
                                    <linearGradient id="bzGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#fbbf24" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#fbbf24" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="time" hide />
                                <YAxis 
                                    domain={[-20, 20]} 
                                    fontSize={10} 
                                    tickLine={false} 
                                    axisLine={false}
                                    tickFormatter={(v) => `${v}`}
                                    width={30}
                                />
                                <Tooltip
                                    contentStyle={{ 
                                        backgroundColor: 'rgba(255,255,255,0.95)', 
                                        borderRadius: '12px',
                                        border: '1px solid rgba(0,0,0,0.1)',
                                        fontSize: '12px',
                                        boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
                                    }}
                                />
                                <ReferenceLine y={0} stroke="#d4d4d4" strokeWidth={1} />
                                <ReferenceLine y={-10} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.5} />
                                <Line
                                    type="monotone"
                                    dataKey="bz"
                                    stroke="#fbbf24"
                                    strokeWidth={2}
                                    dot={false}
                                    fill="url(#bzGradient)"
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* Solar Wind Graph */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="glass rounded-2xl p-4 border border-white/20"
                >
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2">
                            <div className="p-1.5 rounded-lg bg-teal-500/10">
                                <Wind className="w-4 h-4 text-teal-500" />
                            </div>
                            <div>
                                <h3 className="text-sm font-bold">Solar Wind Velocity</h3>
                                <p className="text-[10px] text-muted-foreground">Plasma Speed (24h)</p>
                            </div>
                        </div>
                        <span className="text-[9px] font-mono-data text-muted-foreground px-2 py-1 rounded bg-muted/50">
                            km/s
                        </span>
                    </div>

                    <div className="h-[180px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={historyData || []}>
                                <defs>
                                    <linearGradient id="speedGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#0d9488" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#0d9488" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="time" hide />
                                <YAxis 
                                    fontSize={10} 
                                    tickLine={false} 
                                    axisLine={false}
                                    width={40}
                                />
                                <Tooltip
                                    contentStyle={{ 
                                        backgroundColor: 'rgba(255,255,255,0.95)', 
                                        borderRadius: '12px',
                                        border: '1px solid rgba(0,0,0,0.1)',
                                        fontSize: '12px',
                                        boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
                                    }}
                                />
                                <ReferenceLine y={500} stroke="#f59e0b" strokeDasharray="3 3" strokeOpacity={0.5} />
                                <Area
                                    type="monotone"
                                    dataKey="speed"
                                    stroke="#0d9488"
                                    strokeWidth={2}
                                    fill="url(#speedGradient)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>
            </div>

            {/* METRICS GRID */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="grid grid-cols-2 md:grid-cols-4 gap-3"
            >
                <MetricCard
                    label="Kp Index"
                    value={(solarData.kp_index ?? 0).toFixed(0)}
                    unit=""
                    status={solarData.kp_status ?? 'Unknown'}
                    color={(solarData.kp_index ?? 0) >= 5 ? 'red' : (solarData.kp_index ?? 0) >= 4 ? 'amber' : 'emerald'}
                />
                <MetricCard
                    label="Bz Orientation"
                    value={solarData.bz_orientation ?? 'Unknown'}
                    unit=""
                    color={(solarData.bz_orientation ?? '') === 'South' ? 'red' : 'emerald'}
                />
                <MetricCard
                    label="Wind Density"
                    value={(solarData.solar_wind_density ?? 0).toFixed(1)}
                    unit="p/cm³"
                    color={(solarData.solar_wind_density ?? 0) > 10 ? 'amber' : 'teal'}
                />
                <MetricCard
                    label="Storm Class"
                    value={(solarData.kp_status ?? 'Quiet').split(' ')[0] || 'Quiet'}
                    unit=""
                    color={(solarData.kp_index ?? 0) >= 5 ? 'red' : 'emerald'}
                />
            </motion.div>
        </div>
    );
};

const MetricCard = ({ 
    label, 
    value, 
    unit, 
    status,
    color 
}: { 
    label: string; 
    value: string; 
    unit: string; 
    status?: string;
    color: 'red' | 'amber' | 'emerald' | 'teal' 
}) => {
    const colorClasses = {
        red: 'text-red-500 bg-red-500/10 border-red-500/20',
        amber: 'text-amber-500 bg-amber-500/10 border-amber-500/20',
        emerald: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20',
        teal: 'text-teal-500 bg-teal-500/10 border-teal-500/20',
    };

    return (
        <div className={cn(
            "rounded-xl p-4 border backdrop-blur-sm",
            colorClasses[color].split(' ').slice(1).join(' ')
        )}>
            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1">{label}</p>
            <div className="flex items-baseline gap-1">
                <span className={cn("text-2xl font-mono-data font-black", colorClasses[color].split(' ')[0])}>
                    {value}
                </span>
                {unit && <span className="text-xs text-muted-foreground">{unit}</span>}
            </div>
            {status && <p className="text-[10px] text-muted-foreground mt-1">{status}</p>}
        </div>
    );
};
