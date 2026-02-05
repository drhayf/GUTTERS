import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Bell, Sparkles, Activity, Sun, Target, Award, Signal, Moon, RotateCcw, Zap, ChevronDown, ChevronUp } from 'lucide-react'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { toast } from '@/hooks/use-toast'
import api from '@/lib/api'


// Helper for VAPID key conversion
function urlBase64ToUint8Array(base64String: string) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4)
    const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/')

    const rawData = window.atob(base64)
    const outputArray = new Uint8Array(rawData.length)

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i)
    }
    return outputArray
}

export default function NotificationSettingsPage() {
    const navigate = useNavigate()
    // const { user } = useAuthStore() // Unused

    const [isSupported, setIsSupported] = useState(false)
    const [isMasterEnabled, setIsMasterEnabled] = useState(false)
    const [loading, setLoading] = useState(false)
    const [testLoading, setTestLoading] = useState(false)

    // Granular Preferences (Default True)
    const [prefs, setPrefs] = useState({
        cosmic: true,
        // Granular cosmic preferences
        solar_alerts: true,
        lunar_voc: true,
        lunar_phases: true,
        retrograde_alerts: true,
        ingress_alerts: true,
        transit_aspects: true,
        // Other categories
        quests: true,
        evolution: true,
        intelligence: true,
        journal: true
    })

    // Expansion state for nested preferences
    const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({
        cosmic: false
    })

    useEffect(() => {
        // 1. Feature Detection
        if ('serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window) {
            setIsSupported(true)
            checkMasterSubscription()
        }

        // 2. Load User Preferences
        loadPreferences()
    }, [])

    const loadPreferences = async () => {
        try {
            const { data } = await api.get('/api/v1/profile/preferences')
            if (data && data.notifications) {
                // Merge with defaults to ensure all keys exist
                setPrefs(prev => ({ ...prev, ...data.notifications }))
            }
        } catch (e) {
            console.error("Failed to load prefs", e)
            // Silently fail to defaults
        }
    }

    const checkMasterSubscription = async () => {
        try {
            const registration = await navigator.serviceWorker.ready
            const subscription = await registration.pushManager.getSubscription()
            setIsMasterEnabled(!!subscription)
        } catch (e) {
            console.error('Failed to check subscription', e)
        }
    }

    const toggleMasterSwitch = async () => {
        if (!isSupported) return
        setLoading(true)

        try {
            if (isMasterEnabled) {
                // DISCONNECT
                const registration = await navigator.serviceWorker.ready
                const subscription = await registration.pushManager.getSubscription()
                if (subscription) {
                    // Backend removal
                    await api.delete('/api/v1/push/subscribe', {
                        data: {
                            endpoint: subscription.endpoint,
                            keys: subscription.toJSON().keys
                        }
                    })
                    // Browser removal
                    await subscription.unsubscribe()
                    setIsMasterEnabled(false)
                    toast({ title: "Disconnected", description: "Cosmic connection severed." })
                }
            } else {
                // CONNECT (Re-Sync Logic included by getting fresh key)
                const perm = await Notification.requestPermission()
                if (perm !== 'granted') throw new Error('Permission denied')

                // 1. Get Fresh Key
                const keyResp = await api.get('/api/v1/push/public-key')
                const publicKey = keyResp.data.publicKey

                // 2. Subscribe (Browser)
                const registration = await navigator.serviceWorker.ready
                const subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(publicKey)
                })

                // 3. Subscribe (Backend)
                await api.post('/api/v1/push/subscribe', {
                    endpoint: subscription.endpoint,
                    keys: subscription.toJSON().keys
                })

                setIsMasterEnabled(true)
                toast({ title: "Connected", description: "Cosmic nervous system linked." })
            }
        } catch (error) {
            console.error(error)
            toast({
                title: "Connection Failed",
                description: "Could not link to cosmic stream. Check permissions.",
                variant: "destructive"
            })
        } finally {
            setLoading(false)
        }
    }

    const updatePreference = async (key: string, value: boolean) => {
        // UI Optimistic Update
        const newPrefs = { ...prefs, [key]: value }
        setPrefs(newPrefs)

        try {
            await api.patch('/api/v1/profile/preferences', {
                notifications: { [key]: value }
            })
        } catch (error) {
            console.error("Failed to save preference", error)
            toast({ title: "Sync Error", description: "Failed to save preference.", variant: "destructive" })
            // Revert
            setPrefs({ ...prefs, [key]: !value })
        }
    }

    const sendTestSignal = async () => {
        setTestLoading(true)
        try {
            await api.post('/api/v1/push/test')
            toast({ title: "Signal Sent", description: "Check your device for the cosmic ping." })
        } catch (error) {
            toast({ title: "Signal Failed", description: "The void did not answer.", variant: "destructive" })
        } finally {
            setTestLoading(false)
        }
    }

    const categories = [
        {
            id: 'cosmic',
            label: 'Cosmic & Tracking',
            icon: Sun,
            desc: 'Solar, lunar, and planetary alerts',
            color: 'text-amber-500',
            bg: 'bg-amber-500/10',
            expandable: true,
            subcategories: [
                { id: 'solar_alerts', label: 'Solar Alerts', icon: Zap, desc: 'Geomagnetic storms & Kp spikes', color: 'text-orange-400' },
                { id: 'lunar_voc', label: 'Void of Course', icon: Moon, desc: 'Moon VoC start/end periods', color: 'text-slate-400' },
                { id: 'lunar_phases', label: 'Lunar Phases', icon: Moon, desc: 'New & Full Moon alerts', color: 'text-slate-300' },
                { id: 'retrograde_alerts', label: 'Retrogrades', icon: RotateCcw, desc: 'Retrograde stations & direction changes', color: 'text-indigo-400' },
                { id: 'ingress_alerts', label: 'Ingresses', icon: Sun, desc: 'Planetary sign changes', color: 'text-amber-400' },
                { id: 'transit_aspects', label: 'Natal Transits', icon: Target, desc: 'Exact aspects to your natal chart', color: 'text-purple-400' },
            ]
        },
        { id: 'quests', label: 'Mission Control', icon: Target, desc: 'New directives and rewards', color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
        { id: 'evolution', label: 'Evolution', icon: Award, desc: 'Level ups and Rank changes', color: 'text-violet-500', bg: 'bg-violet-500/10' },
        { id: 'intelligence', label: 'System Intelligence', icon: Activity, desc: 'Hypothesis updates and Synthesis', color: 'text-blue-500', bg: 'bg-blue-500/10' },
        { id: 'journal', label: 'Journal Archive', icon: Sparkles, desc: 'Entry confirmations and prompts', color: 'text-pink-500', bg: 'bg-pink-500/10' },
    ]

    const toggleExpanded = (categoryId: string) => {
        setExpandedCategories(prev => ({
            ...prev,
            [categoryId]: !prev[categoryId]
        }))
    }

    return (
        <div className="h-full flex flex-col bg-background">
            {/* Header */}
            <div className="p-6 border-b border-border/40 backdrop-blur-md bg-background/50 sticky top-0 z-10 flex items-center gap-4">
                <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="rounded-xl hover:bg-muted/50">
                    <ArrowLeft className="w-5 h-5 text-muted-foreground" />
                </Button>
                <div>
                    <h1 className="text-xl font-bold tracking-tight">Nervous System</h1>
                    <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Configuration & Sensitivity</p>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 pb-safe min-h-0">
                <div className="max-w-2xl mx-auto space-y-8 pb-12">

                    {/* Master Switch Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`p-6 rounded-3xl border ${isMasterEnabled ? 'border-primary/20 bg-primary/5' : 'border-border bg-card'} transition-all duration-500`}
                    >
                        <div className="flex items-start justify-between mb-6">
                            <div className="flex items-center gap-4">
                                <div className={`p-3 rounded-2xl ${isMasterEnabled ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20' : 'bg-muted text-muted-foreground'} transition-all duration-300`}>
                                    <Activity className={`w-6 h-6 ${isMasterEnabled ? 'animate-pulse' : ''}`} />
                                </div>
                                <div>
                                    <h2 className="text-lg font-bold text-foreground">Cosmic Link</h2>
                                    <p className="text-sm text-muted-foreground leading-snug">
                                        {isMasterEnabled
                                            ? "Connected to the universal stream."
                                            : "Disconnected from the void."}
                                    </p>
                                </div>
                            </div>
                            <Switch
                                checked={isMasterEnabled}
                                onCheckedChange={toggleMasterSwitch}
                                disabled={loading || !isSupported}
                                className="data-[state=checked]:bg-primary scale-125"
                            />
                        </div>

                        {/* Connection Status / Visualizer */}
                        <div className="h-2 bg-background/50 rounded-full overflow-hidden mb-4 border border-border/50">
                            <motion.div
                                className={`h-full ${isMasterEnabled ? 'bg-primary' : 'bg-muted-foreground/20'}`}
                                animate={{ width: isMasterEnabled ? "100%" : "0%" }}
                                transition={{ duration: 1, ease: "easeInOut" }}
                            />
                        </div>

                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                                <Signal className="w-3 h-3" />
                                <div className="flex gap-2 items-center">
                                    {isMasterEnabled ? "Status: ONLINE" : "Status: OFFLINE"}
                                    {!isSupported && <span className="text-destructive">(Not Supported)</span>}
                                </div>
                            </div>

                            {isMasterEnabled && (
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={sendTestSignal}
                                    disabled={testLoading}
                                    className="h-8 text-xs rounded-lg border-primary/20 hover:bg-primary/10 hover:text-primary"
                                >
                                    {testLoading ? (
                                        <Sparkles className="w-3 h-3 mr-2 animate-spin" />
                                    ) : (
                                        <Bell className="w-3 h-3 mr-2" />
                                    )}
                                    Test Signal
                                </Button>
                            )}
                        </div>
                    </motion.div>

                    {/* Granular Controls */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest px-2">Sensory Filters</h3>

                        <div className={`grid gap-3 ${!isMasterEnabled ? 'opacity-50 pointer-events-none grayscale-[0.5]' : ''} transition-all duration-500`}>
                            {categories.map((cat, idx) => {
                                const Icon = cat.icon
                                const isExpanded = expandedCategories[cat.id]
                                const hasSubcategories = 'subcategories' in cat && cat.subcategories

                                return (
                                    <motion.div
                                        key={cat.id}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: idx * 0.1 }}
                                        className="rounded-2xl bg-card border border-border/50 hover:border-primary/20 transition-all overflow-hidden"
                                    >
                                        {/* Main Category Row */}
                                        <div className="flex items-center justify-between p-4 hover:bg-accent/50 transition-all">
                                            <div className="flex items-center gap-4 flex-1">
                                                {hasSubcategories && (
                                                    <button
                                                        onClick={() => toggleExpanded(cat.id)}
                                                        className="p-1 rounded hover:bg-muted/50 transition-colors"
                                                    >
                                                        {isExpanded ? (
                                                            <ChevronUp className="w-4 h-4 text-muted-foreground" />
                                                        ) : (
                                                            <ChevronDown className="w-4 h-4 text-muted-foreground" />
                                                        )}
                                                    </button>
                                                )}
                                                <div className={`p-2.5 rounded-xl ${cat.bg} ${cat.color}`}>
                                                    <Icon className="w-5 h-5" />
                                                </div>
                                                <div>
                                                    <div className="font-semibold text-sm">{cat.label}</div>
                                                    <div className="text-xs text-muted-foreground">{cat.desc}</div>
                                                </div>
                                            </div>
                                            <Switch
                                                checked={prefs[cat.id as keyof typeof prefs] ?? true}
                                                onCheckedChange={(val) => updatePreference(cat.id, val)}
                                            />
                                        </div>

                                        {/* Expanded Subcategories */}
                                        {hasSubcategories && isExpanded && (
                                            <motion.div
                                                initial={{ height: 0, opacity: 0 }}
                                                animate={{ height: 'auto', opacity: 1 }}
                                                exit={{ height: 0, opacity: 0 }}
                                                className="border-t border-border/30 bg-muted/20"
                                            >
                                                {cat.subcategories!.map((sub) => {
                                                    const SubIcon = sub.icon
                                                    return (
                                                        <div
                                                            key={sub.id}
                                                            className="flex items-center justify-between px-6 py-3 hover:bg-accent/30 transition-all"
                                                        >
                                                            <div className="flex items-center gap-3">
                                                                <SubIcon className={`w-4 h-4 ${sub.color}`} />
                                                                <div>
                                                                    <div className="font-medium text-xs">{sub.label}</div>
                                                                    <div className="text-xs text-muted-foreground">{sub.desc}</div>
                                                                </div>
                                                            </div>
                                                            <Switch
                                                                checked={prefs[sub.id as keyof typeof prefs] ?? true}
                                                                onCheckedChange={(val) => updatePreference(sub.id, val)}
                                                                disabled={!prefs[cat.id as keyof typeof prefs]}
                                                                className="scale-90"
                                                            />
                                                        </div>
                                                    )
                                                })}
                                            </motion.div>
                                        )}
                                    </motion.div>
                                )
                            })}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    )
}
