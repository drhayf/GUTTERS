import { motion } from 'framer-motion'
import CouncilDashboard from '@/components/council/CouncilDashboard'

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

export default function CouncilPage() {
    return (
        <div className="h-full overflow-y-auto overflow-x-hidden w-full min-w-0">
            <motion.div 
                className="max-w-5xl mx-auto space-y-6 px-4 py-6 w-full min-w-0"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >
                {/* Header */}
                <motion.div className="text-center space-y-2 mb-4">
                    <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
                        Council of Systems
                    </h1>
                    <p className="text-sm text-zinc-500 font-medium">
                        Multi-paradigm synthesis of I-Ching & Cardology
                    </p>
                </motion.div>

                {/* Council Dashboard Component */}
                <CouncilDashboard />
            </motion.div>
        </div>
    )
}
