import { useState, useEffect } from 'react'
import { Play, Square, RefreshCcw, Cpu, Clock, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import api from '@/lib/api'
import { toast } from '@/hooks/use-toast'

export default function WorkerControl() {
    const [status, setStatus] = useState<{ is_running: boolean, interval_seconds: number } | null>(null)
    const [isLoading, setIsLoading] = useState(true)

    const fetchStatus = async () => {
        try {
            const resp = await api.get('/api/v1/system/status')
            setStatus(resp.data.worker)
        } catch (err) {
            console.error('Failed to fetch worker status:', err)
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchStatus()
        const interval = setInterval(fetchStatus, 5000)
        return () => clearInterval(interval)
    }, [])

    const handleAction = async (action: 'start' | 'stop' | 'restart') => {
        try {
            const resp = await api.post(`/api/v1/system/worker/${action}`)
            toast({
                title: "Worker Command Issued",
                description: resp.data.message,
                variant: "default"
            })
            fetchStatus()
        } catch (err) {
            toast({
                title: "Command Failed",
                description: "Failed to issue command to background worker.",
                variant: "destructive"
            })
        }
    }

    if (isLoading) return <div className="h-[200px] flex items-center justify-center border border-border rounded-2xl animate-pulse bg-secondary/5">Connecting...</div>

    return (
        <div className="p-6 rounded-2xl border border-border bg-secondary/10 backdrop-blur supports-[backdrop-filter]:bg-secondary/5">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-primary" />
                    <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Background Worker</h3>
                </div>
                <Badge variant={status?.is_running ? "default" : "destructive"} className="text-[10px] font-bold px-2 py-0">
                    {status?.is_running ? "UP" : "DOWN"}
                </Badge>
            </div>

            <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-background/50 border border-border/40">
                        <div className="flex items-center gap-2 text-muted-foreground mb-1">
                            <Clock className="w-3 h-3" />
                            <span className="text-[10px] font-bold uppercase tracking-tight">Interval</span>
                        </div>
                        <p className="text-sm font-mono font-medium">{(status?.interval_seconds || 3600) / 3600}h</p>
                    </div>
                    <div className="p-3 rounded-lg bg-background/50 border border-border/40">
                        <div className="flex items-center gap-2 text-muted-foreground mb-1">
                            <AlertCircle className="w-3 h-3" />
                            <span className="text-[10px] font-bold uppercase tracking-tight">Scope</span>
                        </div>
                        <p className="text-sm font-mono font-medium">All Users</p>
                    </div>
                </div>

                <div className="flex gap-2">
                    {status?.is_running ? (
                        <Button
                            onClick={() => handleAction('stop')}
                            variant="destructive"
                            size="sm"
                            className="flex-1 gap-2 text-[11px] font-bold uppercase"
                        >
                            <Square className="w-3 h-3" /> Stop
                        </Button>
                    ) : (
                        <Button
                            onClick={() => handleAction('start')}
                            variant="default"
                            size="sm"
                            className="flex-1 gap-2 text-[11px] font-bold uppercase"
                        >
                            <Play className="w-3 h-3" /> Start
                        </Button>
                    )}
                    <Button
                        onClick={() => handleAction('restart')}
                        variant="secondary"
                        size="sm"
                        className="gap-2 text-[11px] font-bold uppercase"
                    >
                        <RefreshCcw className="w-3 h-3" />
                    </Button>
                </div>
            </div>

            <p className="mt-4 text-[10px] text-muted-foreground italic">
                {status?.is_running
                    ? "Currently performing active cosmic data ingestion and pattern detection cycles."
                    : "Intelligence processing is currently paused. Patterns will not be detected."}
            </p>
        </div>
    )
}
