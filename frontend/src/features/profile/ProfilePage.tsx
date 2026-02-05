import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, ExternalLink, Activity, Moon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { useAuthStore } from '@/stores/authStore'



import { useProgressionStats } from '@/hooks/useProgressionStats'

export default function ProfilePage() {
    const navigate = useNavigate()
    const { user, logout } = useAuthStore()

    const { data: stats } = useProgressionStats()

    const sections = [
        {
            title: "System",
            items: [
                {
                    icon: Shield,
                    label: "Control Room",
                    description: "Access system internals and logs",
                    action: () => navigate('/control-room'),
                    color: "text-emerald-600",
                    bgColor: "bg-emerald-50"
                },
                {
                    icon: Activity,
                    label: "Sync Status",
                    description: "Check system health and latency",
                    action: () => { }, // Placeholder
                    color: "text-blue-600",
                    bgColor: "bg-blue-50"
                }
            ]
        },
        {
            title: "Configuration",
            items: [
                {
                    icon: Activity,
                    label: "Nervous System",
                    description: "Configure cosmic alerts and sensitivity",
                    action: () => navigate('/settings/notifications'),
                    color: "text-amber-500",
                    bgColor: "bg-amber-50"
                },
                {
                    icon: Moon,
                    label: "Appearance",
                    description: "Manage theme and display settings",
                    action: () => { }, // Placeholder
                    color: "text-violet-600",
                    bgColor: "bg-violet-50"
                }
            ]
        }
    ]

    return (
        <div className="h-full overflow-y-auto overflow-x-hidden flex flex-col space-y-8 pb-20 px-4 w-full min-w-0 py-6">
            {/* Header / User Card */}
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-transparent p-6 border border-white/20 min-w-0 flex-shrink-0">
                <div className="flex items-center gap-4 relative z-10">
                    <Avatar className="h-16 w-16 border-2 border-white shadow-md">
                        <AvatarImage src={`https://api.dicebear.com/7.x/notionists/svg?seed=${user?.username}`} />
                        <AvatarFallback>
                            {user?.username?.[0]?.toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                    <div>
                        <h2 className="text-xl font-bold tracking-tight">{user?.username || 'Cosmic Traveler'}</h2>
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary/10 text-primary">
                            {stats ? `Rank ${stats.rank} // Lvl. ${stats.level}` : 'Loading...'}
                        </span>
                    </div>
                </div>

                {/* Decorative BG elements */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-2xl transform translate-x-10 -translate-y-10" />
            </div>

            {/* Menu Sections */}
            <div className="space-y-6">
                {sections.map((section, idx) => (
                    <motion.div
                        key={section.title}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="space-y-3"
                    >
                        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider px-1">
                            {section.title}
                        </h3>
                        <div className="grid gap-2">
                            {section.items.map((item) => (
                                <button
                                    key={item.label}
                                    onClick={item.action}
                                    className="flex items-center gap-4 w-full p-4 rounded-xl bg-white/40 hover:bg-white/60 active:scale-[0.98] transition-all border border-transparent hover:border-white/40 shadow-sm hover:shadow-md text-left group"
                                >
                                    <div className={`w-10 h-10 rounded-lg ${item.bgColor} ${item.color} flex items-center justify-center shrink-0`}>
                                        <item.icon className="w-5 h-5" />
                                    </div>
                                    <div className="flex-1">
                                        <div className="font-semibold text-zinc-800">{item.label}</div>
                                        <div className="text-xs text-muted-foreground">{item.description}</div>
                                    </div>
                                    <ExternalLink className="w-4 h-4 text-zinc-300 group-hover:text-primary transition-colors" />
                                </button>
                            ))}
                        </div>
                    </motion.div>
                ))}
            </div>

            <div className="px-4">
                <Button variant="destructive" className="w-full" onClick={logout}>
                    Disconnect Session
                </Button>
            </div>
        </div>
    )
}
