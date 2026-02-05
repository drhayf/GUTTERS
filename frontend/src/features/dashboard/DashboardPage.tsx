import { motion } from 'framer-motion'
import PlayerStatus from './components/PlayerStatus'
import QuestBoard from './components/QuestBoard'
import InsightFeed from './components/InsightFeed'
import CosmicStatus from './components/CosmicStatus'
import TimelineScrubber from './components/TimelineScrubber'
import BirthCardWidget from './widgets/BirthCardWidget'
import PeriodForecast from './widgets/PeriodForecast'
import { useIsMobile } from '@/hooks/useMediaQuery'
import { UpcomingEvents } from '@/features/tracking/components/UpcomingEvents'

const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1,
            delayChildren: 0.05,
        }
    }
}

const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
        opacity: 1, 
        y: 0,
        transition: { duration: 0.4, ease: [0.25, 0.1, 0.25, 1] as const }
    }
}

export default function DashboardPage() {
    const isMobile = useIsMobile()

    return (
        <div className="h-full overflow-y-auto overflow-x-hidden w-full min-w-0">
            <motion.div 
                className="max-w-md mx-auto md:max-w-4xl space-y-6 px-4 py-6 w-full min-w-0"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >
                {/* 1. PLAYER HUD (Rank, XP, Sync) */}
                <motion.section variants={itemVariants}>
                    <PlayerStatus />
                </motion.section>

                {/* 2. MAGI TIMELINE SCRUBBER - 52-day Period Progress */}
                <motion.section variants={itemVariants}>
                    <TimelineScrubber />
                </motion.section>

                {/* 2.5 PERIOD FORECAST - Next 7 Days */}
                <motion.section variants={itemVariants}>
                    <PeriodForecast />
                </motion.section>

                {/* 3. COSMIC STATUS + BIRTH CARD (Desktop: Side by Side) */}
                <motion.div 
                    className="grid grid-cols-1 md:grid-cols-[1fr,auto] gap-6"
                    variants={itemVariants}
                >
                    {/* Cosmic Status (larger) */}
                    <CosmicStatus />
                    
                    {/* Birth Card Widget (sidebar on desktop) */}
                    <div className={isMobile ? "flex justify-center" : ""}>
                        <div className="md:w-[180px]">
                            <div className="sticky top-6">
                                <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-2 text-center">
                                    Birth Card
                                </p>
                                <BirthCardWidget />
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* 4. QUESTS & INTELLIGENCE GRID */}
                <motion.div 
                    className="grid grid-cols-1 md:grid-cols-2 gap-6"
                    variants={itemVariants}
                >
                    {/* QUEST BOARD */}
                    <motion.section 
                        className="relative overflow-hidden rounded-2xl p-5 border border-white/20 bg-white/40 backdrop-blur-sm shadow-sm"
                        whileHover={{ scale: 1.005 }}
                        transition={{ type: "spring", stiffness: 400 }}
                    >
                        {/* Subtle gradient decoration */}
                        <div className="absolute -top-10 -right-10 w-32 h-32 bg-gradient-to-br from-violet-500/5 to-transparent rounded-full blur-2xl" />
                        <QuestBoard />
                    </motion.section>

                    {/* INTELLIGENCE FEED */}
                    <motion.section 
                        className="relative overflow-hidden h-[400px] md:h-auto rounded-2xl p-5 border border-white/20 bg-white/40 backdrop-blur-sm shadow-sm"
                        whileHover={{ scale: 1.005 }}
                        transition={{ type: "spring", stiffness: 400 }}
                    >
                        {/* Subtle gradient decoration */}
                        <div className="absolute -top-10 -left-10 w-32 h-32 bg-gradient-to-br from-emerald-500/5 to-transparent rounded-full blur-2xl" />
                        <InsightFeed />
                    </motion.section>
                </motion.div>

                {/* 4. UPCOMING COSMIC EVENTS - Compact Widget */}
                <motion.section variants={itemVariants}>
                    <UpcomingEvents 
                        days={7} 
                        maxEvents={5} 
                        showFilters={false}
                        defaultView="compact"
                    />
                </motion.section>

                {/* Bottom padding for mobile nav */}
                {isMobile && <div className="h-24" />}
            </motion.div>
        </div>
    )
}
