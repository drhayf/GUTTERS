import { Terminal, Activity, ListTodo } from 'lucide-react'
import SystemActivityWidget from './components/SystemActivityWidget'
import ModelSwitcher from './components/ModelSwitcher'
import WorkerControl from './components/WorkerControl'
import QuestEditor from '@/features/quests/QuestEditor'
import { motion } from 'framer-motion'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export default function ControlRoomPage() {
    return (
        <div className="h-full flex flex-col bg-background overflow-hidden">
            {/* Header */}
            <header className="p-6 border-b border-border/40 backdrop-blur-md bg-background/50 sticky top-0 z-10">
                <div className="flex items-center justify-between max-w-7xl mx-auto w-full">
                    <div className="flex items-center gap-4">
                        <div className="p-2.5 bg-primary/10 rounded-xl border border-primary/20 shadow-inner">
                            <Terminal className="w-6 h-6 text-primary" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight text-foreground/90 leading-tight">Control Room</h1>
                            <p className="text-muted-foreground text-sm font-medium">System Intelligence & Background Operations</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-500">System Link Active</span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Content Area */}
            <main className="flex-1 overflow-y-auto p-6 scrollbar-hide">
                <div className="max-w-7xl mx-auto h-full">
                    <Tabs defaultValue="system" className="space-y-6">
                        <TabsList className="bg-secondary/20 border border-border/50 p-1">
                            <TabsTrigger value="system" className="gap-2">
                                <Activity className="w-4 h-4" /> System Operations
                            </TabsTrigger>
                            <TabsTrigger value="directives" className="gap-2">
                                <ListTodo className="w-4 h-4" /> Directives & Quests
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value="system" className="space-y-8 pb-12">
                            {/* Top Row: System Health & Worker Control */}
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="lg:col-span-2"
                                >
                                    <SystemActivityWidget />
                                </motion.div>

                                <div className="space-y-6">
                                    <motion.div
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: 0.1 }}
                                    >
                                        <WorkerControl />
                                    </motion.div>

                                    <motion.div
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: 0.2 }}
                                    >
                                        <div className="p-6 rounded-2xl border border-border bg-secondary/10 backdrop-blur supports-[backdrop-filter]:bg-secondary/5 relative overflow-hidden group">
                                            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                                <Activity className="w-12 h-12" />
                                            </div>
                                            <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-4">Telemetry Stream</h3>
                                            <div className="space-y-4">
                                                <div className="flex items-center justify-between text-xs">
                                                    <span className="text-muted-foreground">Event Bus Latency</span>
                                                    <span className="font-mono text-primary font-medium">~12ms</span>
                                                </div>
                                                <div className="flex items-center justify-between text-xs">
                                                    <span className="text-muted-foreground">Active Streams</span>
                                                    <span className="font-mono text-primary font-medium">02</span>
                                                </div>
                                                <div className="h-1 bg-primary/10 rounded-full overflow-hidden">
                                                    <motion.div
                                                        className="h-full bg-primary"
                                                        animate={{ width: ["20%", "45%", "32%", "80%", "65%"] }}
                                                        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </motion.div>
                                </div>
                            </div>

                            {/* Middle Row: AI Config */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 }}
                            >
                                <ModelSwitcher />
                            </motion.div>
                        </TabsContent>

                        <TabsContent value="directives" className="space-y-6">
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-white/40 border border-white/20 shadow-sm backdrop-blur-md rounded-2xl p-6"
                            >
                                <QuestEditor />
                            </motion.div>
                        </TabsContent>
                    </Tabs>
                </div>
            </main>
        </div>
    )
}
