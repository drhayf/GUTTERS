
import { useState, useEffect } from 'react'
import { BellOff, Sparkles, AlertTriangle } from 'lucide-react'
import { Switch } from '@/components/ui/switch'
import { toast } from '@/hooks/use-toast'
import api from '@/lib/api'

// Utility to convert VAPID key
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

export default function NotificationManager() {
    const [isSupported, setIsSupported] = useState(false)
    const [isSubscribed, setIsSubscribed] = useState(false)
    const [loading, setLoading] = useState(false)
    const [isIOS, setIsIOS] = useState(false)

    useEffect(() => {
        // Feature detection
        if ('serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window) {
            setIsSupported(true)
            checkSubscription()
        }

        // iOS detection
        const userAgent = window.navigator.userAgent.toLowerCase()
        const isIosDevice = /iphone|ipad|ipod/.test(userAgent)
        setIsIOS(isIosDevice)
    }, [])

    const checkSubscription = async () => {
        try {
            const registration = await navigator.serviceWorker.ready
            const subscription = await registration.pushManager.getSubscription()
            setIsSubscribed(!!subscription)
        } catch (e) {
            console.error('Failed to check subscription', e)
        }
    }

    const toggleNotifications = async () => {
        if (!isSupported) return
        setLoading(true)

        try {
            if (isSubscribed) {
                // Call backend to remove subscription
                const registration = await navigator.serviceWorker.ready
                const subscription = await registration.pushManager.getSubscription()

                if (subscription) {
                    await api.delete('/api/v1/push/subscribe', {
                        data: {
                            endpoint: subscription.endpoint,
                            keys: subscription.toJSON().keys
                        }
                    })
                    // Unsubscribe in browser
                    await subscription.unsubscribe()
                    setIsSubscribed(false)
                    toast({ title: "Disconnected", description: "Cosmic alerts disabled." })
                }
            } else {
                // 1. Request Permission
                const perm = await Notification.requestPermission()

                if (perm !== 'granted') {
                    toast({ title: "Permission Denied", description: "Please enable notifications in your browser settings.", variant: "destructive" })
                    return
                }

                // 2. Readiness Check
                const registration = await navigator.serviceWorker.ready
                if (!registration.pushManager) {
                    throw new Error("Push Manager not available")
                }

                // 3. Fetch Public Key
                const keyResp = await api.get('/api/v1/push/public-key')
                const publicKey = keyResp.data.publicKey

                // 4. Subscribe via PushManager (Ghost Buster Protocol)

                // CRITICAL: Check for and remove any stale subscription (from old keys)
                const existingSub = await registration.pushManager.getSubscription()
                if (existingSub) {
                    console.log("Unsubscribing stale subscription...")
                    await existingSub.unsubscribe()
                }

                const subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(publicKey)
                })

                // 5. Send to Backend
                await api.post('/api/v1/push/subscribe', {
                    endpoint: subscription.endpoint,
                    keys: subscription.toJSON().keys
                })

                setIsSubscribed(true)
                toast({
                    title: "Cosmic Gateway Open",
                    description: "You will now receive intelligence alerts.",
                    variant: "default"
                })
            }
        } catch (error: any) {
            console.error(error)
            toast({
                title: "Evolution Failed",
                description: `Push Error: ${error.message || "Unknown error"}`,
                variant: "destructive"
            })
        } finally {
            setLoading(false)
        }
    }

    if (!isSupported) {
        if (isIOS) {
            return (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                        <span className="text-xs font-bold uppercase tracking-wider text-amber-500">iOS Restriction</span>
                    </div>
                    <p className="text-[11px] text-muted-foreground">
                        To enable cosmic alerts on iOS, you must first share this page and select
                        <span className="font-bold text-foreground mx-1">"Add to Home Screen"</span>.
                    </p>
                </div>
            )
        }
        return null // Hidden on completely unsupported browsers
    }

    return (
        <div className="p-6 rounded-[2rem] border border-border/50 bg-secondary/10 flex items-center justify-between">
            <div className="flex items-center gap-4">
                <div className={`p-3 rounded-2xl ${isSubscribed ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'}`}>
                    {isSubscribed ? <Sparkles className="w-5 h-5 animate-pulse" /> : <BellOff className="w-5 h-5" />}
                </div>
                <div>
                    <h4 className="text-sm font-bold tracking-tight">Cosmic Alerts</h4>
                    <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">
                        {isSubscribed ? 'Intelligence Stream Active' : 'Enable System Notifications'}
                    </p>
                </div>
            </div>

            <div className="flex items-center gap-2">
                <Switch
                    checked={isSubscribed}
                    onCheckedChange={toggleNotifications}
                    disabled={loading}
                    className="data-[state=checked]:bg-primary"
                />
            </div>
        </div>
    )
}
