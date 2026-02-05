import React, { Suspense } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon, Orbit, Radio, Calendar } from "lucide-react";
import { cn } from '@/lib/utils';
import { useIsMobile } from '@/hooks/useMediaQuery';
import { SolarWeatherStation } from './components/SolarWeatherStation';
import { LunarObservatory } from './components/LunarObservatory';
import { TransitOrrery } from './components/TransitOrrery';
import { UpcomingEvents } from './components/UpcomingEvents';

type TabKey = 'solar' | 'lunar' | 'transits' | 'events';

const tabs: { key: TabKey; label: string; icon: React.ElementType; color: string; bgGlow: string }[] = [
    { key: 'solar', label: 'Solar', icon: Sun, color: 'text-amber-500', bgGlow: 'from-amber-500/10' },
    { key: 'lunar', label: 'Lunar', icon: Moon, color: 'text-indigo-500', bgGlow: 'from-indigo-500/10' },
    { key: 'transits', label: 'Transits', icon: Orbit, color: 'text-violet-500', bgGlow: 'from-violet-500/10' },
    { key: 'events', label: 'Upcoming', icon: Calendar, color: 'text-emerald-500', bgGlow: 'from-emerald-500/10' },
];

const LoadingSkeleton = ({ message }: { message: string }) => (
    <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex flex-col items-center justify-center h-64 gap-4"
    >
        <div className="relative">
            <div className="w-16 h-16 rounded-full border-2 border-primary/20 animate-ping absolute inset-0" />
            <div className="w-16 h-16 rounded-full border-2 border-t-primary border-r-transparent border-b-transparent border-l-transparent animate-spin" />
        </div>
        <span className="text-sm text-muted-foreground font-medium animate-pulse">{message}</span>
    </motion.div>
);

export const TrackingPage = () => {
    const [searchParams, setSearchParams] = useSearchParams();
    const isMobile = useIsMobile();
    
    const activeTab = (searchParams.get('tab') as TabKey) || 'solar';
    
    const setActiveTab = (tab: TabKey) => {
        setSearchParams({ tab });
    };

    return (
        <div className="h-full overflow-y-auto overflow-x-hidden w-full min-w-0 flex flex-col">
            {/* HEADER - Fixed aesthetic */}
            <div className="shrink-0 px-4 pt-6 pb-4 border-b border-border/30 bg-gradient-to-b from-background to-background/80 backdrop-blur-sm sticky top-0 z-20">
                <div className="max-w-4xl mx-auto w-full min-w-0">
                    {/* Title Row */}
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-xl bg-primary/10 border border-primary/20">
                                <Radio className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-xl font-bold tracking-tight text-foreground">
                                    Deep Space Telemetry
                                </h1>
                                <p className="text-[11px] text-muted-foreground font-medium">
                                    Real-time cosmic surveillance
                                </p>
                            </div>
                        </div>
                        
                        {/* Live Indicator */}
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-lg shadow-emerald-500/50" />
                            <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-600">
                                Live Feed
                            </span>
                        </div>
                    </div>

                    {/* TAB NAVIGATION */}
                    <div className="flex gap-2">
                        {tabs.map((tab) => {
                            const Icon = tab.icon;
                            const isActive = activeTab === tab.key;
                            
                            return (
                                <motion.button
                                    key={tab.key}
                                    onClick={() => setActiveTab(tab.key)}
                                    whileTap={{ scale: 0.97 }}
                                    className={cn(
                                        "relative flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-medium text-sm transition-all",
                                        isActive 
                                            ? "bg-white shadow-md border border-white/60 text-foreground" 
                                            : "text-muted-foreground hover:text-foreground hover:bg-white/40"
                                    )}
                                >
                                    {isActive && (
                                        <motion.div
                                            layoutId="tab-bg"
                                            className={cn(
                                                "absolute inset-0 rounded-xl bg-gradient-to-br to-transparent opacity-50",
                                                tab.bgGlow
                                            )}
                                            transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                                        />
                                    )}
                                    <Icon className={cn(
                                        "w-4 h-4 relative z-10",
                                        isActive ? tab.color : ""
                                    )} />
                                    <span className="relative z-10">{tab.label}</span>
                                    
                                    {/* Active indicator dot */}
                                    {isActive && (
                                        <motion.div
                                            layoutId="tab-indicator"
                                            className={cn(
                                                "absolute -bottom-1 w-1 h-1 rounded-full",
                                                tab.color.replace('text-', 'bg-')
                                            )}
                                        />
                                    )}
                                </motion.button>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* CONTENT AREA */}
            <div className="flex-1 px-4 py-6 min-w-0 w-full">
                <div className="max-w-4xl mx-auto w-full min-w-0">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={activeTab}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.3 }}
                        >
                            {activeTab === 'solar' && (
                                <Suspense fallback={<LoadingSkeleton message="Acquiring Solar Telemetry..." />}>
                                    <SolarWeatherStation />
                                </Suspense>
                            )}
                            {activeTab === 'lunar' && (
                                <Suspense fallback={<LoadingSkeleton message="Calibrating Lunar Sensors..." />}>
                                    <LunarObservatory />
                                </Suspense>
                            )}
                            {activeTab === 'transits' && (
                                <Suspense fallback={<LoadingSkeleton message="Aligning Planetary Sensors..." />}>
                                    <TransitOrrery />
                                </Suspense>
                            )}
                            {activeTab === 'events' && (
                                <Suspense fallback={<LoadingSkeleton message="Scanning Future Timeline..." />}>
                                    <UpcomingEvents days={30} maxEvents={20} />
                                </Suspense>
                            )}
                        </motion.div>
                    </AnimatePresence>
                </div>
            </div>

            {/* Bottom padding for mobile nav */}
            {isMobile && <div className="h-24 shrink-0" />}
        </div>
    );
};
